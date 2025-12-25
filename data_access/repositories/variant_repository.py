# data-access/repositories/variant_repository.py
"""
Variant Repository - FIXED VERSION (Adapted to element_variants schema)

Correcciones:
- increment_allocation() con operación atómica usando RETURNING
- increment_conversion() con operación atómica usando RETURNING
- Compatible con schema element_variants/experiment_elements
- Mantiene encriptación de algorithm_state
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
import json

class VariantRepository(BaseRepository):
    """
    Repository for variants 
    
    Handles encryption of algorithm internal state
    FIXED: Atomic operations for increment methods
    """
    
    async def create_variant(self,
                            experiment_id: str,
                            name: str,
                            content: Dict[str, Any],
                            initial_algorithm_state: Dict[str, Any],
                            variant_order: int = 0,
                            conn: Optional[Any] = None) -> str:
        """
        Create variant with encrypted algorithm state
        """
        
        # Encrypt algorithm state
        encrypted_state = self._encrypt_algorithm_state(initial_algorithm_state)
        
        query = """
            INSERT INTO element_variants (
                element_id, name, content, algorithm_state, variant_order
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        if conn:
            variant_id = await conn.fetchval(
                query,
                experiment_id,
                name,
                json.dumps(content),
                encrypted_state,
                variant_order
            )
        else:
            async with self.db.acquire() as conn_new:
                variant_id = await conn_new.fetchval(
                    query,
                    experiment_id,
                    name,
                    json.dumps(content),
                    encrypted_state,
                    variant_order
                )
        
        return str(variant_id)
    
    async def get_variants_for_experiment(self, experiment_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all variants for an experiment via its elements"""
        async with self.db.acquire() as conn:
            query = """
                SELECT 
                    ev.id, ee.id as element_id, ev.name, ev.content,
                    ev.total_allocations, ev.total_conversions,
                    ev.conversion_rate, ev.is_active, ev.created_at
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ee.experiment_id = $1
            """
            rows = await conn.fetch(query, experiment_id)
            return [dict(row) for row in rows]

    async def get_variant_with_algorithm_state(self, 
                                               variant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get variant WITH decrypted algorithm state
        
        ⚠️  ONLY use this in backend services, NEVER expose in API
        """
        
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    ev.id, ee.experiment_id, ev.name, ev.content,
                    ev.algorithm_state,
                    ev.total_allocations, ev.total_conversions,
                    ev.conversion_rate as observed_conversion_rate,
                    ev.created_at, ev.updated_at
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ev.id = $1
                """,
                variant_id
            )
        
        if not row:
            return None
        
        variant = dict(row)
        
        # Decrypt algorithm state
        if row['algorithm_state']:
            variant['algorithm_state_decrypted'] = self._decrypt_algorithm_state(
                row['algorithm_state']
            )
        else:
            variant['algorithm_state_decrypted'] = {}
        
        # Remove encrypted data from response
        del variant['algorithm_state']
        
        return variant
    
    async def update_algorithm_state(self,
                                     variant_id: str,
                                     new_state: Dict[str, Any]) -> None:
        """
        Update algorithm internal state
        
        Called after each allocation/conversion to update
        Thompson Sampling parameters, etc.
        """
        
        # Encrypt new state
        encrypted_state = self._encrypt_algorithm_state(new_state)
        
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE element_variants
                SET 
                    algorithm_state = $1,
                    updated_at = NOW()
                WHERE id = $2
                """,
                encrypted_state,
                variant_id
            )
    
    async def get_variants_for_optimization(self,
                                           experiment_id: str) -> List[Dict[str, Any]]:
        """
        Get all variants with decrypted state for optimization
        
        This is what the optimizer uses internally
        """
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    ev.id, ev.name, ev.content,
                    ev.algorithm_state,
                    ev.total_allocations, ev.total_conversions,
                    ev.conversion_rate as observed_conversion_rate,
                    TRUE as is_active
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ee.experiment_id = $1
                """,
                experiment_id
            )
        
        variants = []
        for row in rows:
            variant = dict(row)
            
            # Decrypt algorithm state
            if row['algorithm_state']:
                state = self._decrypt_algorithm_state(row['algorithm_state'])
                variant['algorithm_state'] = state
            else:
                variant['algorithm_state'] = {
                    'alpha': 1.0,
                    'beta': 1.0,
                    'samples': 0,
                    'algorithm_type': 'bayesian'
                }
            
            variants.append(variant)
        
        return variants
    
    async def get_variant_public_data(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get variant data WITHOUT algorithm state
        
        Safe for API exposure
        """
        
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    ev.id, ee.experiment_id, ev.name, ev.content,
                    ev.total_allocations, ev.total_conversions,
                    ev.conversion_rate as observed_conversion_rate,
                    TRUE as is_active, ev.created_at
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ev.id = $1
                """,
                variant_id
            )
        
        return dict(row) if row else None

    async def increment_conversion(self, variant_id: str) -> int:
        """
        ✅ FIXED: Increment conversion count atomically with RETURNING
    
        Called after recording a conversion in allocations table.
        Updates public-facing metrics.
        
        Returns:
            New total_conversions value
        
        Raises:
            ValueError if variant not found
        """
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                UPDATE element_variants
                SET 
                    total_conversions = total_conversions + 1,
                    conversion_rate = 
                        (total_conversions + 1)::DECIMAL / 
                        GREATEST(total_allocations, 1)::DECIMAL,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING total_conversions, conversion_rate
                """,
                variant_id
            )
        
        if result is None:
            raise ValueError(f"Variant {variant_id} not found")
        
        return result['total_conversions']

    async def increment_allocation(self, variant_id: str) -> int:
        """
        ✅ FIXED: Increment allocation count atomically with RETURNING
        
        Called when user is assigned to this variant.
        
        Returns:
            New total_allocations value
        
        Raises:
            ValueError if variant not found
        """
        async with self.db.acquire() as conn:
            new_total = await conn.fetchval(
                """
                UPDATE element_variants
                SET 
                    total_allocations = total_allocations + 1,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING total_allocations
                """,
                variant_id
            )
        
        if new_total is None:
            raise ValueError(f"Variant {variant_id} not found")
        
        return new_total

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get variant by ID (required by BaseRepository)"""
        return await self.get_variant_public_data(id)

    async def create(self, data: Dict[str, Any]) -> str:
        """Create variant (required by BaseRepository)"""
        return await self.create_variant(
            experiment_id=data['experiment_id'],  # Esto será element_id en tu caso
            name=data['name'],
            content=data['content'],
            initial_algorithm_state=data.get('initial_algorithm_state', {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'alpha': 1.0,
                'beta': 1.0,
                'algorithm_type': 'bayesian'
            })
        )

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update variant (required by BaseRepository)"""
        if 'algorithm_state' in data:
            await self.update_algorithm_state(id, data['algorithm_state'])
            return True
        return False
