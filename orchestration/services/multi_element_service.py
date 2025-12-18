# orchestration/services/multi_element_service.py
"""
Multi-Element Experiment Service

Maneja experimentos con múltiples elementos y sus combinaciones.

Dos modos de operación:
1. INDEPENDENT: Cada elemento selecciona su mejor variante independientemente
2. FACTORIAL: Genera todas las combinaciones y las trata como variantes únicas

CONFIDENCIAL - Propiedad intelectual protegida
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from itertools import product
from datetime import datetime

logger = logging.getLogger(__name__)


class CombinationMode:
    """Modos de generación de combinaciones"""
    INDEPENDENT = "independent"  # Cada elemento independiente (default)
    FACTORIAL = "factorial"      # Todas las combinaciones posibles


class MultiElementService:
    """
    ✅ Servicio para experimentos multi-elemento
    
    Resuelve el problema de combinaciones de variantes
    """
    
    def __init__(self, db_pool, variant_repo, assignment_repo):
        self.db = db_pool
        self.variant_repo = variant_repo
        self.assignment_repo = assignment_repo
        self.logger = logging.getLogger(f"{__name__}.MultiElementService")
    
    # ========================================================================
    # CREACIÓN DE EXPERIMENTO MULTI-ELEMENTO
    # ========================================================================
    
    async def create_multi_element_experiment(
        self,
        experiment_id: str,
        elements_config: List[Dict[str, Any]],
        combination_mode: str = CombinationMode.INDEPENDENT
    ) -> Dict[str, Any]:
        """
        Crear experimento multi-elemento con combinaciones
        
        Args:
            experiment_id: ID del experimento
            elements_config: Lista de elementos con sus variantes
                [
                    {
                        'name': 'Hero Title',
                        'selector': {...},
                        'variants': [
                            {'text': 'Variant 1'},
                            {'text': 'Variant 2'},
                            {'text': 'Variant 3'}
                        ]
                    },
                    {
                        'name': 'CTA Text',
                        'selector': {...},
                        'variants': [...]
                    }
                ]
            combination_mode: 'independent' o 'factorial'
        
        Returns:
            {
                'mode': str,
                'elements': List[dict],
                'combinations': List[dict] (si factorial),
                'total_variants': int
            }
        """
        
        self.logger.info(
            f"Creating multi-element experiment {experiment_id} "
            f"with {len(elements_config)} elements in {combination_mode} mode"
        )
        
        # Validar modo
        if combination_mode not in [CombinationMode.INDEPENDENT, CombinationMode.FACTORIAL]:
            raise ValueError(f"Invalid combination_mode: {combination_mode}")
        
        elements_created = []
        
        async with self.db.acquire() as conn:
            async with conn.transaction():
                # Crear elementos y variantes
                for elem_idx, element_config in enumerate(elements_config):
                    element_id = await conn.fetchval(
                        """
                        INSERT INTO experiment_elements (
                            experiment_id, element_order, name,
                            selector_type, selector_value, element_type,
                            original_content
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                        """,
                        experiment_id,
                        elem_idx,
                        element_config['name'],
                        element_config['selector']['type'],
                        element_config['selector']['selector'],
                        element_config.get('element_type', 'generic'),
                        element_config.get('original_content', {})
                    )
                    
                    # Crear variantes para este elemento
                    variant_ids = []
                    for var_idx, variant_content in enumerate(element_config['variants']):
                        # Inicializar Thompson Sampling state
                        initial_state = {
                            'alpha': 1.0,
                            'beta': 1.0,
                            'samples': 0
                        }
                        
                        variant_id = await self.variant_repo.create_variant(
                            element_id=str(element_id),
                            name=f"Variant {var_idx + 1}",
                            content=variant_content,
                            initial_state=initial_state
                        )
                        variant_ids.append(variant_id)
                    
                    elements_created.append({
                        'element_id': str(element_id),
                        'name': element_config['name'],
                        'variant_ids': variant_ids,
                        'variant_count': len(variant_ids)
                    })
                
                # Si es FACTORIAL, generar tabla de combinaciones
                if combination_mode == CombinationMode.FACTORIAL:
                    combinations = await self._generate_combinations(
                        experiment_id,
                        elements_created,
                        conn
                    )
                    
                    return {
                        'mode': combination_mode,
                        'elements': elements_created,
                        'combinations': combinations,
                        'total_variants': len(combinations)
                    }
                
                else:
                    # INDEPENDENT: Total de variantes es la suma
                    total_variants = sum(e['variant_count'] for e in elements_created)
                    
                    return {
                        'mode': combination_mode,
                        'elements': elements_created,
                        'total_variants': total_variants
                    }
    
    async def _generate_combinations(
        self,
        experiment_id: str,
        elements: List[Dict],
        conn
    ) -> List[Dict]:
        """
        Generar todas las combinaciones posibles (producto cartesiano)
        
        Ejemplo:
        - Elemento A: [V1, V2, V3]
        - Elemento B: [V1, V2, V3]
        → 9 combinaciones
        """
        
        # Construir listas de variant_ids por elemento
        variant_lists = [
            element['variant_ids'] 
            for element in elements
        ]
        
        # Producto cartesiano
        all_combinations = list(product(*variant_lists))
        
        self.logger.info(
            f"Generated {len(all_combinations)} combinations for {len(elements)} elements"
        )
        
        # Guardar combinaciones en metadata de experimento
        combinations_metadata = []
        
        for combo_idx, combination in enumerate(all_combinations):
            combo_dict = {
                'combination_id': combo_idx,
                'variant_ids': list(combination),
                'label': f"Combination {combo_idx + 1}"
            }
            combinations_metadata.append(combo_dict)
        
        # Actualizar metadata del experimento
        await conn.execute(
            """
            UPDATE experiments
            SET config = config || $1::jsonb
            WHERE id = $2
            """,
            {
                'combinations': combinations_metadata,
                'combination_mode': 'factorial'
            },
            experiment_id
        )
        
        return combinations_metadata
    
    # ========================================================================
    # ASIGNACIÓN MULTI-ELEMENTO
    # ========================================================================
    
    async def allocate_user_multi_element(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Asignar usuario a combinación de variantes
        
        Detecta automáticamente el modo (independent vs factorial)
        
        Returns:
            {
                'experiment_id': str,
                'mode': str,
                'assignments': [
                    {
                        'element_id': str,
                        'element_name': str,
                        'variant_id': str,
                        'variant_index': int,
                        'content': dict
                    },
                    ...
                ],
                'combination_id': int (si factorial),
                'new_assignment': bool
            }
        """
        
        # Verificar si ya existe asignación
        existing = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if existing:
            # Reconstruir asignaciones desde variant_assignments
            if existing.get('variant_assignments'):
                return await self._reconstruct_assignment(
                    experiment_id,
                    existing
                )
            else:
                # Asignación antigua (1 elemento)
                return await self._reconstruct_single_assignment(
                    experiment_id,
                    existing
                )
        
        # Obtener configuración del experimento
        async with self.db.acquire() as conn:
            exp_config = await conn.fetchrow(
                "SELECT config FROM experiments WHERE id = $1",
                experiment_id
            )
        
        if not exp_config:
            return None
        
        config = exp_config['config'] or {}
        combination_mode = config.get('combination_mode', CombinationMode.INDEPENDENT)
        
        # Asignar según modo
        if combination_mode == CombinationMode.FACTORIAL:
            return await self._allocate_factorial(
                experiment_id,
                user_identifier,
                session_id,
                context,
                config
            )
        else:
            return await self._allocate_independent(
                experiment_id,
                user_identifier,
                session_id,
                context
            )
    
    async def _allocate_independent(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        MODO INDEPENDIENTE:
        Cada elemento selecciona su mejor variante usando Thompson Sampling
        
        ✅ Ventajas:
        - Converge rápido
        - No hay explosión combinatoria
        - Cada elemento aprende independientemente
        
        ❌ Limitación:
        - No captura interacciones entre elementos
        """
        
        # Obtener todos los elementos del experimento
        async with self.db.acquire() as conn:
            elements = await conn.fetch(
                """
                SELECT id, name, element_order
                FROM experiment_elements
                WHERE experiment_id = $1
                ORDER BY element_order
                """,
                experiment_id
            )
        
        assignments = []
        variant_assignments_map = {}
        
        # Para cada elemento, seleccionar la mejor variante
        for element in elements:
            element_id = str(element['id'])
            
            # Obtener variantes con Thompson Sampling state
            variants = await self.variant_repo.get_variants_for_optimization(
                element_id
            )
            
            if not variants:
                continue
            
            # ✅ THOMPSON SAMPLING: Seleccionar mejor variante para este elemento
            selected_variant = await self._thompson_sampling_select(variants)
            
            if not selected_variant:
                continue
            
            # Incrementar allocation counter
            await self.variant_repo.increment_allocation(selected_variant['id'])
            
            assignments.append({
                'element_id': element_id,
                'element_name': element['name'],
                'variant_id': selected_variant['id'],
                'variant_index': selected_variant.get('variant_order', 0),
                'content': selected_variant['content']
            })
            
            variant_assignments_map[element_id] = selected_variant['id']
        
        # Guardar asignación en BD
        assignment_id = await self._save_assignment(
            experiment_id,
            user_identifier,
            variant_assignments_map,
            session_id,
            context,
            combination_mode='independent'
        )
        
        self.logger.info(
            f"Allocated user {user_identifier} to {len(assignments)} independent variants "
            f"in experiment {experiment_id}"
        )
        
        return {
            'experiment_id': experiment_id,
            'mode': 'independent',
            'assignments': assignments,
            'assignment_id': assignment_id,
            'new_assignment': True
        }
    
    async def _allocate_factorial(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str],
        context: Optional[Dict],
        config: Dict
    ) -> Dict[str, Any]:
        """
        MODO FACTORIAL:
        Trata cada combinación como una "variante" independiente
        
        ✅ Ventajas:
        - Captura interacciones entre elementos
        - Puede encontrar combinaciones inesperadamente buenas
        
        ❌ Limitación:
        - Explosión combinatoria (3x3 = 9, 5x5 = 25)
        - Requiere más tráfico
        """
        
        combinations = config.get('combinations', [])
        
        if not combinations:
            raise ValueError("No combinations found in factorial experiment")
        
        # Obtener performance de cada combinación
        combination_performances = []
        
        for combo in combinations:
            combo_id = combo['combination_id']
            variant_ids = combo['variant_ids']
            
            # Agregar performance de todas las variantes en esta combinación
            total_allocations = 0
            total_conversions = 0
            
            for variant_id in variant_ids:
                variant = await self.variant_repo.get_variant_public_data(variant_id)
                if variant:
                    total_allocations += variant['total_allocations']
                    total_conversions += variant['total_conversions']
            
            combination_performances.append({
                'combination_id': combo_id,
                'variant_ids': variant_ids,
                'total_allocations': total_allocations,
                'total_conversions': total_conversions,
                '_internal_state': {
                    'success_count': total_conversions + 1,
                    'failure_count': (total_allocations - total_conversions) + 1,
                    'samples': total_allocations
                }
            })
        
        # ✅ THOMPSON SAMPLING: Seleccionar mejor COMBINACIÓN
        selected_combination = await self._thompson_sampling_select(
            combination_performances
        )
        
        if not selected_combination:
            return None
        
        # Incrementar counters de todas las variantes en esta combinación
        for variant_id in selected_combination['variant_ids']:
            await self.variant_repo.increment_allocation(variant_id)
        
        # Construir assignments
        assignments = []
        variant_assignments_map = {}
        
        async with self.db.acquire() as conn:
            for variant_id in selected_combination['variant_ids']:
                variant = await conn.fetchrow(
                    """
                    SELECT 
                        ev.id, ev.element_id, ev.variant_order, ev.content,
                        ee.name as element_name
                    FROM element_variants ev
                    JOIN experiment_elements ee ON ev.element_id = ee.id
                    WHERE ev.id = $1
                    """,
                    variant_id
                )
                
                if variant:
                    element_id = str(variant['element_id'])
                    
                    assignments.append({
                        'element_id': element_id,
                        'element_name': variant['element_name'],
                        'variant_id': str(variant['id']),
                        'variant_index': variant['variant_order'],
                        'content': variant['content']
                    })
                    
                    variant_assignments_map[element_id] = str(variant['id'])
        
        # Guardar asignación
        assignment_id = await self._save_assignment(
            experiment_id,
            user_identifier,
            variant_assignments_map,
            session_id,
            context,
            combination_mode='factorial',
            combination_id=selected_combination['combination_id']
        )
        
        self.logger.info(
            f"Allocated user {user_identifier} to combination {selected_combination['combination_id']} "
            f"in experiment {experiment_id}"
        )
        
        return {
            'experiment_id': experiment_id,
            'mode': 'factorial',
            'assignments': assignments,
            'combination_id': selected_combination['combination_id'],
            'assignment_id': assignment_id,
            'new_assignment': True
        }
    
    # ========================================================================
    # CONVERSIONES MULTI-ELEMENTO
    # ========================================================================
    
    async def record_conversion_multi_element(
        self,
        experiment_id: str,
        user_identifier: str,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Registrar conversión para experimento multi-elemento
        
        ✅ Actualiza TODAS las variantes en la combinación asignada
        """
        
        # Obtener asignación
        assignment = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if not assignment:
            self.logger.warning(
                f"No assignment found for user {user_identifier} "
                f"in experiment {experiment_id}"
            )
            return None
        
        if assignment.get('converted_at'):
            self.logger.info(
                f"User {user_identifier} already converted in {experiment_id}"
            )
            return None
        
        # Registrar conversión en assignment
        conversion_id = await self.assignment_repo.record_conversion(
            assignment['id'],
            conversion_value=conversion_value,
            metadata=metadata
        )
        
        # Actualizar counters de TODAS las variantes involucradas
        variant_assignments = assignment.get('variant_assignments', {})
        
        if variant_assignments:
            # Multi-elemento
            for element_id, variant_id in variant_assignments.items():
                await self.variant_repo.increment_conversion(variant_id)
                self.logger.debug(
                    f"Incremented conversion for variant {variant_id} "
                    f"in element {element_id}"
                )
        elif assignment.get('variant_id'):
            # Experimento simple (1 elemento)
            await self.variant_repo.increment_conversion(assignment['variant_id'])
        
        self.logger.info(
            f"🎯 Recorded conversion for user {user_identifier} "
            f"in experiment {experiment_id}"
        )
        
        return conversion_id
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    async def _thompson_sampling_select(
        self,
        options: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Thompson Sampling selection
        
        Uses encrypted state from variants/combinations
        """
        from engine.core.allocators._bayesian import AdaptiveBayesianAllocator
        
        allocator = AdaptiveBayesianAllocator({})
        
        try:
            selected_id = await allocator.select(options, {})
            
            # Find selected option
            for option in options:
                if option.get('id') == selected_id or \
                   option.get('combination_id') == selected_id:
                    return option
            
            return None
        
        except Exception as e:
            self.logger.error(f"Thompson Sampling error: {e}")
            import random
            return random.choice(options)
    
    async def _save_assignment(
        self,
        experiment_id: str,
        user_identifier: str,
        variant_assignments_map: Dict[str, str],
        session_id: Optional[str],
        context: Optional[Dict],
        combination_mode: str,
        combination_id: Optional[int] = None
    ) -> str:
        """Guardar asignación en BD"""
        
        import json
        
        async with self.db.acquire() as conn:
            assignment_id = await conn.fetchval(
                """
                INSERT INTO assignments (
                    experiment_id,
                    user_id,
                    variant_assignments,
                    session_id,
                    context,
                    metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                experiment_id,
                user_identifier,
                json.dumps(variant_assignments_map),
                session_id,
                json.dumps(context or {}),
                json.dumps({
                    'combination_mode': combination_mode,
                    'combination_id': combination_id
                })
            )
        
        return str(assignment_id)
    
    async def _reconstruct_assignment(
        self,
        experiment_id: str,
        assignment: Dict
    ) -> Dict[str, Any]:
        """Reconstruir asignación existente desde variant_assignments"""
        
        variant_assignments = assignment.get('variant_assignments', {})
        
        if isinstance(variant_assignments, str):
            import json
            variant_assignments = json.loads(variant_assignments)
        
        assignments = []
        
        async with self.db.acquire() as conn:
            for element_id, variant_id in variant_assignments.items():
                variant = await conn.fetchrow(
                    """
                    SELECT 
                        ev.id, ev.variant_order, ev.content,
                        ee.name as element_name
                    FROM element_variants ev
                    JOIN experiment_elements ee ON ev.element_id = ee.id
                    WHERE ev.id = $1
                    """,
                    variant_id
                )
                
                if variant:
                    assignments.append({
                        'element_id': element_id,
                        'element_name': variant['element_name'],
                        'variant_id': str(variant['id']),
                        'variant_index': variant['variant_order'],
                        'content': variant['content']
                    })
        
        metadata = assignment.get('metadata', {})
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)
        
        return {
            'experiment_id': experiment_id,
            'mode': metadata.get('combination_mode', 'independent'),
            'assignments': assignments,
            'combination_id': metadata.get('combination_id'),
            'assigned_at': assignment['assigned_at'],
            'new_assignment': False
        }
    
    async def _reconstruct_single_assignment(
        self,
        experiment_id: str,
        assignment: Dict
    ) -> Dict[str, Any]:
        """Reconstruir asignación de 1 elemento (backward compatibility)"""
        
        variant_id = assignment.get('variant_id')
        
        if not variant_id:
            return None
        
        async with self.db.acquire() as conn:
            variant = await conn.fetchrow(
                """
                SELECT 
                    ev.id, ev.element_id, ev.variant_order, ev.content,
                    ee.name as element_name
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ev.id = $1
                """,
                variant_id
            )
        
        if not variant:
            return None
        
        return {
            'experiment_id': experiment_id,
            'mode': 'single_element',
            'assignments': [{
                'element_id': str(variant['element_id']),
                'element_name': variant['element_name'],
                'variant_id': str(variant['id']),
                'variant_index': variant['variant_order'],
                'content': variant['content']
            }],
            'assigned_at': assignment['assigned_at'],
            'new_assignment': False
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

async def create_multi_element_service(db_pool):
    """Factory function para crear el servicio"""
    from data_access.repositories.variant_repository import VariantRepository
    from data_access.repositories.allocation_repository import AllocationRepository
    
    variant_repo = VariantRepository(db_pool)
    assignment_repo = AllocationRepository(db_pool)
    
    return MultiElementService(db_pool, variant_repo, assignment_repo)
