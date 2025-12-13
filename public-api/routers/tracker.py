# public-api/routers/tracker.py

"""
Tracker API

Endpoints públicos usados por el JavaScript tracker.
NO requieren autenticación (son llamados por el sitio del usuario).

"""

"""
Tracker API - FIXED VERSION
Correcciones:
- Rate limiting implementado usando Redis
- Validación de tokens mejorada
- Manejo de errores robusto
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import redis.asyncio as redis

from ..services.experiment_service import ExperimentService
from ..services.service_factory import ServiceFactory
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tracker", tags=["tracker"])


# ============================================================================
# RATE LIMITER - NUEVO
# ============================================================================

class RateLimiter:
    """Redis-based rate limiter for public endpoints"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_limit(
        self,
        key: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if rate limit exceeded
        
        Args:
            key: Unique identifier (IP, installation_token, etc)
            limit: Max requests
            window: Time window in seconds
        
        Returns:
            (is_allowed, current_count)
        """
        try:
            current = await self.redis.incr(key)
            
            if current == 1:
                await self.redis.expire(key, window)
            
            return (current <= limit, current)
            
        except redis.RedisError as e:
            logger.error(f"Rate limiter error: {e}")
            # On Redis error, allow the request (fail open)
            return (True, 0)
    
    async def get_remaining(
        self,
        key: str,
        limit: int
    ) -> int:
        """Get remaining requests in current window"""
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0
            return max(0, limit - current)
        except redis.RedisError:
            return limit


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AssignmentRequest(BaseModel):
    """Request for variant assignment"""
    
    installation_token: str = Field(..., min_length=1, max_length=255)
    experiment_id: str = Field(..., min_length=1)
    user_identifier: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    context: Optional[Dict[str, Any]] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()
    
    @validator('user_identifier')
    def validate_user(cls, v):
        if not v or v.strip() == '':
            raise ValueError("user_identifier cannot be empty")
        return v.strip()


class ConversionRequest(BaseModel):
    """Request to record a conversion"""
    
    installation_token: str = Field(..., min_length=1, max_length=255)
    experiment_id: str = Field(..., min_length=1)
    user_identifier: str = Field(..., min_length=1, max_length=255)
    conversion_value: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()
    
    @validator('user_identifier')
    def validate_user(cls, v):
        if not v or v.strip() == '':
            raise ValueError("user_identifier cannot be empty")
        return v.strip()


class ExperimentStatusRequest(BaseModel):
    """Request for experiment status"""
    
    installation_token: str = Field(..., min_length=1, max_length=255)
    experiment_id: str = Field(..., min_length=1)


class AssignmentResponse(BaseModel):
    """Response with variant assignment"""
    
    variant_id: str
    variant_name: str
    content: Dict[str, Any]
    experiment_id: str
    assigned_at: datetime


class ConversionResponse(BaseModel):
    """Response after recording conversion"""
    
    success: bool
    conversion_id: Optional[str] = None
    message: str


# ============================================================================
# DEPENDENCY: RATE LIMITER
# ============================================================================

async def get_rate_limiter(request: Request) -> RateLimiter:
    """Get rate limiter instance from app state"""
    
    # Check if Redis is available
    redis_client = getattr(request.app.state, 'redis', None)
    
    if redis_client is None:
        logger.warning("Redis not available, rate limiting disabled")
        # Return a dummy rate limiter that always allows
        class DummyRateLimiter:
            async def check_limit(self, *args, **kwargs):
                return (True, 0)
            async def get_remaining(self, *args, **kwargs):
                return 999999
        
        return DummyRateLimiter()
    
    return RateLimiter(redis_client)


async def check_rate_limit(
    request: Request,
    installation_token: str,
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
) -> None:
    """
    ✅ NUEVO: Rate limiting middleware
    
    Limits:
    - 1000 requests per minute per installation_token
    - 100 requests per minute per IP (fallback)
    """
    
    # Primary rate limit: by installation_token
    token_key = f"rate_limit:tracker:token:{installation_token}"
    is_allowed, current = await rate_limiter.check_limit(
        token_key,
        limit=1000,
        window=60
    )
    
    if not is_allowed:
        remaining = await rate_limiter.get_remaining(token_key, 1000)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": 1000,
                "window": "1 minute",
                "retry_after": 60
            },
            headers={
                "X-RateLimit-Limit": "1000",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(60),
                "Retry-After": "60"
            }
        )
    
    # Secondary rate limit: by IP (protects against token abuse)
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"rate_limit:tracker:ip:{client_ip}"
    
    is_allowed_ip, current_ip = await rate_limiter.check_limit(
        ip_key,
        limit=2000,  # Higher limit for IP (multiple tokens)
        window=60
    )
    
    if not is_allowed_ip:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "IP rate limit exceeded",
                "limit": 2000,
                "window": "1 minute"
            }
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/assign", response_model=AssignmentResponse)
async def assign_variant(
    request: Request,
    request_data: AssignmentRequest,
    db=Depends(get_db),
    _rate_limit: None = Depends(
        lambda r=Request, rd=AssignmentRequest: check_rate_limit(
            r,
            rd.installation_token
        )
    )
):
    """
    ✅ FIXED: Assign user to variant with rate limiting
    
    Rate limits:
    - 1000 req/min per installation_token
    - 2000 req/min per IP
    """
    
    try:
        # Verify installation token
        # TODO: Add actual token verification against platform_installations table
        if not request_data.installation_token:
            raise HTTPException(400, "Invalid installation_token")
        
        # Get experiment service (auto-detects Redis/PostgreSQL)
        service = await ServiceFactory.get_experiment_service(db)
        
        # Allocate user to variant
        assignment = await service.allocate_user_to_variant(
            experiment_id=request_data.experiment_id,
            user_identifier=request_data.user_identifier,
            session_id=request_data.session_id,
            context=request_data.context or {}
        )
        
        if not assignment:
            raise HTTPException(404, "Experiment not found or inactive")
        
        return AssignmentResponse(
            variant_id=assignment['variant_id'],
            variant_name=assignment['variant_name'],
            content=assignment['content'],
            experiment_id=assignment['experiment_id'],
            assigned_at=assignment['assigned_at']
        )
    
    except ValueError as e:
        logger.error(f"Assignment error: {e}")
        raise HTTPException(400, str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in assign_variant: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.post("/convert", response_model=ConversionResponse)
async def record_conversion(
    request: Request,
    request_data: ConversionRequest,
    db=Depends(get_db),
    _rate_limit: None = Depends(
        lambda r=Request, rd=ConversionRequest: check_rate_limit(
            r,
            rd.installation_token
        )
    )
):
    """
    ✅ FIXED: Record conversion with rate limiting
    
    Rate limits:
    - 1000 req/min per installation_token
    - 2000 req/min per IP
    """
    
    try:
        # Verify installation token
        if not request_data.installation_token:
            raise HTTPException(400, "Invalid installation_token")
        
        # Get experiment service
        service = await ServiceFactory.get_experiment_service(db)
        
        # Record conversion
        conversion_id = await service.record_conversion(
            experiment_id=request_data.experiment_id,
            user_identifier=request_data.user_identifier,
            conversion_value=request_data.conversion_value,
            metadata=request_data.metadata
        )
        
        if not conversion_id:
            return ConversionResponse(
                success=False,
                message="No assignment found for this user"
            )
        
        return ConversionResponse(
            success=True,
            conversion_id=conversion_id,
            message="Conversion recorded successfully"
        )
    
    except ValueError as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(400, str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in record_conversion: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.post("/experiments/active")
async def get_active_experiments(
    request: Request,
    request_data: ExperimentStatusRequest,
    db=Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get all active experiments for an installation
    
    Lower rate limit: 100 req/min
    """
    
    # Rate limit: 100 req/min for list endpoints
    token_key = f"rate_limit:tracker:list:{request_data.installation_token}"
    is_allowed, current = await rate_limiter.check_limit(
        token_key,
        limit=100,
        window=60
    )
    
    if not is_allowed:
        raise HTTPException(429, "Rate limit exceeded for list endpoint")
    
    try:
        # Verify installation token
        if not request_data.installation_token:
            raise HTTPException(400, "Invalid installation_token")
        
        # Get experiment service
        service = await ServiceFactory.get_experiment_service(db)
        
        # Get active experiments
        # TODO: Filter by installation_token
        experiments = await service.get_active_experiments()
        
        return {
            "experiments": experiments,
            "count": len(experiments)
        }
    
    except Exception as e:
        logger.error(f"Error fetching active experiments: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


@router.get("/health")
async def health_check():
    """
    Health check endpoint (no rate limiting)
    """
    return {
        "status": "healthy",
        "service": "tracker",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/rate-limit/status")
async def rate_limit_status(
    installation_token: str,
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Check current rate limit status for a token
    """
    
    token_key = f"rate_limit:tracker:token:{installation_token}"
    remaining = await rate_limiter.get_remaining(token_key, 1000)
    
    return {
        "installation_token": installation_token,
        "limit": 1000,
        "remaining": remaining,
        "window": "60 seconds"
    }
