"""
Experiment Service with Redis - FIXED VERSION
Correcciones:
- Redis fallback robusto (graceful degradation)
- Manejo de errores mejorado
- Sincronización más confiable
"""

from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import redis.asyncio as redis

from .experiment_service import ExperimentService
from ..repositories.experiment_repository import ExperimentRepository
from ..repositories.variant_repository import VariantRepository
from ..repositories.assignment_repository import AssignmentRepository

logger = logging.getLogger(__name__)


class ExperimentServiceRedis(ExperimentService):
    """
    ✅ FIXED: Experiment service with Redis caching and graceful degradation
    
    Features:
    - Hot cache in Redis
    - Background sync to PostgreSQL
    - Automatic fallback to PostgreSQL if Redis fails
    - Robust error handling
    """
    
    def __init__(
        self,
        db_pool,
        redis_client: redis.Redis,
        experiment_repo: ExperimentRepository,
        variant_repo: VariantRepository,
        assignment_repo: AssignmentRepository
    ):
        super().__init__(db_pool, experiment_repo, variant_repo, assignment_repo)
        self.redis = redis_client
        self.logger = logging.getLogger(f"{__name__}.ExperimentServiceRedis")
    
    # ========================================================================
    # REDIS OPERATIONS WITH FALLBACK - ✅ FIXED
    # ========================================================================
    
    async def _get_variants_from_redis(
        self,
        experiment_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        ✅ FIXED: Get variants from Redis with graceful degradation
        
        Returns:
            - List of variants if found in Redis
            - None if not in cache (cache miss)
            - None if Redis error (triggers PostgreSQL fallback)
        """
        try:
            # Try to get from Redis
            cache_key = f"exp:{experiment_id}:variants"
            cached_data = await self.redis.get(cache_key)
            
            if not cached_data:
                # Cache miss - this is normal
                self.logger.debug(f"Cache miss for experiment {experiment_id}")
                return None
            
            # Parse cached data
            variants = json.loads(cached_data)
            self.logger.debug(
                f"Cache hit for experiment {experiment_id}: {len(variants)} variants"
            )
            
            return variants
        
        except redis.RedisError as e:
            # Redis connection/operation error
            self.logger.error(
                f"Redis error getting variants for {experiment_id}: {e}. "
                f"Falling back to PostgreSQL"
            )
            return None
        
        except json.JSONDecodeError as e:
            # Corrupted cache data
            self.logger.error(
                f"Corrupted cache data for {experiment_id}: {e}. "
                f"Falling back to PostgreSQL"
            )
            # Invalidate corrupted cache
            await self._safe_redis_delete(f"exp:{experiment_id}:variants")
            return None
        
        except Exception as e:
            # Unexpected error
            self.logger.error(
                f"Unexpected error in Redis get for {experiment_id}: {e}. "
                f"Falling back to PostgreSQL",
                exc_info=True
            )
            return None
    
    async def _set_variants_in_redis(
        self,
        experiment_id: str,
        variants: List[Dict[str, Any]],
        ttl: int = 3600
    ) -> bool:
        """
        ✅ FIXED: Set variants in Redis with error handling
        
        Returns:
            - True if successful
            - False if error (non-blocking)
        """
        try:
            cache_key = f"exp:{experiment_id}:variants"
            
            # Serialize variants
            cache_data = json.dumps(variants, default=str)
            
            # Set with TTL
            await self.redis.setex(cache_key, ttl, cache_data)
            
            self.logger.debug(
                f"Cached {len(variants)} variants for experiment {experiment_id} "
                f"(TTL: {ttl}s)"
            )
            
            return True
        
        except redis.RedisError as e:
            self.logger.error(f"Redis error setting cache for {experiment_id}: {e}")
            return False
        
        except Exception as e:
            self.logger.error(
                f"Unexpected error caching {experiment_id}: {e}",
                exc_info=True
            )
            return False
    
    async def _safe_redis_delete(self, key: str) -> bool:
        """
        ✅ NEW: Safe Redis delete (non-blocking)
        
        Returns:
            - True if deleted
            - False if error
        """
        try:
            await self.redis.delete(key)
            return True
        except redis.RedisError as e:
            self.logger.error(f"Redis error deleting key {key}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting key {key}: {e}")
            return False
    
    async def _safe_redis_incr(
        self,
        key: str,
        amount: int = 1
    ) -> Optional[int]:
        """
        ✅ NEW: Safe Redis increment (non-blocking)
        
        Returns:
            - New value if successful
            - None if error
        """
        try:
            new_value = await self.redis.incrby(key, amount)
            return new_value
        except redis.RedisError as e:
            self.logger.error(f"Redis error incrementing {key}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error incrementing {key}: {e}")
            return None
    
    # ========================================================================
    # OVERRIDDEN METHODS WITH REDIS CACHING - ✅ FIXED
    # ========================================================================
    
    async def allocate_user_to_variant(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ✅ FIXED: Allocate user with Redis caching and PostgreSQL fallback
        
        Flow:
        1. Try to get variants from Redis
        2. If Redis fails, fallback to PostgreSQL
        3. Use Thompson Sampling to select variant
        4. Store assignment in PostgreSQL
        5. Update Redis counters (non-blocking)
        """
        
        # Check for existing assignment
        existing = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if existing:
            # Already assigned
            variant = await self.variant_repo.get_variant(existing['variant_id'])
            
            if not variant:
                # Variant deleted, create new assignment
                pass
            else:
                return {
                    'variant_id': variant['id'],
                    'variant_name': variant['name'],
                    'content': variant['content'],
                    'experiment_id': experiment_id,
                    'assigned_at': existing['assigned_at']
                }
        
        # Get variants (Redis → PostgreSQL fallback)
        variants = await self._get_variants_from_redis(experiment_id)
        
        if variants is None:
            # Cache miss or Redis error → Load from PostgreSQL
            self.logger.info(
                f"Loading variants from PostgreSQL for experiment {experiment_id}"
            )
            
            variants = await self.variant_repo.get_variants_for_optimization(
                experiment_id
            )
            
            if not variants:
                self.logger.warning(f"No variants found for experiment {experiment_id}")
                return None
            
            # Try to cache for next time (non-blocking)
            await self._set_variants_in_redis(experiment_id, variants)
        
        # Use Thompson Sampling to select variant
        selected_variant = await self._thompson_sampling_select(variants)
        
        if not selected_variant:
            return None
        
        # Create assignment in PostgreSQL (authoritative)
        try:
            assignment_id = await self.assignment_repo.create_assignment(
                experiment_id=experiment_id,
                variant_id=selected_variant['id'],
                user_identifier=user_identifier,
                session_id=session_id,
                context=context or {}
            )
            
            # Increment allocation counter in PostgreSQL
            await self.variant_repo.increment_allocation(selected_variant['id'])
            
            # Try to increment in Redis (non-blocking)
            redis_key = f"exp:{experiment_id}:var:{selected_variant['id']}:allocations"
            await self._safe_redis_incr(redis_key)
            
            return {
                'variant_id': selected_variant['id'],
                'variant_name': selected_variant['name'],
                'content': selected_variant['content'],
                'experiment_id': experiment_id,
                'assigned_at': datetime.utcnow()
            }
        
        except Exception as e:
            self.logger.error(
                f"Error creating assignment for {user_identifier} "
                f"in experiment {experiment_id}: {e}",
                exc_info=True
            )
            return None
    
    async def record_conversion(
        self,
        experiment_id: str,
        user_identifier: str,
        conversion_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        ✅ FIXED: Record conversion with Redis caching
        
        Flow:
        1. Find assignment in PostgreSQL
        2. Update conversion in PostgreSQL
        3. Update Redis counters (non-blocking)
        """
        
        # Find assignment (PostgreSQL is authoritative)
        assignment = await self.assignment_repo.get_assignment(
            experiment_id,
            user_identifier
        )
        
        if not assignment:
            self.logger.warning(
                f"No assignment found for {user_identifier} "
                f"in experiment {experiment_id}"
            )
            return None
        
        if assignment['converted_at']:
            # Already converted
            self.logger.info(
                f"User {user_identifier} already converted "
                f"in experiment {experiment_id}"
            )
            return None
        
        # Record conversion in PostgreSQL
        try:
            conversion_id = await self.assignment_repo.record_conversion(
                assignment['id'],
                conversion_value=conversion_value,
                metadata=metadata
            )
            
            # Increment conversion counter in PostgreSQL
            await self.variant_repo.increment_conversion(assignment['variant_id'])
            
            # Try to increment in Redis (non-blocking)
            redis_key = f"exp:{experiment_id}:var:{assignment['variant_id']}:conversions"
            await self._safe_redis_incr(redis_key)
            
            return conversion_id
        
        except Exception as e:
            self.logger.error(
                f"Error recording conversion for {user_identifier}: {e}",
                exc_info=True
            )
            return None
    
    async def invalidate_experiment_cache(self, experiment_id: str) -> None:
        """
        ✅ FIXED: Invalidate all Redis cache for an experiment
        
        Patterns to invalidate:
        - exp:{id}:variants
        - exp:{id}:var:*:allocations
        - exp:{id}:var:*:conversions
        """
        
        patterns = [
            f"exp:{experiment_id}:variants",
            f"exp:{experiment_id}:var:*:allocations",
            f"exp:{experiment_id}:var:*:conversions"
        ]
        
        for pattern in patterns:
            try:
                if "*" in pattern:
                    # Pattern matching - scan and delete
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis.scan(
                            cursor,
                            match=pattern,
                            count=100
                        )
                        
                        if keys:
                            await self.redis.delete(*keys)
                        
                        if cursor == 0:
                            break
                else:
                    # Exact key
                    await self._safe_redis_delete(pattern)
            
            except redis.RedisError as e:
                self.logger.error(
                    f"Redis error invalidating pattern {pattern}: {e}"
                )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error invalidating pattern {pattern}: {e}"
                )
        
        self.logger.info(f"Invalidated cache for experiment {experiment_id}")
    
    # ========================================================================
    # BACKGROUND SYNC (Optional for future enhancement)
    # ========================================================================
    
    async def sync_redis_to_postgresql(self, experiment_id: str) -> bool:
        """
        ✅ NEW: Sync Redis counters to PostgreSQL
        
        This can be called periodically to ensure consistency
        """
        try:
            # Get all variants
            variants = await self.variant_repo.get_variants_for_experiment(
                experiment_id
            )
            
            for variant in variants:
                # Get Redis counters
                alloc_key = f"exp:{experiment_id}:var:{variant['id']}:allocations"
                conv_key = f"exp:{experiment_id}:var:{variant['id']}:conversions"
                
                redis_alloc = await self.redis.get(alloc_key)
                redis_conv = await self.redis.get(conv_key)
                
                if redis_alloc or redis_conv:
                    # Update PostgreSQL
                    # This is a placeholder - implement if needed
                    pass
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error syncing Redis to PostgreSQL: {e}")
            return False
