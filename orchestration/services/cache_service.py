# orchestration/services/cache_service.py

"""
Cache Service - Política de Uso

✅ CACHEAR (TTL largo):
  • Metadata de experimentos (nombre, descripción, config)
  • Listas de experimentos por usuario
  • Datos de usuario
  • Cualquier dato que cambie rara vez

❌ NO CACHEAR:
  • Estado Engine
  • Contadores de asignaciones/conversiones en tiempo real
  • Cualquier dato que cambie con cada request

REGLA DE ORO:
  Si el dato cambia más de 1 vez por minuto → NO cachear
  Si el dato cambia menos de 1 vez por hora → Sí cachear
"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """
    Cache service con fallback a in-memory
    
    ✅ Production: Usar Redis
    ✅ Development: Usa dict en memoria si Redis no disponible
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self.in_memory_cache = {}  # Fallback
        self.use_redis = False
        
        # Try to connect to Redis
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url, 
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"⚠️ Redis unavailable, using in-memory cache: {e}")
                self.redis_client = None
        else:
            logger.info("📦 Using in-memory cache (no Redis URL)")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value
        
        Returns None if not found or expired
        """
        try:
            if self.use_redis and self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
                return None
            else:
                # In-memory fallback
                if key in self.in_memory_cache:
                    entry = self.in_memory_cache[key]
                    # Check if expired
                    if entry['expires_at'] and datetime.now() > entry['expires_at']:
                        del self.in_memory_cache[key]
                        return None
                    return entry['value']
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set cached value with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
        
        Returns:
            True if successful
        """
        try:
            if self.use_redis and self.redis_client:
                serialized = json.dumps(value, default=str)
                self.redis_client.setex(key, ttl, serialized)
                return True
            else:
                # In-memory fallback
                self.in_memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.now() + timedelta(seconds=ttl) if ttl else None
                }
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) cache entry
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if deleted
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
                return True
            else:
                if key in self.in_memory_cache:
                    del self.in_memory_cache[key]
                return True
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Pattern like "experiments:*"
        
        Returns:
            Number of keys deleted
        """
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # In-memory: simple prefix matching
                count = 0
                keys_to_delete = [
                    k for k in self.in_memory_cache.keys() 
                    if k.startswith(pattern.replace('*', ''))
                ]
                for key in keys_to_delete:
                    del self.in_memory_cache[key]
                    count += 1
                return count
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")
            return 0
    
    # ============================================
    # CONVENIENCE METHODS (METADATA ONLY)
    # ============================================
    
    def get_experiment_metadata(self, experiment_id: str) -> Optional[Dict]:
        """
        ✅ Get cached experiment METADATA
        
        Solo metadata estática, NO estado Engine
        """
        key = f"experiment_meta:{experiment_id}"
        return self.get(key)
    
    def set_experiment_metadata(self, experiment_id: str, metadata: Dict, ttl: int = 300):
        """✅ Cache experiment metadata (5 min default)"""
        key = f"experiment_meta:{experiment_id}"
        self.set(key, metadata, ttl)
    
    def invalidate_experiment(self, experiment_id: str):
        """
        ✅ Invalidar cache de metadata cuando cambia
        
        Usar cuando:
        - Cambias nombre
        - Cambias status
        - Cambias configuración
        """
        self.invalidate(f"experiment_meta:{experiment_id}")
    
    # ============================================
    # ❌ REMOVED: No más cache de variants
    # ============================================
    # def get_variants() - REMOVED
    # def set_variants() - REMOVED
    
    def clear_all(self):
        """Clear all cache (for testing)"""
        if self.use_redis and self.redis_client:
            self.redis_client.flushdb()
        else:
            self.in_memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.use_redis and self.redis_client:
            info = self.redis_client.info()
            return {
                'backend': 'redis',
                'used_memory': info.get('used_memory_human'),
                'total_keys': self.redis_client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        else:
            return {
                'backend': 'in-memory',
                'total_keys': len(self.in_memory_cache)
            }
