# data-access/repositories/variant_repository.py

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
import json

class VariantRepository(BaseRepository):
    """
    Repository for variants 
    
    Handles encryption of algorithm internal state
    """
    
    async def create_variant(self,
                            experiment_id: str,
                            name: str,
                            content: Dict[str, Any],
                            initial_algorithm_state: Dict[str, Any]) -> str:
        """
        Create variant with encrypted algorithm state
        
        Args:
            initial_algorithm_state: Dict like:
                {
                    'alpha': 1.0,
                    'beta': 1.0,
                    'exploration_bonus': 0.0,
                    'algorithm_type': 'bayesian'  # For internal use
                }
        """
        
        # Encrypt algorithm state
        encrypted_state = self._encrypt_algorithm_state(initial_algorithm_state)
        
        async with self.db.acquire() as conn:
            variant_id = await conn.fetchval(
                """
                INSERT INTO variants (
                    experiment_id, name, content, algorithm_state, state_version
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                experiment_id,
                name,
                json.dumps(content),
                encrypted_state,
                1  # Version 1
            )
        
        return str(variant_id)
    
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
                    id, experiment_id, name, content,
                    algorithm_state, state_version,
                    total_allocations, total_conversions,
                    observed_conversion_rate,
                    created_at, updated_at
                FROM variants
                WHERE id = $1
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
                UPDATE variants
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
                    id, name, content,
                    algorithm_state,
                    total_allocations, total_conversions,
                    observed_conversion_rate,
                    is_active
                FROM variants
                WHERE experiment_id = $1 AND is_active = true
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
                    'beta': 1.0
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
                    id, experiment_id, name, content,
                    total_allocations, total_conversions,
                    observed_conversion_rate,
                    is_active, created_at
                FROM variants
                WHERE id = $1
                """,
                variant_id
            )
        
        return dict(row) if row else None

    # data-access/repositories/variant_repository.py
    # AGREGAR este método a la clase VariantRepository

    async def increment_conversion(self, variant_id: str) -> None:
        """
        Increment conversion count and update metrics
    
        Called after recording a conversion in allocations table.
        Updates public-facing metrics.
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE variants
                SET 
                    total_conversions = total_conversions + 1,
                    observed_conversion_rate = 
                        (total_conversions + 1)::DECIMAL / 
                        GREATEST(total_allocations, 1)::DECIMAL,
                    updated_at = NOW()
                WHERE id = $1
                """,
                variant_id
            )

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get variant by ID (required by BaseRepository)"""
        return await self.get_variant_public_data(id)

    async def create(self, data: Dict[str, Any]) -> str:
        """Create variant (required by BaseRepository)"""
        return await self.create_variant(
            experiment_id=data['experiment_id'],
            name=data['name'],
            content=data['content'],
            initial_algorithm_state=data.get('initial_algorithm_state', {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'algorithm_type': 'bayesian'
            })
        )

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update variant (required by BaseRepository)"""
        if 'algorithm_state' in data:
            await self.update_algorithm_state(id, data['algorithm_state'])
            return True
        return False

    async def increment_allocation(self, variant_id: str) -> None:
    """
    Increment allocation count
    
    Called when user is assigned to this variant.
    """
    async with self.db.acquire() as conn:
        await conn.execute(
            """
            UPDATE variants
            SET 
                total_allocations = total_allocations + 1,
                updated_at = NOW()
            WHERE id = $1
            """,
            variant_id
        )
