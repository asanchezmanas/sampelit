# public-api/routers/tracker.py

"""
Tracker API - VERSIÓN COMPLETA

Endpoints públicos usados por el JavaScript tracker.
NO requieren autenticación (son llamados por el sitio del usuario).

✅ Incluye endpoint nuevo: /experiments/active
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from data_access.database import get_database, DatabaseManager
from orchestration.services.service_factory import ServiceFactory

logger = logging.getLogger(__name__)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════

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


# ✅ NUEVO: Request/Response para experimentos activos
class ActiveExperimentsRequest(BaseModel):
    """Request para obtener experimentos activos"""
    installation_token: str = Field(..., min_length=1)
    page_url: Optional[str] = None
    
    @validator('installation_token')
    def validate_token(cls, v):
        if not v or v.strip() == '':
            raise ValueError("installation_token cannot be empty")
        return v.strip()


class ExperimentInfo(BaseModel):
    """Información básica de experimento"""
    id: str
    name: str
    target_url: Optional[str]


class ActiveExperimentsResponse(BaseModel):
    """Response con experimentos activos"""
    experiments: List[ExperimentInfo]
    count: int


# ════════════════════════════════════════════════════════════════════════════
# ✅ NUEVO: OBTENER EXPERIMENTOS ACTIVOS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/experiments/active", response_model=ActiveExperimentsResponse)
async def get_active_experiments_for_installation(
    request: ActiveExperimentsRequest,
    db: DatabaseManager = Depends(get_database)
):
    """
    ✅ NUEVO: Obtener experimentos activos para una instalación
    
    Usado por el tracker JavaScript para saber qué experimentos ejecutar.
    
    PUBLIC ENDPOINT - No auth required.
    
    Args:
        installation_token: Token único de la instalación
        page_url: URL actual de la página (opcional, para filtrar)
    
    Returns:
        Lista de experimentos activos que aplican a esta instalación
    
    Example:
        POST /api/v1/tracker/experiments/active
        {
            "installation_token": "inst_abc123",
            "page_url": "https://example.com/products"
        }
        
        Response:
        {
            "experiments": [
                {
                    "id": "exp-123",
                    "name": "Homepage Hero Test",
                    "target_url": "https://example.com"
                }
            ],
            "count": 1
        }
    """
    
    try:
        # Validar installation_token
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, user_id, site_url, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                request.installation_token
            )
        
        if not installation:
            logger.warning(f"Installation not found: {request.installation_token[:15]}...")
            raise HTTPException(404, "Installation not found")
        
        if installation['status'] != 'active':
            logger.info(f"Installation inactive: {installation['status']}")
            return ActiveExperimentsResponse(experiments=[], count=0)
        
        # Obtener experimentos activos del usuario para este sitio
        async with db.pool.acquire() as conn:
            
            # Si se proporciona page_url, filtrar por target_url
            if request.page_url:
                experiments = await conn.fetch(
                    """
                    SELECT 
                        e.id,
                        e.name,
                        e.target_url
                    FROM experiments e
                    WHERE e.user_id = $1
                      AND e.status = 'active'
                      AND (
                        e.target_url IS NULL 
                        OR $2 LIKE e.target_url || '%'
                      )
                    ORDER BY e.created_at DESC
                    """,
                    str(installation['user_id']),
                    request.page_url
                )
            else:
                # Sin page_url, devolver todos los experimentos activos
                experiments = await conn.fetch(
                    """
                    SELECT 
                        e.id,
                        e.name,
                        e.target_url
                    FROM experiments e
                    WHERE e.user_id = $1
                      AND e.status = 'active'
                    ORDER BY e.created_at DESC
                    """,
                    str(installation['user_id'])
                )
        
        experiment_list = [
            ExperimentInfo(
                id=str(exp['id']),
                name=exp['name'],
                target_url=exp['target_url']
            )
            for exp in experiments
        ]
        
        logger.info(
            f"Found {len(experiment_list)} active experiments for "
            f"installation {request.installation_token[:15]}..."
        )
        
        return ActiveExperimentsResponse(
            experiments=experiment_list,
            count=len(experiment_list)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active experiments: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


# ════════════════════════════════════════════════════════════════════════════
# ASIGNAR VARIANTE
# ════════════════════════════════════════════════════════════════════════════

@router.post("/assign", response_model=AssignmentResponse)
async def assign_variant(
    request: AssignmentRequest,
    db: DatabaseManager = Depends(get_database)
):
    """
    Assign user to variant
    
    This is the main allocation endpoint. Uses Thompson Sampling (adaptive strategy)
    to intelligently allocate traffic to variants.
    
    PUBLIC ENDPOINT - No auth required for visitor allocation.
    
    Rate limits:
    - 1000 req/min per installation_token (handled by middleware)
    - 2000 req/min per IP (handled by middleware)
    """
    
    try:
        # Verificar installation token (validación básica)
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, status FROM platform_installations
                WHERE installation_token = $1
                """,
                request.installation_token
            )
        
        if not installation or installation['status'] != 'active':
            raise HTTPException(400, "Invalid or inactive installation token")
        
        # Get experiment service (auto-detects Redis/PostgreSQL)
        service = await ServiceFactory.create_experiment_service(db)
        
        # Allocate user to variant
        assignment = await service.allocate_user_to_variant(
            experiment_id=request.experiment_id,
            user_identifier=request.user_identifier,
            session_id=request.session_id,
            context=request.context or {}
        )
        
        if not assignment:
            raise HTTPException(404, "Experiment not found or inactive")
        
        logger.info(
            f"Assigned user {request.user_identifier[:15]}... to variant "
            f"{assignment['variant_name']} in experiment {request.experiment_id}"
        )
        
        return AssignmentResponse(
            variant_id=assignment['variant_id'],
            variant_name=assignment['variant_name'],
            content=assignment['content'],
            experiment_id=assignment['experiment_id'],
            assigned_at=assignment['assigned_at']
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Assignment error: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in assign_variant: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


# ════════════════════════════════════════════════════════════════════════════
# REGISTRAR CONVERSIÓN
# ════════════════════════════════════════════════════════════════════════════

@router.post("/convert", response_model=ConversionResponse)
async def record_conversion(
    request: ConversionRequest,
    db: DatabaseManager = Depends(get_database)
):
    """
    Record conversion
    
    Updates the optimization algorithm with conversion data.
    This is how the system learns which variants perform better.
    
    PUBLIC ENDPOINT - No auth required.
    
    Rate limits:
    - 1000 req/min per installation_token (handled by middleware)
    - 2000 req/min per IP (handled by middleware)
    """
    
    try:
        # Verificar installation token
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, status FROM platform_installations
                WHERE installation_token = $1
                """,
                request.installation_token
            )
        
        if not installation or installation['status'] != 'active':
            raise HTTPException(400, "Invalid or inactive installation token")
        
        # Get experiment service
        service = await ServiceFactory.create_experiment_service(db)
        
        # Record conversion
        conversion_id = await service.record_conversion(
            experiment_id=request.experiment_id,
            user_identifier=request.user_identifier,
            conversion_value=request.conversion_value,
            metadata=request.metadata
        )
        
        if not conversion_id:
            logger.warning(
                f"No assignment found for user {request.user_identifier[:15]}... "
                f"in experiment {request.experiment_id}"
            )
            return ConversionResponse(
                success=False,
                message="No assignment found for this user"
            )
        
        logger.info(
            f"Conversion tracked: {conversion_id} for user "
            f"{request.user_identifier[:15]}... in experiment {request.experiment_id}"
        )
        
        return ConversionResponse(
            success=True,
            conversion_id=conversion_id,
            message="Conversion recorded successfully"
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in record_conversion: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")


# ════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """
    Health check endpoint (no rate limiting)
    
    Used by monitoring systems to verify tracker API is operational.
    """
    return {
        "status": "healthy",
        "service": "tracker",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ════════════════════════════════════════════════════════════════════════════
# PING (SIMPLE CONNECTIVITY TEST)
# ════════════════════════════════════════════════════════════════════════════

@router.get("/ping")
async def ping():
    """Simple ping endpoint for connectivity tests"""
    return {"pong": True}


# ════════════════════════════════════════════════════════════════════════════
# ✅ GENERIC EVENT TRACKING (For Self-Tracking & Custom Events)
# ════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class GenericEventRequest(BaseModel):
    """Request to track a generic event (landing_view, email_submit, etc.)"""
    event: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None

@router.post("/event")
async def track_event(request: GenericEventRequest):
    """
    Track a generic event (pageview, click, custom)
    
    PUBLIC ENDPOINT - No auth required.
    Used by Samplit's own landing pages for self-tracking (conv_track.md).
    """
    logger.info(f"[Event] {request.event}: {request.data}")
    
    # In production, this would save to an events table
    # For MVP, we just log it (can be picked up by log aggregators)
    
    return {
        "success": True,
        "event": request.event,
        "message": "Event tracked"
    }

