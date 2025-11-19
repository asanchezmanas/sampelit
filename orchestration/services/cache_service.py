# orchestration/services/cache_service.py

import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    def get_variants(self, experiment_id: str) -> Optional[list]:
        """Get cached variants"""
        key = f"exp:{experiment_id}:variants"
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None
    
    def set_variants(self, experiment_id: str, variants: list, ttl: int = 300):
        """Cache variants for 5 minutes"""
        key = f"exp:{experiment_id}:variants"
        self.redis.setex(key, ttl, json.dumps(variants, default=str))
    
    def invalidate_experiment(self, experiment_id: str):
        """Invalidate cache when experiment changes"""
        key = f"exp:{experiment_id}:variants"
        self.redis.delete(key)
