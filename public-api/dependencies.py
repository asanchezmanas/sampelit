# public-api/dependencies.py
"""
Shared dependencies for FastAPI routes.

Centralized auth, database, and utility dependencies.
Import these in routers instead of duplicating code.
"""

from fastapi import Depends, HTTPException, Header, Request
from typing import Optional
import os
import logging

from data_access.database import get_database, DatabaseManager
from public_api.middleware.rate_limit import rate_limiter

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════════════════

async def get_db() -> DatabaseManager:
    """
    Get database connection.
    Use in routes: db: DatabaseManager = Depends(get_db)
    """
    return await get_database()


# ════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ════════════════════════════════════════════════════════════════════════════

async def get_optional_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """Get API key if provided (optional auth)"""
    return x_api_key


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """Require valid API key"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "API key required", "code": "UNAUTHORIZED"}
        )
    
    # TODO: Validate API key against database
    # For now, just check it exists and has correct format
    if len(x_api_key) < 20:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid API key format", "code": "INVALID_TOKEN"}
        )
    
    return x_api_key


async def get_current_user_from_key(
    api_key: str = Depends(require_api_key),
    db: DatabaseManager = Depends(get_db)
) -> str:
    """
    Get user ID from API key.
    
    Returns user_id associated with the API key.
    """
    try:
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT user_id FROM api_keys WHERE key_hash = $1 AND revoked = false",
                api_key  # TODO: Hash the key before lookup
            )
            
            if not result:
                raise HTTPException(
                    status_code=401,
                    detail={"error": "API key not found or revoked", "code": "INVALID_TOKEN"}
                )
            
            return result['user_id']
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Authentication service error", "code": "INTERNAL_ERROR"}
        )


# ════════════════════════════════════════════════════════════════════════════
# RATE LIMITING
# ════════════════════════════════════════════════════════════════════════════

async def check_rate_limit(request: Request):
    """
    Check rate limit for request.
    Use: Depends(check_rate_limit)
    """
    await rate_limiter(request)


# ════════════════════════════════════════════════════════════════════════════
# REQUEST CONTEXT
# ════════════════════════════════════════════════════════════════════════════

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


# ════════════════════════════════════════════════════════════════════════════
# COMMON QUERY PARAMS
# ════════════════════════════════════════════════════════════════════════════

class PaginationParams:
    """Common pagination parameters"""
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20
    ):
        self.page = max(1, page)
        self.per_page = min(100, max(1, per_page))
        self.offset = (self.page - 1) * self.per_page


def get_pagination(
    page: int = 1, 
    per_page: int = 20
) -> PaginationParams:
    """Get pagination params: Depends(get_pagination)"""
    return PaginationParams(page, per_page)
