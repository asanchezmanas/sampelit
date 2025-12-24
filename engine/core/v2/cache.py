# engine/core/cache.py (ENHANCED)

"""
Enhanced caching with Redis support

Supports both:
- In-memory cache (development)
- Redis cache (production)
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Production Redis cache
    
    Benefits over in-memory:
    - Shared across instances
    - Survives restarts
    - Scales horizontally
    """
    
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int = 60,
        key_prefix: str = 'samplit:'
    ):
        self.redis_url = redis_url
        self.ttl = ttl_seconds
        self.key_prefix = key_prefix
        self.client: Optional[redis.Redis] = None
        
        # Metrics
        self._hits = 0
        self._misses = 0
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(
            self.redis_url,
            encoding='utf-8',
            decode_responses=True,
            max_connections=20
        )
        
        logger.info(f"Connected to Redis: {self.redis_url}")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        full_key = self._make_key(key)
        
        value = await self.client.get(full_key)
        
        if value is None:
            self._misses += 1
            return None
        
        self._hits += 1
        
        # Deserialize JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_override: Optional[int] = None
    ):
        """Set value in Redis"""
        full_key = self._make_key(key)
        ttl = ttl_override if ttl_override is not None else self.ttl
        
        # Serialize to JSON
        if not isinstance(value, str):
            value = json.dumps(value)
        
        await self.client.setex(full_key, ttl, value)
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        full_key = self._make_key(key)
        deleted = await self.client.delete(full_key)
        return deleted > 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        full_pattern = self._make_key(pattern)
        
        # Scan for keys
        keys = []
        async for key in self.client.scan_iter(match=full_pattern):
            keys.append(key)
        
        if keys:
            deleted = await self.client.delete(*keys)
            return deleted
        
        return 0
    
    async def clear(self):
        """Clear all keys with our prefix"""
        await self.delete_pattern('*')
    
    def get_metrics(self) -> dict:
        """Get cache metrics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate_percent': hit_rate
        }


# Factory function
def create_cache(use_redis: bool = True):
    """
    Create appropriate cache instance
    
    Args:
        use_redis: Use Redis if True, else in-memory
    """
    if use_redis:
        import os
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        return RedisCache(redis_url)
    else:
        from engine.core.cache import AllocatorCache
        return AllocatorCache()
