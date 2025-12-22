# public-api/middleware/rate_limit.py
"""
Rate limiting middleware.

Simple in-memory rate limiter. For production, use Redis.
"""

from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """
    Simple rate limiter (in-memory).
    
    For production with multiple instances, use Redis:
    - pip install redis-py-cluster
    - Store counts in Redis with TTL
    """
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_task = None
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request"""
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:16]}"
        
        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"
    
    def _cleanup_old_requests(self, client_id: str):
        """Remove requests older than 1 minute"""
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] 
            if ts > cutoff
        ]
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed, remaining)
        """
        client_id = self._get_client_id(request)
        now = datetime.utcnow()
        
        # Cleanup old requests
        self._cleanup_old_requests(client_id)
        
        # Count recent requests
        recent_count = len(self.requests[client_id])
        
        if recent_count >= self.requests_per_minute:
            return False, 0
        
        # Check burst limit (requests in last second)
        one_second_ago = now - timedelta(seconds=1)
        burst_count = sum(
            1 for ts in self.requests[client_id] 
            if ts > one_second_ago
        )
        
        if burst_count >= self.burst_limit:
            return False, self.requests_per_minute - recent_count
        
        # Allow request
        self.requests[client_id].append(now)
        remaining = self.requests_per_minute - recent_count - 1
        
        return True, max(0, remaining)
    
    async def __call__(self, request: Request):
        """Dependency for use in routes"""
        allowed, remaining = await self.check_rate_limit(request)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMITED",
                    "retry_after_seconds": 60
                }
            )
        
        # Add headers to response
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_limit = self.requests_per_minute


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=100, burst_limit=20)


# ════════════════════════════════════════════════════════════════════════════
# PLAN-BASED RATE LIMITS
# ════════════════════════════════════════════════════════════════════════════

PLAN_RATE_LIMITS = {
    "free": {"requests_per_minute": 60, "burst": 10},
    "starter": {"requests_per_minute": 200, "burst": 30},
    "professional": {"requests_per_minute": 500, "burst": 50},
    "scale": {"requests_per_minute": 1000, "burst": 100},
    "enterprise": {"requests_per_minute": 5000, "burst": 500},
}
