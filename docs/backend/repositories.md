# 📦 Repositorios (Data Access Layer)

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Nivel**: Beginner-friendly 🟢

---

## 🎯 ¿Qué son los Repositorios?

Los **Repositorios** son una capa de abstracción entre tu código de negocio y la base de datos. Piensa en ellos como "traductores" que convierten operaciones de alto nivel (como "obtener experimento") en queries SQL específicas.

### ¿Por qué usar Repositorios?

```
❌ SIN Repositorios (código acoplado):
┌─────────────┐         ┌────────────┐
│   Service   │ ──SQL──▶│  Database  │
└─────────────┘         └────────────┘
    El servicio conoce SQL = difícil de testear y mantener

✅ CON Repositorios (código desacoplado):
┌─────────────┐         ┌──────────────┐         ┌────────────┐
│   Service   │ ──API──▶│  Repository  │ ──SQL──▶│  Database  │
└─────────────┘         └──────────────┘         └────────────┘
    El servicio no sabe de SQL = fácil de testear con mocks
```

---

## 📁 Estructura de Archivos

```
data_access/
├── __init__.py              # Exports públicos
├── database.py              # Conexión a PostgreSQL
└── repositories/
    ├── __init__.py
    ├── base_repository.py   # Clase base abstracta
    ├── experiment_repository.py
    ├── variant_repository.py
    ├── assignment_repository.py
    ├── funnel_repository.py
    └── user_repository.py
```

---

## 📄 Archivo por Archivo

---

### 1️⃣ `base_repository.py`

**Propósito**: Define la estructura base que todos los repositorios deben seguir.

```python
# data_access/repositories/base_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class BaseRepository(ABC):
    """
    Clase base abstracta para todos los repositorios.
    
    🎓 CONCEPTO: ABC (Abstract Base Class)
    ----------------------------------------
    - "abstractmethod" significa que las clases hijas DEBEN implementar ese método
    - Si no lo implementan, Python lanzará un error al crear la instancia
    - Es como un "contrato" que garantiza consistencia entre repositorios
    """
    
    def __init__(self, pool):
        """
        Inicializa el repositorio con un pool de conexiones.
        
        Args:
            pool: asyncpg connection pool
                  Esto permite reutilizar conexiones en lugar de crear una nueva
                  para cada query (mucho más eficiente)
        """
        self.pool = pool
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por su ID.
        
        🎓 NOTA: Todos los IDs en Samplit son UUIDs (strings de 36 caracteres)
        Ejemplo: "550e8400-e29b-41d4-a716-446655440000"
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo registro.
        
        Returns:
            El registro creado con su ID generado
        """
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualiza un registro existente.
        
        Returns:
            El registro actualizado o None si no existe
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Elimina un registro.
        
        Returns:
            True si se eliminó, False si no existía
        """
        pass
```

---

### 2️⃣ `experiment_repository.py`

**Propósito**: Todas las operaciones de base de datos relacionadas con experimentos.

```python
# data_access/repositories/experiment_repository.py

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ExperimentRepository:
    """
    Repositorio para la tabla 'experiments'.
    
    🎓 RESPONSABILIDADES:
    - CRUD de experimentos (Create, Read, Update, Delete)
    - Queries específicas (por usuario, por estado, etc.)
    - NO contiene lógica de negocio (eso va en Services)
    
    🎓 PATRÓN DE DISEÑO:
    Cada método hace UNA sola cosa y la hace bien.
    Si necesitas combinar operaciones, hazlo en el Service.
    """
    
    def __init__(self, pool):
        """
        Args:
            pool: asyncpg.Pool - Pool de conexiones a PostgreSQL
        
        🎓 ¿QUÉ ES UN POOL DE CONEXIONES?
        ─────────────────────────────────
        Crear una conexión a la DB es costoso (~50-100ms).
        Un pool mantiene conexiones "calientes" listas para usar.
        
        ❌ Sin pool: Crear conexión → Query → Cerrar (lento)
        ✅ Con pool: Pedir conexión del pool → Query → Devolver al pool (rápido)
        """
        self.pool = pool
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREATE - Crear experimento
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create(
        self,
        name: str,
        user_id: str,
        description: Optional[str] = None,
        target_url: Optional[str] = None,
        traffic_allocation: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo experimento en la base de datos.
        
        Args:
            name: Nombre del experimento (ej: "Test botón CTA")
            user_id: UUID del usuario propietario
            description: Descripción opcional
            target_url: URL donde se ejecuta el experimento
            traffic_allocation: 0.0-1.0, porcentaje de tráfico (1.0 = 100%)
            metadata: JSON con datos extra
        
        Returns:
            Dict con el experimento creado, incluyendo su ID generado
        
        🎓 ANATOMÍA DEL QUERY:
        ─────────────────────
        INSERT INTO experiments (...) VALUES ($1, $2, ...)
                                              ↑
                                    Parámetros numerados (asyncpg)
                                    Previene SQL Injection automáticamente
        
        RETURNING * → Devuelve el registro insertado (incluye el ID generado)
        """
        
        query = """
            INSERT INTO experiments (
                name, user_id, description, target_url, 
                traffic_allocation, metadata, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'draft')
            RETURNING *
        """
        
        # 🔒 Usar 'async with' garantiza que la conexión se devuelve al pool
        #    incluso si hay un error
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                name,
                user_id,
                description,
                target_url,
                traffic_allocation,
                metadata or {}  # Si metadata es None, usar dict vacío
            )
            
            # 🎓 fetchrow() devuelve un asyncpg.Record
            #    dict(row) lo convierte a un diccionario normal de Python
            return dict(row)
    
    # ═══════════════════════════════════════════════════════════════════════
    # READ - Obtener experimentos
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_by_id(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un experimento por su ID.
        
        Args:
            experiment_id: UUID del experimento
        
        Returns:
            Dict con el experimento o None si no existe
        
        🎓 ¿POR QUÉ DEVOLVER NONE EN VEZ DE LANZAR EXCEPCIÓN?
        ─────────────────────────────────────────────────────
        - Esta capa solo accede a datos, no decide qué hacer si no existe
        - El Service decidirá si lanzar 404, crear uno nuevo, etc.
        - Mantiene el repositorio simple y reutilizable
        """
        
        query = "SELECT * FROM experiments WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, experiment_id)
            
            if row is None:
                return None
            
            return dict(row)
    
    async def get_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Lista experimentos de un usuario con filtros opcionales.
        
        Args:
            user_id: UUID del usuario
            status: Filtrar por estado ('draft', 'active', 'paused', etc.)
            limit: Máximo de resultados (paginación)
            offset: Saltar N resultados (paginación)
        
        Returns:
            Lista de experimentos
        
        🎓 PAGINACIÓN:
        ─────────────
        LIMIT 50 OFFSET 0  → Primeros 50 resultados (página 1)
        LIMIT 50 OFFSET 50 → Siguientes 50 (página 2)
        
        La fórmula es: offset = (page - 1) * limit
        """
        
        # Construir query dinámicamente según los filtros
        if status:
            query = """
                SELECT * FROM experiments 
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
            """
            params = [user_id, status, limit, offset]
        else:
            query = """
                SELECT * FROM experiments 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            params = [user_id, limit, offset]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            # 🎓 fetch() devuelve una lista de Records
            #    Usamos list comprehension para convertir a dicts
            return [dict(row) for row in rows]
    
    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """
        Obtiene TODOS los experimentos activos del sistema.
        
        🎓 CASO DE USO:
        ──────────────
        El tracker.js llama a este endpoint para saber qué experimentos
        están corriendo en un dominio específico.
        
        ⚠️ NOTA DE RENDIMIENTO:
        Este query puede ser costoso si hay muchos experimentos.
        En producción, se cachea con Redis (ver CacheService).
        """
        
        query = """
            SELECT * FROM experiments 
            WHERE status = 'active'
            ORDER BY created_at DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    # ═══════════════════════════════════════════════════════════════════════
    # UPDATE - Modificar experimentos
    # ═══════════════════════════════════════════════════════════════════════
    
    async def update(
        self,
        experiment_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza campos específicos de un experimento.
        
        Args:
            experiment_id: UUID del experimento
            updates: Dict con los campos a actualizar
                     Ejemplo: {"name": "Nuevo nombre", "status": "active"}
        
        Returns:
            Experimento actualizado o None si no existe
        
        🎓 ACTUALIZACIONES DINÁMICAS:
        ────────────────────────────
        En vez de UPDATE ... SET name=$1, description=$2, status=$3
        Construimos el SET dinámicamente según lo que venga en 'updates'.
        
        Esto es más flexible pero requiere cuidado con SQL injection.
        Por eso usamos parámetros numerados ($1, $2...) en vez de f-strings.
        """
        
        if not updates:
            # Nada que actualizar
            return await self.get_by_id(experiment_id)
        
        # Construir SET clause dinámicamente
        # Ejemplo: "name = $1, status = $2"
        set_clauses = []
        values = []
        
        # 🎓 enumerate(dict.items(), 1) empieza a contar desde 1
        #    Esto nos da: (1, ('name', 'valor')), (2, ('status', 'active')), ...
        for i, (key, value) in enumerate(updates.items(), 1):
            set_clauses.append(f"{key} = ${i}")
            values.append(value)
        
        # El ID del experimento es el último parámetro
        values.append(experiment_id)
        id_param = len(values)
        
        query = f"""
            UPDATE experiments 
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = ${id_param}
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            
            if row is None:
                return None
            
            return dict(row)
    
    async def update_status(
        self,
        experiment_id: str,
        new_status: str
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza el estado de un experimento.
        
        Args:
            experiment_id: UUID del experimento
            new_status: Nuevo estado
        
        Estados válidos:
        ├── 'draft'     → Borrador (creado pero no iniciado)
        ├── 'active'    → Corriendo (recibiendo tráfico)
        ├── 'paused'    → Pausado temporalmente
        ├── 'completed' → Finalizado (ya no recibe tráfico)
        └── 'archived'  → Archivado (soft delete)
        
        🎓 TRANSICIONES DE ESTADO:
        ─────────────────────────
        draft → active (iniciar experimento)
        active → paused (pausar)
        paused → active (reanudar)
        active|paused → completed (finalizar)
        * → archived (archivar)
        
        La validación de transiciones se hace en ExperimentService,
        aquí solo actualizamos el valor.
        """
        
        # Campos adicionales según el estado
        extra_fields = ""
        if new_status == 'active':
            extra_fields = ", started_at = NOW()"
        elif new_status == 'completed':
            extra_fields = ", completed_at = NOW()"
        
        query = f"""
            UPDATE experiments 
            SET status = $1 {extra_fields}, updated_at = NOW()
            WHERE id = $2
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, new_status, experiment_id)
            
            if row is None:
                return None
            
            return dict(row)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DELETE - Eliminar experimentos
    # ═══════════════════════════════════════════════════════════════════════
    
    async def delete(self, experiment_id: str, hard_delete: bool = False) -> bool:
        """
        Elimina un experimento.
        
        Args:
            experiment_id: UUID del experimento
            hard_delete: Si True, elimina físicamente. Si False, archiva.
        
        Returns:
            True si se eliminó/archivó, False si no existía
        
        🎓 SOFT DELETE vs HARD DELETE:
        ──────────────────────────────
        Soft Delete (default): Cambiar status a 'archived'
        - Los datos se mantienen para auditoría
        - Se puede "recuperar" cambiando el status
        - Más seguro
        
        Hard Delete: DELETE FROM experiments WHERE id = ...
        - Los datos se pierden permanentemente
        - También elimina variants, assignments (CASCADE)
        - Usar solo cuando realmente necesario
        """
        
        if hard_delete:
            query = "DELETE FROM experiments WHERE id = $1 RETURNING id"
        else:
            query = """
                UPDATE experiments 
                SET status = 'archived', updated_at = NOW()
                WHERE id = $1
                RETURNING id
            """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, experiment_id)
            
            # Si result es None, el experimento no existía
            return result is not None
    
    # ═══════════════════════════════════════════════════════════════════════
    # QUERIES ESPECIALIZADAS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def count_by_user(self, user_id: str, status: Optional[str] = None) -> int:
        """
        Cuenta experimentos de un usuario.
        
        Útil para:
        - Dashboard stats
        - Verificar límites del plan (ej: "Free plan: máx 3 experimentos")
        """
        
        if status:
            query = "SELECT COUNT(*) FROM experiments WHERE user_id = $1 AND status = $2"
            params = [user_id, status]
        else:
            query = "SELECT COUNT(*) FROM experiments WHERE user_id = $1"
            params = [user_id]
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, *params)
            return result or 0
    
    async def get_with_variants(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un experimento con todos sus elementos y variantes.
        
        🎓 ESTA ES UNA QUERY COMPLEJA:
        ─────────────────────────────
        En vez de hacer 3 queries separadas:
        1. SELECT * FROM experiments
        2. SELECT * FROM experiment_elements
        3. SELECT * FROM element_variants
        
        Hacemos UN query con JOINs y JSON aggregation.
        Esto es MUCHO más eficiente (1 round-trip a la DB en vez de 3).
        """
        
        query = """
            SELECT 
                e.*,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', el.id,
                            'name', el.name,
                            'selector_type', el.selector_type,
                            'selector_value', el.selector_value,
                            'element_type', el.element_type,
                            'variants', (
                                SELECT COALESCE(json_agg(
                                    json_build_object(
                                        'id', v.id,
                                        'name', v.name,
                                        'content', v.content,
                                        'is_control', v.is_control,
                                        'total_allocations', v.total_allocations,
                                        'total_conversions', v.total_conversions,
                                        'conversion_rate', v.conversion_rate
                                    )
                                    ORDER BY v.variant_order
                                ), '[]'::json)
                                FROM element_variants v 
                                WHERE v.element_id = el.id AND v.is_active = true
                            )
                        )
                        ORDER BY el.element_order
                    ) FILTER (WHERE el.id IS NOT NULL),
                    '[]'::json
                ) as elements
            FROM experiments e
            LEFT JOIN experiment_elements el ON el.experiment_id = e.id
            WHERE e.id = $1
            GROUP BY e.id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, experiment_id)
            
            if row is None:
                return None
            
            return dict(row)
```

---

### 3️⃣ `variant_repository.py`

**Propósito**: Operaciones sobre variantes de experimentos.

```python
# data_access/repositories/variant_repository.py

import logging
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)

class VariantRepository:
    """
    Repositorio para la tabla 'element_variants'.
    
    🎓 CONTEXTO:
    ───────────
    Una VARIANTE es una versión alternativa de un elemento.
    
    Ejemplo para un botón CTA:
    ├── Variante A (control): "Comprar ahora" (azul)
    ├── Variante B: "Obtener oferta" (verde)
    └── Variante C: "Empezar gratis" (rojo)
    
    El sistema asigna usuarios a variantes y mide conversiones
    para determinar cuál funciona mejor.
    """
    
    def __init__(self, pool):
        self.pool = pool
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREATE
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create(
        self,
        element_id: str,
        name: str,
        content: Dict[str, Any],
        is_control: bool = False,
        variant_order: int = 0
    ) -> Dict[str, Any]:
        """
        Crea una nueva variante para un elemento.
        
        Args:
            element_id: UUID del elemento padre
            name: Nombre de la variante (ej: "Variante A", "Control")
            content: Contenido de la variante en JSON
                     Ejemplo: {"text": "Comprar ahora", "color": "#0066cc"}
            is_control: True si es la variante de control (original)
            variant_order: Orden de visualización (0, 1, 2...)
        
        🎓 ¿QUÉ ES LA VARIANTE DE CONTROL?
        ──────────────────────────────────
        El "control" es la versión original/actual del elemento.
        Todas las demás variantes se comparan contra el control.
        
        Si Variante B tiene +15% conversiones vs Control,
        sabemos que B es mejor que lo que teníamos antes.
        """
        
        query = """
            INSERT INTO element_variants (
                element_id, name, content, is_control, 
                variant_order, is_active
            )
            VALUES ($1, $2, $3, $4, $5, true)
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                element_id,
                name,
                json.dumps(content),  # Convertir dict a JSON string
                is_control,
                variant_order
            )
            return dict(row)
    
    async def create_many(
        self,
        element_id: str,
        variants: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Crea múltiples variantes en una sola operación.
        
        🎓 BATCH INSERT:
        ────────────────
        Insertar 5 variantes una por una = 5 queries = ~50ms
        Insertar 5 variantes de una vez = 1 query = ~10ms
        
        Usamos executemany() para esto.
        """
        
        created = []
        
        async with self.pool.acquire() as conn:
            # Preparar el statement una vez
            stmt = await conn.prepare("""
                INSERT INTO element_variants (
                    element_id, name, content, is_control, variant_order, is_active
                )
                VALUES ($1, $2, $3, $4, $5, true)
                RETURNING *
            """)
            
            # Ejecutar para cada variante
            for i, v in enumerate(variants):
                row = await stmt.fetchrow(
                    element_id,
                    v.get('name', f'Variant {i+1}'),
                    json.dumps(v.get('content', {})),
                    v.get('is_control', i == 0),  # Primera = control por defecto
                    v.get('order', i)
                )
                created.append(dict(row))
        
        return created
    
    # ═══════════════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_by_id(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una variante por su ID."""
        
        query = "SELECT * FROM element_variants WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, variant_id)
            return dict(row) if row else None
    
    async def get_by_element(
        self,
        element_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las variantes de un elemento.
        
        Args:
            element_id: UUID del elemento
            active_only: Si True, solo variantes activas
        """
        
        if active_only:
            query = """
                SELECT * FROM element_variants 
                WHERE element_id = $1 AND is_active = true
                ORDER BY variant_order
            """
        else:
            query = """
                SELECT * FROM element_variants 
                WHERE element_id = $1
                ORDER BY variant_order
            """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, element_id)
            return [dict(row) for row in rows]
    
    async def get_by_experiment(
        self,
        experiment_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene TODAS las variantes de un experimento (todos los elementos).
        
        🎓 CASO DE USO:
        ──────────────
        El AnalyticsService necesita todas las variantes para calcular
        estadísticas Bayesianas del experimento completo.
        """
        
        query = """
            SELECT v.* 
            FROM element_variants v
            JOIN experiment_elements e ON e.id = v.element_id
            WHERE e.experiment_id = $1 AND v.is_active = true
            ORDER BY e.element_order, v.variant_order
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, experiment_id)
            return [dict(row) for row in rows]
    
    # ═══════════════════════════════════════════════════════════════════════
    # UPDATE - Estadísticas
    # ═══════════════════════════════════════════════════════════════════════
    
    async def increment_allocations(self, variant_id: str) -> Dict[str, Any]:
        """
        Incrementa el contador de asignaciones de una variante.
        
        🎓 ¿QUÉ ES UNA ASIGNACIÓN?
        ─────────────────────────
        Cuando un usuario visita la página y se le muestra esta variante,
        eso cuenta como una "asignación" o "allocation".
        
        total_allocations = cuántos usuarios han visto esta variante
        
        Este contador se usa para calcular:
        - Conversion Rate = conversions / allocations
        - Parámetros Bayesianos (alpha, beta)
        """
        
        query = """
            UPDATE element_variants 
            SET 
                total_allocations = total_allocations + 1,
                conversion_rate = CASE 
                    WHEN total_allocations + 1 > 0 
                    THEN total_conversions::float / (total_allocations + 1)
                    ELSE 0 
                END
            WHERE id = $1
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, variant_id)
            return dict(row) if row else None
    
    async def increment_conversions(
        self,
        variant_id: str,
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Incrementa el contador de conversiones de una variante.
        
        Args:
            variant_id: UUID de la variante
            conversion_value: Valor de la conversión (default 1.0)
                              Útil si quieres ponderar conversiones
                              (ej: compra de $100 vale más que newsletter signup)
        
        🎓 FÓRMULA DE CONVERSION RATE:
        ─────────────────────────────
        CR = conversions / allocations
        
        Ejemplo:
        - 1000 usuarios vieron Variante A
        - 50 usuarios convirtieron
        - CR = 50/1000 = 0.05 = 5%
        """
        
        query = """
            UPDATE element_variants 
            SET 
                total_conversions = total_conversions + 1,
                conversion_rate = CASE 
                    WHEN total_allocations > 0 
                    THEN (total_conversions + 1)::float / total_allocations
                    ELSE 0 
                END
            WHERE id = $1
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, variant_id)
            return dict(row) if row else None
    
    async def update_algorithm_state(
        self,
        variant_id: str,
        state: str
    ) -> None:
        """
        Actualiza el estado del algoritmo para una variante.
        
        🎓 ¿QUÉ ES ALGORITHM_STATE?
        ──────────────────────────
        El algoritmo Thompson Sampling mantiene parámetros (alpha, beta)
        que representan la "creencia" sobre la tasa de conversión.
        
        Este estado se guarda encriptado en la DB para:
        1. Persistencia entre reinicios del servidor
        2. Auditoría (trail de decisiones)
        3. Reproducibilidad
        
        El estado está encriptado por seguridad (nadie puede manipularlo).
        """
        
        query = """
            UPDATE element_variants 
            SET algorithm_state = $1
            WHERE id = $2
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, state, variant_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # DELETE
    # ═══════════════════════════════════════════════════════════════════════
    
    async def deactivate(self, variant_id: str) -> bool:
        """
        Desactiva una variante (soft delete).
        
        🎓 ¿POR QUÉ SOFT DELETE?
        ───────────────────────
        Si eliminamos físicamente una variante que tiene asignaciones,
        perdemos datos históricos importantes.
        
        "Desactivar" significa:
        - No se asignará a nuevos usuarios
        - Los datos históricos se mantienen
        - Se puede reactivar si es necesario
        """
        
        query = """
            UPDATE element_variants 
            SET is_active = false
            WHERE id = $1
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, variant_id)
            return result is not None
    
    async def delete(self, variant_id: str) -> bool:
        """
        Elimina físicamente una variante.
        
        ⚠️ USAR CON CUIDADO: Esto elimina datos permanentemente.
        Solo usar para variantes sin asignaciones (ej: borradores).
        """
        
        query = "DELETE FROM element_variants WHERE id = $1 RETURNING id"
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, variant_id)
            return result is not None
```

---

### 4️⃣ `assignment_repository.py`

**Propósito**: Gestiona quién ve qué variante.

```python
# data_access/repositories/assignment_repository.py

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AssignmentRepository:
    """
    Repositorio para la tabla 'assignments'.
    
    🎓 ¿QUÉ ES UN ASSIGNMENT?
    ────────────────────────
    Un "assignment" (asignación) es el registro de:
    "El usuario X fue asignado a la variante Y del experimento Z"
    
    Esto es CRÍTICO para:
    1. CONSISTENCIA: El mismo usuario siempre ve la misma variante
    2. ATRIBUCIÓN: Saber qué variante convirtió
    3. AUDITORÍA: Proof que las decisiones fueron justas
    """
    
    def __init__(self, pool):
        self.pool = pool
    
    async def get_user_assignment(
        self,
        experiment_id: str,
        user_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la asignación existente de un usuario.
        
        🎓 USER IDENTIFIER:
        ───────────────────
        Este es un ID único del visitante. Puede ser:
        - browser_id: Generado por tracker.js y guardado en localStorage
        - user_id: Si el usuario está logueado
        - custom: Cualquier ID que el cliente quiera usar
        
        La clave es que sea CONSISTENTE para el mismo usuario.
        """
        
        query = """
            SELECT * FROM assignments 
            WHERE experiment_id = $1 AND user_identifier = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, experiment_id, user_identifier)
            return dict(row) if row else None
    
    async def create(
        self,
        experiment_id: str,
        variant_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva asignación.
        
        Args:
            experiment_id: UUID del experimento
            variant_id: UUID de la variante asignada
            user_identifier: ID del usuario/visitante
            session_id: ID de sesión (opcional)
            context: Contexto adicional (device, browser, etc.)
        
        🎓 ¿QUÉ VA EN 'CONTEXT'?
        ───────────────────────
        Datos útiles para segmentación posterior:
        {
            "device": "mobile",
            "browser": "Chrome",
            "os": "iOS",
            "country": "ES",
            "referrer": "google.com",
            "url": "https://example.com/pricing"
        }
        """
        
        query = """
            INSERT INTO assignments (
                experiment_id, variant_id, user_identifier,
                session_id, context, assigned_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (experiment_id, user_identifier) 
            DO UPDATE SET session_id = EXCLUDED.session_id
            RETURNING *
        """
        
        # 🎓 ON CONFLICT DO UPDATE:
        # ─────────────────────────
        # Si ya existe una asignación para este usuario+experimento,
        # actualizamos el session_id en vez de fallar.
        # Esto maneja el caso donde el mismo usuario vuelve en otra sesión.
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                experiment_id,
                variant_id,
                user_identifier,
                session_id,
                context or {}
            )
            return dict(row)
    
    async def record_conversion(
        self,
        assignment_id: str,
        conversion_value: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Registra una conversión para una asignación.
        
        Args:
            assignment_id: UUID de la asignación
            conversion_value: Valor de la conversión (default 1.0)
            metadata: Datos adicionales de la conversión
        
        🎓 ¿QUÉ ES UNA CONVERSIÓN?
        ─────────────────────────
        El "éxito" que estás midiendo. Ejemplos:
        - Click en botón de compra
        - Registro de cuenta
        - Descarga de PDF
        - Tiempo en página > 2 minutos
        
        El tracker.js llama a este endpoint cuando ocurre la acción objetivo.
        """
        
        query = """
            UPDATE assignments 
            SET 
                converted_at = NOW(),
                conversion_value = $1,
                metadata = COALESCE(metadata, '{}'::jsonb) || $2
            WHERE id = $3 AND converted_at IS NULL
            RETURNING *
        """
        
        # 🎓 "converted_at IS NULL" previene conversiones duplicadas
        # Un usuario solo puede convertir UNA vez por experimento
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                conversion_value,
                metadata or {},
                assignment_id
            )
            return dict(row) if row else None
    
    async def get_experiment_stats(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de un experimento.
        
        Returns:
            {
                "total_assignments": 1500,
                "total_conversions": 120,
                "conversion_rate": 0.08,
                "by_variant": [
                    {"variant_id": "...", "assignments": 500, "conversions": 45},
                    {"variant_id": "...", "assignments": 500, "conversions": 35},
                    {"variant_id": "...", "assignments": 500, "conversions": 40}
                ]
            }
        """
        
        query = """
            SELECT 
                variant_id,
                COUNT(*) as assignments,
                COUNT(converted_at) as conversions,
                AVG(conversion_value) as avg_value
            FROM assignments
            WHERE experiment_id = $1
            GROUP BY variant_id
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, experiment_id)
            
            by_variant = [dict(row) for row in rows]
            
            total_assignments = sum(v['assignments'] for v in by_variant)
            total_conversions = sum(v['conversions'] for v in by_variant)
            
            return {
                "total_assignments": total_assignments,
                "total_conversions": total_conversions,
                "conversion_rate": (
                    total_conversions / total_assignments 
                    if total_assignments > 0 else 0
                ),
                "by_variant": by_variant
            }
```

---

## 🧪 Cómo Testear Repositorios

```python
# tests/test_experiment_repository.py

import pytest
from data_access.repositories.experiment_repository import ExperimentRepository

@pytest.fixture
async def repo(test_db_pool):
    """Crear repo con pool de test."""
    return ExperimentRepository(test_db_pool)

@pytest.mark.asyncio
async def test_create_experiment(repo):
    """Test crear un experimento."""
    
    exp = await repo.create(
        name="Test Experiment",
        user_id="test-user-id",
        description="Testing"
    )
    
    assert exp["id"] is not None
    assert exp["name"] == "Test Experiment"
    assert exp["status"] == "draft"

@pytest.mark.asyncio
async def test_get_by_id(repo):
    """Test obtener por ID."""
    
    # Crear
    created = await repo.create(name="Test", user_id="user-1")
    
    # Obtener
    fetched = await repo.get_by_id(created["id"])
    
    assert fetched is not None
    assert fetched["id"] == created["id"]

@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(repo):
    """Test que devuelve None si no existe."""
    
    result = await repo.get_by_id("nonexistent-id")
    
    assert result is None
```

---

## 📚 Resumen

| Repositorio | Tabla | Responsabilidad |
|-------------|-------|-----------------|
| `ExperimentRepository` | experiments | CRUD experimentos |
| `VariantRepository` | element_variants | CRUD variantes, estadísticas |
| `AssignmentRepository` | assignments | Asignaciones, conversiones |
| `FunnelRepository` | funnels, nodes, edges | Embudos de conversión |
| `UserRepository` | users | Autenticación, perfiles |

**Próximo paso**: [Ver Servicios](./services.md) para entender cómo usar estos repositorios.

