# sampelit/orchestration/services/cache_service.py

"""
Cache Service - FIXED VERSION
Correcciones:
- Invalidación completa de cache (metadata + tracker + Redis)
- Manejo de patrones mejorado
- Logging más detallado
"""

import logging
from typing import Any, Optional, List, Dict
import redis.asyncio as redis
import json

logger = logging.getLogger(__name__)


class CacheService:
    """
    ✅ FIXED: Cache service with comprehensive invalidation
    
    Features:
    - Pattern-based invalidation
    - Multiple cache types (metadata, tracker, variants)
    - Robust error handling
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(f"{__name__}.CacheService")
    
    # ========================================================================
    # BASIC CACHE OPERATIONS
    # ========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.RedisError as e:
            self.logger.error(f"Redis error getting key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            data = json.dumps(value, default=str)
            
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
            
            return True
        except redis.RedisError as e:
            self.logger.error(f"Redis error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete single key"""
        try:
            await self.redis.delete(key)
            return True
        except redis.RedisError as e:
            self.logger.error(f"Redis error deleting key {key}: {e}")
            return False
    
    # ========================================================================
    # PATTERN-BASED OPERATIONS - ✅ IMPROVED
    # ========================================================================
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        ✅ IMPROVED: Delete all keys matching pattern
        
        Returns: Number of keys deleted
        """
        try:
            deleted_count = 0
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)
                    self.logger.debug(
                        f"Deleted {len(keys)} keys matching {pattern}"
                    )
                
                if cursor == 0:
                    break
            
            if deleted_count > 0:
                self.logger.info(
                    f"✅ Deleted {deleted_count} keys matching {pattern}"
                )
            
            return deleted_count
        
        except redis.RedisError as e:
            self.logger.error(f"Redis error deleting pattern {pattern}: {e}")
            return 0
    
    # ========================================================================
    # EXPERIMENT CACHE INVALIDATION - ✅ FIXED
    # ========================================================================
    
    async def invalidate_experiment(self, experiment_id: str) -> Dict[str, int]:
        """
        ✅ FIXED: Comprehensive experiment cache invalidation
        
        Invalidates:
        1. Experiment metadata
        2. Tracker cache
        3. Variant cache (Redis service)
        4. Analytics cache
        
        Returns: Dict with counts of deleted keys per pattern
        """
        
        patterns_to_invalidate = [
            # Metadata cache
            f"experiment_meta:{experiment_id}",
            f"experiment:{experiment_id}:*",
            
            # Tracker cache
            f"tracker:experiments:*:{experiment_id}*",
            f"tracker:exp:{experiment_id}:*",
            
            # Variant cache (Redis service)
            f"exp:{experiment_id}:variants",
            f"exp:{experiment_id}:var:*",
            
            # Analytics cache
            f"analytics:{experiment_id}:*",
            
            # Rate limiting (optional - only if you want to reset limits)
            # f"rate_limit:tracker:*:{experiment_id}*",
        ]
        
        results = {}
        
        for pattern in patterns_to_invalidate:
            if "*" in pattern:
                # Pattern matching
                count = await self.delete_pattern(pattern)
                results[pattern] = count
            else:
                # Exact key
                success = await self.delete(pattern)
                results[pattern] = 1 if success else 0
        
        total_deleted = sum(results.values())
        
        self.logger.info(
            f"🗑️  Invalidated {total_deleted} cache entries for "
            f"experiment {experiment_id}"
        )
        
        return results
    
    async def invalidate_variant(
        self,
        experiment_id: str,
        variant_id: str
    ) -> int:
        """
        ✅ NEW: Invalidate cache for a specific variant
        
        Useful when variant is updated
        """
        
        patterns = [
            f"exp:{experiment_id}:var:{variant_id}:*",
            f"variant:{variant_id}:*"
        ]
        
        total_deleted = 0
        
        for pattern in patterns:
            count = await self.delete_pattern(pattern)
            total_deleted += count
        
        # Also invalidate experiment variants cache
        await self.delete(f"exp:{experiment_id}:variants")
        total_deleted += 1
        
        self.logger.info(
            f"🗑️  Invalidated {total_deleted} cache entries for "
            f"variant {variant_id}"
        )
        
        return total_deleted
    
    # ========================================================================
    # USER CACHE INVALIDATION
    # ========================================================================
    
    async def invalidate_user(self, user_identifier: str) -> int:
        """
        Invalidate all cache for a user
        
        Useful for testing or user data deletion
        """
        
        patterns = [
            f"user:{user_identifier}:*",
            f"assignment:*:{user_identifier}",
        ]
        
        total_deleted = 0
        
        for pattern in patterns:
            count = await self.delete_pattern(pattern)
            total_deleted += count
        
        self.logger.info(
            f"🗑️  Invalidated {total_deleted} cache entries for "
            f"user {user_identifier}"
        )
        
        return total_deleted
    
    # ========================================================================
    # GLOBAL CACHE OPERATIONS
    # ========================================================================
    
    async def flush_all(self) -> bool:
        """
        ⚠️  DANGER: Flush entire cache
        
        Use only in development or emergency
        """
        try:
            await self.redis.flushdb()
            self.logger.warning("⚠️  Flushed entire cache database")
            return True
        except redis.RedisError as e:
            self.logger.error(f"Error flushing cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns info about cache size, memory, etc.
        """
        try:
            info = await self.redis.info('stats')
            memory = await self.redis.info('memory')
            
            return {
                'total_keys': await self.redis.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'memory_used': memory.get('used_memory_human', 'unknown'),
                'memory_peak': memory.get('used_memory_peak_human', 'unknown')
            }
        
        except redis.RedisError as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
# Initialize
cache = CacheService(redis_client)

# Invalidate experiment (comprehensive)
results = await cache.invalidate_experiment("exp-123")
# Returns: {
#   "experiment_meta:exp-123": 1,
#   "tracker:experiments:*:exp-123*": 5,
#   "exp:exp-123:variants": 1,
#   "exp:exp-123:var:*": 3,
#   ...
# }

# Invalidate specific variant
count = await cache.invalidate_variant("exp-123", "var-456")

# Get cache stats
stats = await cache.get_cache_stats()
# Returns: {
#   "total_keys": 1234,
#   "hits": 5678,
#   "misses": 123,
#   "hit_rate": 97.88,
#   ...
# }
"""
