# 🔧 Servicios (Business Logic Layer)

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Nivel**: Beginner-friendly 🟢

---

## 🎯 ¿Qué son los Servicios?

Los **Servicios** contienen la **lógica de negocio** de la aplicación. Son el "cerebro" que coordina operaciones entre múltiples repositorios y aplica reglas de negocio.

```
          ┌─────────────────┐
          │     Router      │  ← Recibe HTTP request
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │    SERVICE      │  ← Lógica de negocio
          │  (Este archivo) │
          └────────┬────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
     ┌────────┐ ┌────────┐ ┌────────┐
     │ Repo A │ │ Repo B │ │ Repo C │  ← Acceso a datos
     └────────┘ └────────┘ └────────┘
```

**Regla de oro**: Los Servicios NUNCA acceden directamente a la base de datos. Siempre usan Repositorios.

---

## 📁 Estructura de Archivos

```
orchestration/
├── __init__.py
├── factories/
│   └── service_factory.py      # Crea servicios con dependencias
├── interfaces/
│   └── experiment_interface.py # Interfaces abstractas
└── services/
    ├── __init__.py
    ├── analytics_service.py    # Análisis Bayesiano
    ├── audit_service.py        # Trail de auditoría
    ├── cache_service.py        # Cache en memoria/Redis
    ├── experiment_service.py   # CRUD + asignación
    ├── funnel_service.py       # Embudos de conversión
    ├── metrics_service.py      # Métricas agregadas
    ├── multi_element_service.py # Experimentos multi-elemento
    ├── service_factory.py      # Factory para crear servicios
    └── traffic_filter_service.py # Filtrado de bots
```

---

## 📄 Archivo por Archivo

---

### 1️⃣ `experiment_service.py`

**Propósito**: Gestión completa de experimentos (CRUD + asignación de usuarios).

```python
# orchestration/services/experiment_service.py

"""
Experiment Service - El servicio más importante del sistema.

🎓 RESPONSABILIDADES:
─────────────────────
1. Crear experimentos con variantes (transacción atómica)
2. Gestionar ciclo de vida (draft → active → completed)
3. Asignar usuarios a variantes (Thompson Sampling)
4. Registrar conversiones
5. Coordinar con AuditService para trail de decisiones
"""

from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime

# Importamos repositorios (capa de datos)
from data_access.repositories.experiment_repository import ExperimentRepository
from data_access.repositories.variant_repository import VariantRepository
from data_access.repositories.assignment_repository import AssignmentRepository

# Importamos el motor de optimización
from engine.core.allocators.bayesian import BayesianAllocator

logger = logging.getLogger(__name__)


class ExperimentService:
    """
    🎓 PATRÓN: Service Layer
    ────────────────────────
    - Orquesta operaciones complejas
    - Aplica reglas de negocio
    - Maneja transacciones
    - Coordina múltiples repositorios
    """
    
    def __init__(
        self,
        db_pool,
        experiment_repo: ExperimentRepository,
        variant_repo: VariantRepository,
        assignment_repo: AssignmentRepository,
        audit_service: Optional['AuditService'] = None
    ):
        """
        Inicializa el servicio con todas sus dependencias.
        
        🎓 DEPENDENCY INJECTION:
        ───────────────────────
        En vez de crear los repositorios DENTRO del servicio:
        ❌ self.repo = ExperimentRepository()  # Difícil de testear
        
        Los recibimos como parámetros:
        ✅ self.repo = experiment_repo  # Fácil de mockear en tests
        
        Esto permite:
        - Tests unitarios con mocks
        - Diferentes implementaciones (prod vs test)
        - Configuración flexible
        """
        self.db_pool = db_pool
        self.experiment_repo = experiment_repo
        self.variant_repo = variant_repo
        self.assignment_repo = assignment_repo
        self.audit_service = audit_service
        
        # Inicializar allocator para Thompson Sampling
        self.allocator = BayesianAllocator()
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREATE EXPERIMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_experiment(
        self,
        name: str,
        description: Optional[str],
        variants_data: List[Dict[str, Any]],
        user_id: str,
        traffic_allocation: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea un experimento completo con sus variantes.
        
        🎓 TRANSACCIÓN ATÓMICA:
        ──────────────────────
        Todo se crea en UNA transacción. Si falla crear una variante,
        el experimento también se revierte. Esto garantiza consistencia.
        
        ❌ Sin transacción:
        1. Crear experimento ✅
        2. Crear variante A ✅
        3. Crear variante B ❌ (error)
        → Queda experimento huérfano sin variantes
        
        ✅ Con transacción:
        1. BEGIN TRANSACTION
        2. Crear experimento
        3. Crear variante A
        4. Crear variante B ❌ (error)
        5. ROLLBACK
        → Todo se revierte, DB queda limpia
        
        Args:
            name: Nombre del experimento
            description: Descripción opcional
            variants_data: Lista de variantes a crear
                [
                    {"name": "Control", "content": {...}, "is_control": true},
                    {"name": "Variante B", "content": {...}}
                ]
            user_id: UUID del usuario creador
            traffic_allocation: 0.0-1.0 (1.0 = 100% del tráfico)
            metadata: Datos adicionales
        
        Returns:
            Experimento creado con sus variantes
        
        Raises:
            ValueError: Si los datos son inválidos
            Exception: Si hay error de base de datos
        """
        
        # ═════════════════════════════════════════════════════════════════
        # PASO 1: VALIDACIONES
        # ═════════════════════════════════════════════════════════════════
        
        # 🎓 Validar ANTES de tocar la base de datos
        # Esto evita transacciones innecesarias
        
        if not name or not name.strip():
            raise ValueError("El nombre del experimento es requerido")
        
        if not variants_data or len(variants_data) < 2:
            raise ValueError(
                "Se requieren al menos 2 variantes. "
                "Un test A/B necesita mínimo: Control (A) y Variante (B)"
            )
        
        if traffic_allocation < 0 or traffic_allocation > 1:
            raise ValueError("traffic_allocation debe estar entre 0 y 1")
        
        # Validar que hay exactamente 1 control
        controls = [v for v in variants_data if v.get('is_control', False)]
        if len(controls) == 0:
            # Si no se especificó control, la primera variante es control
            variants_data[0]['is_control'] = True
        elif len(controls) > 1:
            raise ValueError("Solo puede haber una variante de control")
        
        # ═════════════════════════════════════════════════════════════════
        # PASO 2: TRANSACCIÓN
        # ═════════════════════════════════════════════════════════════════
        
        async with self.db_pool.acquire() as conn:
            # 🎓 async with conn.transaction():
            # Esto crea una transacción que:
            # - Se hace COMMIT automático si todo sale bien
            # - Se hace ROLLBACK automático si hay excepción
            
            async with conn.transaction():
                # 2.1 Crear el experimento
                experiment = await self.experiment_repo.create(
                    name=name.strip(),
                    user_id=user_id,
                    description=description,
                    traffic_allocation=traffic_allocation,
                    metadata=metadata
                )
                
                experiment_id = experiment['id']
                logger.info(f"Experimento creado: {experiment_id}")
                
                # 2.2 Crear un elemento por defecto
                # (Para experimentos simples A/B)
                element = await self._create_default_element(
                    conn, 
                    experiment_id, 
                    name
                )
                element_id = element['id']
                
                # 2.3 Crear las variantes
                created_variants = []
                for i, variant_data in enumerate(variants_data):
                    variant = await self.variant_repo.create(
                        element_id=element_id,
                        name=variant_data.get('name', f'Variante {i+1}'),
                        content=variant_data.get('content', {}),
                        is_control=variant_data.get('is_control', False),
                        variant_order=i
                    )
                    created_variants.append(variant)
                    logger.info(f"Variante creada: {variant['id']}")
                
                # 2.4 Registrar en audit trail (si está configurado)
                if self.audit_service:
                    await self.audit_service.log_decision(
                        experiment_id=experiment_id,
                        decision_type='experiment_created',
                        decision_data={
                            'name': name,
                            'variant_count': len(created_variants),
                            'user_id': user_id,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
        
        # ═════════════════════════════════════════════════════════════════
        # PASO 3: RETORNAR RESULTADO
        # ═════════════════════════════════════════════════════════════════
        
        # Obtener experimento completo con variantes
        return await self.experiment_repo.get_with_variants(experiment_id)
    
    async def _create_default_element(
        self, 
        conn, 
        experiment_id: str, 
        experiment_name: str
    ) -> Dict[str, Any]:
        """
        Crea un elemento por defecto para experimentos simples.
        
        🎓 ¿POR QUÉ UN ELEMENTO?
        ───────────────────────
        La estructura de Samplit soporta Multi-Element Experiments:
        - Experimento
          ├── Elemento 1 (ej: Botón CTA)
          │   ├── Variante A
          │   └── Variante B
          └── Elemento 2 (ej: Headline)
              ├── Variante A
              └── Variante B
        
        Para experimentos simples (A/B de una sola cosa),
        creamos un elemento "default" automáticamente.
        """
        
        query = """
            INSERT INTO experiment_elements (
                experiment_id, name, element_type, element_order
            )
            VALUES ($1, $2, 'default', 0)
            RETURNING *
        """
        
        row = await conn.fetchrow(
            query, 
            experiment_id, 
            f"Element: {experiment_name}"
        )
        return dict(row)
    
    # ═══════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un experimento por ID con todos sus datos.
        
        🎓 ENRIQUECIMIENTO:
        ──────────────────
        El repositorio solo devuelve datos crudos.
        El servicio puede "enriquecer" con datos calculados.
        """
        
        experiment = await self.experiment_repo.get_with_variants(experiment_id)
        
        if not experiment:
            return None
        
        # Enriquecer con estadísticas calculadas
        stats = await self.assignment_repo.get_experiment_stats(experiment_id)
        experiment['stats'] = stats
        
        return experiment
    
    async def list_experiments(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista experimentos de un usuario.
        
        🎓 PAGINACIÓN:
        ─────────────
        limit=50, offset=0  → Página 1 (items 1-50)
        limit=50, offset=50 → Página 2 (items 51-100)
        
        Formula: offset = (page - 1) * limit
        """
        
        return await self.experiment_repo.get_by_user(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    
    async def start_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Inicia un experimento (draft → active).
        
        🎓 VALIDACIONES DE NEGOCIO:
        ──────────────────────────
        No se puede iniciar un experimento si:
        1. Ya está activo
        2. No tiene suficientes variantes
        3. No tiene URL configurada (para web experiments)
        """
        
        experiment = await self.experiment_repo.get_by_id(experiment_id)
        
        if not experiment:
            raise ValueError(f"Experimento {experiment_id} no encontrado")
        
        if experiment['status'] == 'active':
            raise ValueError("El experimento ya está activo")
        
        if experiment['status'] not in ['draft', 'paused']:
            raise ValueError(
                f"No se puede iniciar un experimento con status '{experiment['status']}'. "
                "Solo experimentos en 'draft' o 'paused' pueden iniciarse."
            )
        
        # Verificar que tiene variantes
        variants = await self.variant_repo.get_by_experiment(experiment_id)
        if len(variants) < 2:
            raise ValueError(
                "El experimento necesita al menos 2 variantes para iniciarse"
            )
        
        # Actualizar status
        updated = await self.experiment_repo.update_status(experiment_id, 'active')
        
        # Log audit
        if self.audit_service:
            await self.audit_service.log_decision(
                experiment_id=experiment_id,
                decision_type='experiment_started',
                decision_data={
                    'timestamp': datetime.utcnow().isoformat(),
                    'variant_count': len(variants)
                }
            )
        
        logger.info(f"Experimento {experiment_id} iniciado")
        return updated
    
    async def pause_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Pausa un experimento activo.
        
        🎓 ¿CUÁNDO PAUSAR?
        ─────────────────
        - Bug detectado en una variante
        - Evento externo que afecta métricas (ej: Black Friday)
        - Revisión manual necesaria
        
        Al pausar:
        - No se asignan nuevos usuarios
        - Los usuarios ya asignados mantienen su variante
        - Las conversiones se siguen registrando
        """
        
        experiment = await self.experiment_repo.get_by_id(experiment_id)
        
        if not experiment:
            raise ValueError(f"Experimento {experiment_id} no encontrado")
        
        if experiment['status'] != 'active':
            raise ValueError("Solo se pueden pausar experimentos activos")
        
        return await self.experiment_repo.update_status(experiment_id, 'paused')
    
    async def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Finaliza un experimento (active/paused → completed).
        
        🎓 ¿CUÁNDO PARAR?
        ────────────────
        - Significancia estadística alcanzada
        - Tiempo máximo del test alcanzado
        - Ganador claro identificado
        - Decisión de negocio
        """
        
        experiment = await self.experiment_repo.get_by_id(experiment_id)
        
        if not experiment:
            raise ValueError(f"Experimento {experiment_id} no encontrado")
        
        if experiment['status'] not in ['active', 'paused']:
            raise ValueError(
                "Solo se pueden completar experimentos activos o pausados"
            )
        
        return await self.experiment_repo.update_status(experiment_id, 'completed')
    
    # ═══════════════════════════════════════════════════════════════════════
    # ALLOCATION (El corazón del A/B testing)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Asigna un usuario a una variante del experimento.
        
        🎓 FLUJO DE ASIGNACIÓN:
        ─────────────────────
        
        Usuario llega → ¿Ya tiene asignación?
                              │
                    ┌─────────┴─────────┐
                    │ SÍ                │ NO
                    ▼                   ▼
            Retornar la misma     ¿Experimento activo?
            variante (sticky)           │
                              ┌─────────┴─────────┐
                              │ SÍ                │ NO
                              ▼                   ▼
                    Seleccionar variante    Retornar None
                    (Thompson Sampling)
                              │
                              ▼
                    Guardar asignación
                              │
                              ▼
                    Retornar variante
        
        Args:
            experiment_id: UUID del experimento
            user_identifier: ID único del usuario (browser_id, user_id, etc.)
            session_id: ID de sesión actual (opcional)
            context: Contexto adicional {device, browser, country, ...}
        
        Returns:
            Dict con la variante asignada y datos adicionales, o None
        """
        
        # ════════════════════════════════════════════════════════════════
        # PASO 1: Verificar experimento
        # ════════════════════════════════════════════════════════════════
        
        experiment = await self.experiment_repo.get_by_id(experiment_id)
        
        if not experiment:
            logger.warning(f"Experimento {experiment_id} no encontrado")
            return None
        
        if experiment['status'] != 'active':
            logger.debug(f"Experimento {experiment_id} no está activo")
            return None
        
        # ════════════════════════════════════════════════════════════════
        # PASO 2: Verificar asignación existente (STICKY BUCKETING)
        # ════════════════════════════════════════════════════════════════
        
        # 🎓 STICKY BUCKETING:
        # Una vez que un usuario es asignado a una variante,
        # SIEMPRE ve esa misma variante. Esto es crítico para:
        # 1. Consistencia de experiencia de usuario
        # 2. Validez estadística (no contaminar datos)
        # 3. Atribución correcta de conversiones
        
        existing = await self.assignment_repo.get_user_assignment(
            experiment_id,
            user_identifier
        )
        
        if existing:
            logger.debug(
                f"Usuario {user_identifier} ya asignado a variante {existing['variant_id']}"
            )
            
            # Obtener datos de la variante
            variant = await self.variant_repo.get_by_id(existing['variant_id'])
            
            return {
                'experiment_id': experiment_id,
                'variant_id': variant['id'],
                'variant_name': variant['name'],
                'content': variant['content'],
                'is_new_assignment': False,  # Usuario ya tenía asignación
                'assignment_id': existing['id']
            }
        
        # ════════════════════════════════════════════════════════════════
        # PASO 3: Obtener variantes disponibles
        # ════════════════════════════════════════════════════════════════
        
        variants = await self.variant_repo.get_by_experiment(experiment_id)
        
        if not variants:
            logger.error(f"Experimento {experiment_id} no tiene variantes activas")
            return None
        
        # ════════════════════════════════════════════════════════════════
        # PASO 4: Seleccionar variante (Thompson Sampling)
        # ════════════════════════════════════════════════════════════════
        
        # 🎓 THOMPSON SAMPLING:
        # Es un algoritmo de "Multi-Armed Bandit" que balancea:
        # - EXPLORACIÓN: Probar variantes menos vistas
        # - EXPLOTACIÓN: Favorecer variantes que funcionan mejor
        #
        # Cómo funciona:
        # 1. Cada variante tiene una distribución Beta(α, β)
        # 2. α = conversiones + 1, β = no-conversiones + 1
        # 3. Muestreamos un valor de cada distribución
        # 4. Elegimos la variante con mayor muestra
        #
        # Esto hace que:
        # - Al inicio: Distribución uniforme (exploración)
        # - Con datos: Favorece ganadoras (explotación)
        
        selected_variant = await self._adaptive_selection(variants)
        
        # ════════════════════════════════════════════════════════════════
        # PASO 5: Crear asignación
        # ════════════════════════════════════════════════════════════════
        
        assignment = await self.assignment_repo.create(
            experiment_id=experiment_id,
            variant_id=selected_variant['id'],
            user_identifier=user_identifier,
            session_id=session_id,
            context=context or {}
        )
        
        # ════════════════════════════════════════════════════════════════
        # PASO 6: Actualizar contadores
        # ════════════════════════════════════════════════════════════════
        
        await self.variant_repo.increment_allocations(selected_variant['id'])
        
        # ════════════════════════════════════════════════════════════════
        # PASO 7: Log audit (si configurado)
        # ════════════════════════════════════════════════════════════════
        
        if self.audit_service:
            await self.audit_service.log_decision(
                experiment_id=experiment_id,
                decision_type='assignment',
                decision_data={
                    'user_identifier': user_identifier,
                    'variant_id': selected_variant['id'],
                    'variant_name': selected_variant['name'],
                    'algorithm': 'thompson_sampling',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        logger.info(
            f"Usuario {user_identifier} asignado a variante "
            f"{selected_variant['name']} ({selected_variant['id']})"
        )
        
        return {
            'experiment_id': experiment_id,
            'variant_id': selected_variant['id'],
            'variant_name': selected_variant['name'],
            'content': selected_variant['content'],
            'is_new_assignment': True,
            'assignment_id': assignment['id']
        }
    
    async def _adaptive_selection(
        self,
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Selecciona una variante usando Thompson Sampling.
        
        🎓 MATEMÁTICAS SIMPLIFICADAS:
        ────────────────────────────
        
        Distribución Beta:
        - Describe "probabilidad de éxito" con incertidumbre
        - α (alpha) = éxitos + 1
        - β (beta) = fracasos + 1
        
        Ejemplo:
        Variante A: 10 conversiones de 100 visitas
        - α = 10 + 1 = 11
        - β = (100 - 10) + 1 = 91
        - Media = α / (α + β) = 11/102 ≈ 0.108 (10.8%)
        
        Thompson Sampling:
        1. Sacar un número random de Beta(11, 91) → ej: 0.12
        2. Hacer lo mismo para todas las variantes
        3. Elegir la que tenga el número más alto
        
        Esto balancea automáticamente explorar vs explotar.
        """
        
        import numpy as np
        
        samples = []
        
        for variant in variants:
            # Obtener estadísticas
            allocations = variant.get('total_allocations', 0)
            conversions = variant.get('total_conversions', 0)
            
            # Calcular parámetros Beta
            # +1 es el "prior" (creencia inicial)
            alpha = conversions + 1
            beta = (allocations - conversions) + 1
            
            # Muestrear de la distribución
            sample = np.random.beta(alpha, beta)
            
            samples.append({
                'variant': variant,
                'sample': sample,
                'alpha': alpha,
                'beta': beta
            })
            
            logger.debug(
                f"Variante {variant['name']}: "
                f"α={alpha}, β={beta}, sample={sample:.4f}"
            )
        
        # Seleccionar variante con mayor muestra
        winner = max(samples, key=lambda x: x['sample'])
        
        logger.debug(f"Variante seleccionada: {winner['variant']['name']}")
        
        return winner['variant']
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONVERSIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def record_conversion(
        self,
        experiment_id: str,
        user_identifier: str,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Registra una conversión para un usuario.
        
        🎓 QUÉ ES UNA CONVERSIÓN:
        ───────────────────────
        El "éxito" que estás midiendo. Puede ser:
        - Click en botón de compra
        - Formulario completado
        - Compra realizada
        - Tiempo en página > X segundos
        - Cualquier acción objetivo
        
        El tracker.js llama este endpoint cuando detecta la acción.
        
        Args:
            experiment_id: UUID del experimento
            user_identifier: ID del usuario (mismo que en assign)
            conversion_value: Valor opcional (para revenue tracking)
            metadata: Datos adicionales de la conversión
        
        Returns:
            ID de la conversión o None si no hay asignación
        """
        
        # Buscar asignación existente
        assignment = await self.assignment_repo.get_user_assignment(
            experiment_id,
            user_identifier
        )
        
        if not assignment:
            logger.warning(
                f"No hay asignación para usuario {user_identifier} "
                f"en experimento {experiment_id}"
            )
            return None
        
        if assignment.get('converted_at'):
            logger.debug(
                f"Usuario {user_identifier} ya convirtió anteriormente"
            )
            # Ya convirtió, no registrar duplicado
            return assignment['id']
        
        # Registrar conversión
        updated = await self.assignment_repo.record_conversion(
            assignment_id=assignment['id'],
            conversion_value=conversion_value or 1.0,
            metadata=metadata
        )
        
        if updated:
            # Actualizar contador de variante
            await self.variant_repo.increment_conversions(
                assignment['variant_id'],
                conversion_value or 1.0
            )
            
            # Log audit
            if self.audit_service:
                await self.audit_service.log_decision(
                    experiment_id=experiment_id,
                    decision_type='conversion',
                    decision_data={
                        'user_identifier': user_identifier,
                        'variant_id': assignment['variant_id'],
                        'conversion_value': conversion_value or 1.0,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            
            logger.info(
                f"Conversión registrada para {user_identifier} "
                f"en variante {assignment['variant_id']}"
            )
            
            return updated['id']
        
        return None
```

---

### 2️⃣ `analytics_service.py`

**Propósito**: Análisis estadístico Bayesiano de experimentos.

```python
# orchestration/services/analytics_service.py

"""
Analytics Service - El cerebro estadístico.

🎓 ESTE SERVICIO CALCULA:
────────────────────────
1. Tasas de conversión con intervalos de confianza
2. Probabilidad de que cada variante sea la mejor (Monte Carlo)
3. Significancia estadística
4. Recomendaciones automáticas
5. Pérdida esperada si eliges cada variante
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    🎓 ANÁLISIS BAYESIANO:
    ─────────────────────
    En vez de preguntarnos "¿Es B mejor que A?" (enfoque frecuentista),
    preguntamos "¿Cuál es la PROBABILIDAD de que B sea mejor que A?"
    
    Esto es más útil para decisiones de negocio:
    - "B tiene 95% de probabilidad de ser mejor" → ¡Implementar!
    - "B tiene 60% de probabilidad de ser mejor" → Necesitamos más datos
    """
    
    def __init__(self):
        # Configuración por defecto
        self.default_confidence = 0.95  # 95% confidence interval
        self.min_samples_for_significance = 100  # Mínimo para conclusiones
    
    async def analyze_experiment(
        self,
        experiment_id: str,
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Análisis completo de un experimento.
        
        Args:
            experiment_id: UUID del experimento
            variants: Lista de variantes con sus stats:
                [
                    {
                        "id": "...",
                        "name": "Control",
                        "total_allocations": 1000,
                        "total_conversions": 50
                    },
                    ...
                ]
        
        Returns:
            {
                "experiment_id": "...",
                "analyzed_at": "2024-12-27T10:00:00Z",
                "total_allocations": 3000,
                "total_conversions": 150,
                "overall_conversion_rate": 0.05,
                "variants": [...],  # Con análisis individual
                "bayesian_analysis": {...},  # Probabilidades
                "recommendations": {...},  # Qué hacer
                "has_sufficient_data": true
            }
        """
        
        # ════════════════════════════════════════════════════════════════
        # PASO 1: Calcular totales
        # ════════════════════════════════════════════════════════════════
        
        total_allocations = sum(v.get('total_allocations', 0) for v in variants)
        total_conversions = sum(v.get('total_conversions', 0) for v in variants)
        
        overall_cr = (
            total_conversions / total_allocations 
            if total_allocations > 0 else 0
        )
        
        # ════════════════════════════════════════════════════════════════
        # PASO 2: Analizar cada variante individualmente
        # ════════════════════════════════════════════════════════════════
        
        # Encontrar baseline (control)
        control = next(
            (v for v in variants if v.get('is_control', False)),
            variants[0]  # Si no hay control, usar la primera
        )
        baseline_cr = (
            control.get('total_conversions', 0) / 
            control.get('total_allocations', 1)
        )
        
        analyzed_variants = []
        for variant in variants:
            analysis = self._analyze_variant(variant, baseline_cr)
            analyzed_variants.append(analysis)
        
        # ════════════════════════════════════════════════════════════════
        # PASO 3: Análisis Bayesiano (Monte Carlo)
        # ════════════════════════════════════════════════════════════════
        
        bayesian = self._perform_bayesian_analysis(variants)
        
        # ════════════════════════════════════════════════════════════════
        # PASO 4: Generar recomendaciones
        # ════════════════════════════════════════════════════════════════
        
        recommendations = self._generate_recommendations(
            analyzed_variants, 
            bayesian
        )
        
        return {
            "experiment_id": experiment_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "total_allocations": total_allocations,
            "total_conversions": total_conversions,
            "overall_conversion_rate": round(overall_cr, 4),
            "variant_count": len(variants),
            "variants": analyzed_variants,
            "bayesian_analysis": bayesian,
            "recommendations": recommendations,
            "has_sufficient_data": total_allocations >= self.min_samples_for_significance
        }
    
    def _analyze_variant(
        self,
        variant: Dict[str, Any],
        baseline_cr: float
    ) -> Dict[str, Any]:
        """
        Analiza una variante individual.
        
        🎓 MÉTRICAS CALCULADAS:
        ──────────────────────
        1. Conversion Rate: conversions / allocations
        2. Confidence Interval: Rango donde está el CR real (95%)
        3. Uplift: Cuánto mejor/peor que el baseline
        4. Statistical Significance: ¿Es el uplift real o ruido?
        """
        
        allocations = variant.get('total_allocations', 0)
        conversions = variant.get('total_conversions', 0)
        
        # Conversion Rate
        cr = conversions / allocations if allocations > 0 else 0
        
        # Confidence Interval (Wilson Score)
        ci_lower, ci_upper = self._calculate_confidence_interval(
            conversions, allocations
        )
        
        # Uplift vs baseline
        if baseline_cr > 0:
            uplift = ((cr - baseline_cr) / baseline_cr) * 100  # Porcentaje
        else:
            uplift = 0
        
        # Statistical Significance
        p_value, is_significant = self._calculate_significance(
            conversions, allocations, baseline_cr
        )
        
        return {
            "id": variant.get('id'),
            "name": variant.get('name'),
            "is_control": variant.get('is_control', False),
            "allocations": allocations,
            "conversions": conversions,
            "conversion_rate": round(cr, 4),
            "conversion_rate_percent": f"{cr * 100:.2f}%",
            "confidence_interval": {
                "lower": round(ci_lower, 4),
                "upper": round(ci_upper, 4),
                "confidence_level": 0.95
            },
            "uplift_percent": round(uplift, 2),
            "p_value": round(p_value, 4),
            "is_statistically_significant": is_significant
        }
    
    def _calculate_confidence_interval(
        self,
        conversions: int,
        allocations: int,
        confidence: float = 0.95
    ) -> tuple:
        """
        Calcula intervalo de confianza usando Wilson Score.
        
        🎓 ¿POR QUÉ WILSON SCORE?
        ────────────────────────
        El intervalo normal (Wald) falla con:
        - Muestras pequeñas
        - Proporciones cercanas a 0% o 100%
        
        Wilson Score es más robusto y preciso.
        
        Ejemplo:
        - 10 conversiones de 100 visitas
        - CR = 10%
        - CI 95%: [5.5%, 17.4%]
        
        Interpretación: Estamos 95% seguros de que el CR real
        está entre 5.5% y 17.4%.
        """
        
        if allocations == 0:
            return 0, 0
        
        z = stats.norm.ppf((1 + confidence) / 2)  # 1.96 para 95%
        p = conversions / allocations
        n = allocations
        
        # Fórmula Wilson Score
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        spread = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
        
        lower = max(0, center - spread)
        upper = min(1, center + spread)
        
        return lower, upper
    
    def _calculate_significance(
        self,
        conversions: int,
        allocations: int,
        baseline_cr: float,
        alpha: float = 0.05
    ) -> tuple:
        """
        Calcula si la diferencia es estadísticamente significativa.
        
        🎓 P-VALUE EXPLICADO:
        ────────────────────
        "Si NO hubiera diferencia real entre variantes,
        ¿qué tan probable es ver esta diferencia por azar?"
        
        - p-value < 0.05: Muy improbable por azar → Diferencia real
        - p-value > 0.05: Podría ser azar → Necesita más datos
        
        ⚠️ IMPORTANTE: p-value NO dice "cuánto mejor" es una variante,
        solo si la diferencia es "real" o "ruido".
        """
        
        if allocations < 10 or baseline_cr == 0:
            return 1.0, False  # Datos insuficientes
        
        observed_cr = conversions / allocations
        
        # Z-test para proporciones
        pooled_se = np.sqrt(baseline_cr * (1 - baseline_cr) / allocations)
        
        if pooled_se == 0:
            return 1.0, False
        
        z_score = (observed_cr - baseline_cr) / pooled_se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # Two-tailed
        
        return p_value, p_value < alpha
    
    def _perform_bayesian_analysis(
        self,
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Análisis Bayesiano con Monte Carlo.
        
        🎓 MONTE CARLO SIMPLIFICADO:
        ───────────────────────────
        1. Para cada variante, tenemos una distribución Beta
        2. Simulamos 10,000 "mundos posibles"
        3. En cada mundo, muestreamos de cada distribución
        4. Contamos en cuántos mundos gana cada variante
        
        Si Variante B gana en 8,500 de 10,000 mundos → 85% prob de ser mejor
        """
        
        n_simulations = self._get_adaptive_sample_size(len(variants))
        
        # 🎓 ADAPTIVE SAMPLING:
        # Más variantes = menos muestras necesarias por variante
        # 2-5 variantes: 10,000 muestras (~100ms)
        # 6-10 variantes: 5,000 muestras (~75ms)
        # 11+ variantes: 3,000 muestras (~50ms)
        
        logger.debug(f"Monte Carlo con {n_simulations} simulaciones")
        
        # Preparar parámetros Beta para cada variante
        variant_params = []
        for v in variants:
            allocations = v.get('total_allocations', 0)
            conversions = v.get('total_conversions', 0)
            
            alpha = conversions + 1  # Éxitos + prior
            beta = (allocations - conversions) + 1  # Fracasos + prior
            
            variant_params.append({
                'id': v.get('id'),
                'name': v.get('name'),
                'alpha': alpha,
                'beta': beta
            })
        
        # Simular
        n_variants = len(variant_params)
        samples = np.zeros((n_simulations, n_variants))
        
        for i, vp in enumerate(variant_params):
            samples[:, i] = np.random.beta(vp['alpha'], vp['beta'], n_simulations)
        
        # ¿Quién gana en cada simulación?
        winners = np.argmax(samples, axis=1)
        
        # Contar victorias
        win_counts = np.bincount(winners, minlength=n_variants)
        win_probabilities = win_counts / n_simulations
        
        # Calcular pérdida esperada
        expected_losses = self._calculate_expected_loss(samples)
        
        # Armar resultado
        results = []
        for i, vp in enumerate(variant_params):
            results.append({
                'variant_id': vp['id'],
                'variant_name': vp['name'],
                'win_probability': round(float(win_probabilities[i]), 4),
                'win_probability_percent': f"{win_probabilities[i] * 100:.1f}%",
                'expected_loss': round(float(expected_losses[i]), 4)
            })
        
        # Ordenar por probabilidad de ganar
        results.sort(key=lambda x: x['win_probability'], reverse=True)
        
        # Identificar líder
        leader = results[0]
        confidence_in_leader = leader['win_probability']
        
        return {
            'method': 'bayesian_monte_carlo',
            'simulations': n_simulations,
            'variants': results,
            'leader': {
                'variant_id': leader['variant_id'],
                'variant_name': leader['variant_name'],
                'confidence': confidence_in_leader
            },
            'is_conclusive': confidence_in_leader >= 0.95
        }
    
    def _get_adaptive_sample_size(self, n_variants: int) -> int:
        """Ajusta muestras según número de variantes."""
        if n_variants <= 5:
            return 10000
        elif n_variants <= 10:
            return 5000
        else:
            return 3000
    
    def _calculate_expected_loss(self, samples: np.ndarray) -> np.ndarray:
        """
        Calcula la pérdida esperada de elegir cada variante.
        
        🎓 EXPECTED LOSS:
        ────────────────
        "Si elijo Variante A pero B era realmente mejor,
        ¿cuánto estoy perdiendo en promedio?"
        
        Es una métrica de RIESGO, no solo de probabilidad.
        
        Variante con menor expected loss = opción más segura.
        """
        n_simulations, n_variants = samples.shape
        losses = np.zeros(n_variants)
        
        for i in range(n_variants):
            # Para cada simulación, calcular cuánto "perdemos"
            # respecto al mejor
            max_values = np.max(samples, axis=1)
            losses[i] = np.mean(max_values - samples[:, i])
        
        return losses
    
    def _generate_recommendations(
        self,
        variants: List[Dict[str, Any]],
        bayesian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera recomendaciones accionables basadas en el análisis.
        
        🎓 DECISIONES AUTOMATIZADAS:
        ───────────────────────────
        El objetivo es dar una recomendación clara:
        - "Implementar Variante B" (alta confianza)
        - "Continuar el test" (datos insuficientes)
        - "Considerar parar" (sin diferencias claras)
        """
        
        leader = bayesian.get('leader', {})
        confidence = leader.get('confidence', 0)
        
        total_allocations = sum(v['allocations'] for v in variants)
        
        # Determinar acción recomendada
        if total_allocations < 100:
            action = "CONTINUAR_RECOLECTANDO_DATOS"
            reason = (
                "Datos insuficientes. Se necesitan al menos 100 "
                "visitantes por variante para conclusiones fiables."
            )
            urgency = "low"
            
        elif confidence >= 0.99:
            action = "IMPLEMENTAR_GANADOR"
            reason = (
                f"Variante '{leader.get('variant_name')}' tiene "
                f"{confidence * 100:.1f}% de probabilidad de ser la mejor. "
                "Confianza muy alta."
            )
            urgency = "high"
            
        elif confidence >= 0.95:
            action = "IMPLEMENTAR_GANADOR"
            reason = (
                f"Variante '{leader.get('variant_name')}' tiene "
                f"{confidence * 100:.1f}% de probabilidad de ser la mejor. "
                "Nivel de confianza estándar alcanzado (95%)."
            )
            urgency = "medium"
            
        elif confidence >= 0.80:
            action = "CONSIDERAR_IMPLEMENTAR"
            reason = (
                f"Variante '{leader.get('variant_name')}' lidera con "
                f"{confidence * 100:.1f}% de confianza. "
                "Recomendamos más datos para mayor certeza."
            )
            urgency = "low"
            
        else:
            action = "CONTINUAR_TEST"
            reason = (
                "No hay un ganador claro aún. "
                f"La variante líder solo tiene {confidence * 100:.1f}% de confianza."
            )
            urgency = "low"
        
        return {
            "action": action,
            "reason": reason,
            "urgency": urgency,
            "leader_variant": leader.get('variant_name'),
            "confidence_level": f"{confidence * 100:.1f}%",
            "min_confidence_for_decision": "95%",
            "samples_collected": total_allocations,
            "recommendation_generated_at": datetime.utcnow().isoformat()
        }
```

---

## 📚 Resumen de Servicios

| Servicio | Archivo | Responsabilidad |
|----------|---------|-----------------|
| `ExperimentService` | experiment_service.py | CRUD, asignación Thompson Sampling |
| `AnalyticsService` | analytics_service.py | Análisis Bayesiano, Monte Carlo |
| `AuditService` | audit_service.py | Hash chain, trail de decisiones |
| `CacheService` | cache_service.py | Cache Redis/memoria |
| `FunnelService` | funnel_service.py | Embudos multi-paso |
| `MetricsService` | metrics_service.py | Métricas agregadas dashboard |
| `MultiElementService` | multi_element_service.py | Experimentos multi-elemento |

**Próximo paso**: [Ver API Reference](./api_reference.md) para los endpoints HTTP.

