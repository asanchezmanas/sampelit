# public-api/dependencies.py
"""
Shared dependencies for FastAPI routes.

Centralized auth, database, and utility dependencies.
Import these in routers instead of duplicating code.
"""

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

import jwt
from config.settings import settings
from public_api.middleware.error_handler import APIError, ErrorCodes

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify JWT and return user_id"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=['HS256']
        )
        user_id = payload.get('sub')
        if not user_id:
            raise APIError("Invalid token: sub claim missing", code=ErrorCodes.INVALID_TOKEN, status=401)
        return user_id
    except jwt.ExpiredSignatureError:
        raise APIError("Token expired", code=ErrorCodes.TOKEN_EXPIRED, status=401)
    except jwt.InvalidTokenError:
        raise APIError("Invalid token", code=ErrorCodes.INVALID_TOKEN, status=401)


async def get_current_admin_user(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
) -> str:
    """
    Verify user is an admin.
    """
    async with db.pool.acquire() as conn:
        role = await conn.fetchval(
            "SELECT role FROM users WHERE id = $1",
            user_id
        )
    
    if role != 'admin':
        raise APIError(
            "Admin privileges required", 
            code=ErrorCodes.FORBIDDEN, 
            status=403
        )
    
    return user_id


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> str:
    """Require valid API key"""
    if not x_api_key:
        raise APIError("API key required", code=ErrorCodes.UNAUTHORIZED, status=401)
    
    # TODO: Validate API key against database
    if len(x_api_key) < 20:
        raise APIError("Invalid API key format", code=ErrorCodes.INVALID_TOKEN, status=401)
    
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
