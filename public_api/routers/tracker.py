# public-api/routers/tracker.py

"""
Tracker API

Endpoints and event collection for the JavaScript tracker.
Uses centralized models and robust dependencies.
"""

from fastapi import APIRouter, Depends, Request
from typing import Optional, List
from datetime import datetime
import logging

from data_access.database import DatabaseManager
from orchestration.services.service_factory import ServiceFactory
from public_api.models.tracker import (
    TrackerAssignmentRequest,
    TrackerAssignmentResponse,
    TrackerConversionRequest,
    TrackerConversionResponse,
    ExperimentInfo,
    ActiveExperimentsRequest,
    ActiveExperimentsResponse,
    GenericEventRequest
)
from public_api.dependencies import get_db, check_rate_limit
from public_api.middleware.error_handler import APIError, ErrorCodes

logger = logging.getLogger(__name__)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/experiments/active", response_model=ActiveExperimentsResponse)
async def get_active_experiments_for_installation(
    request: ActiveExperimentsRequest,
    db: DatabaseManager = Depends(get_db)
):
    """
    Obtain active experiments for an installation.
    Used by JS tracker to know which experiments to run.
    """
    try:
        # Validate installation_token
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
            raise APIError("Installation not found", code=ErrorCodes.NOT_FOUND, status=404)
        
        if installation['status'] != 'active':
            return ActiveExperimentsResponse(experiments=[], count=0)
        
        # Get active experiments
        async with db.pool.acquire() as conn:
            query = """
                SELECT id, name, target_url
                FROM experiments
                WHERE user_id = $1 AND status = 'active'
            """
            params = [str(installation['user_id'])]
            
            if request.page_url:
                query += " AND (target_url IS NULL OR $2 LIKE target_url || '%')"
                params.append(request.page_url)
                
            query += " ORDER BY created_at DESC"
            experiments = await conn.fetch(query, *params)
        
        experiment_list = [
            ExperimentInfo(
                id=str(exp['id']),
                name=exp['name'],
                target_url=exp['target_url']
            )
            for exp in experiments
        ]
        
        return ActiveExperimentsResponse(
            experiments=experiment_list,
            count=len(experiment_list)
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get active experiments: {e}", exc_info=True)
        raise APIError("Internal server error", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/assign", response_model=TrackerAssignmentResponse, dependencies=[Depends(check_rate_limit)])
async def assign_variant(
    request: TrackerAssignmentRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Assign user to variant using adaptive strategy"""
    try:
        # Verify installation token
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                "SELECT id, status FROM platform_installations WHERE installation_token = $1",
                request.installation_token
            )
        
        if not installation or installation['status'] != 'active':
            raise APIError("Invalid or inactive installation token", code=ErrorCodes.UNAUTHORIZED, status=400)
        
        # Get experiment service
        service = await ServiceFactory.create_experiment_service(db)
        
        # Allocate user
        assignment = await service.allocate_user_to_variant(
            experiment_id=request.experiment_id,
            user_identifier=request.user_identifier,
            session_id=request.session_id,
            context=request.context or {}
        )
        
        if not assignment:
            raise APIError("Experiment not found or inactive", code=ErrorCodes.EXPERIMENT_NOT_FOUND, status=404)
        
        return TrackerAssignmentResponse(
            variant_id=assignment['variant_id'],
            variant_name=assignment['variant_name'],
            content=assignment['content'],
            experiment_id=assignment['experiment_id'],
            assigned_at=assignment['assigned_at']
        )
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(str(e), code=ErrorCodes.INVALID_INPUT, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in assign_variant: {e}", exc_info=True)
        raise APIError("Internal server error", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/convert", response_model=TrackerConversionResponse, dependencies=[Depends(check_rate_limit)])
async def record_conversion(
    request: TrackerConversionRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Record conversion for optimization"""
    try:
        # Verify installation token
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                "SELECT id, status FROM platform_installations WHERE installation_token = $1",
                request.installation_token
            )
        
        if not installation or installation['status'] != 'active':
            raise APIError("Invalid or inactive installation token", code=ErrorCodes.UNAUTHORIZED, status=400)
        
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
            return TrackerConversionResponse(
                success=False,
                message="No assignment found for this user"
            )
        
        return TrackerConversionResponse(
            success=True,
            conversion_id=conversion_id,
            message="Conversion recorded successfully"
        )
        
    except APIError:
        raise
    except ValueError as e:
        raise APIError(str(e), code=ErrorCodes.INVALID_INPUT, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in record_conversion: {e}", exc_info=True)
        raise APIError("Internal server error", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "service": "tracker",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ping")
async def ping():
    """Simple ping test"""
    return {"pong": True}


@router.post("/event", dependencies=[Depends(check_rate_limit)])
async def track_event(request: GenericEventRequest):
    """Track generic events (self-tracking)"""
    logger.info(f"[Tracker Event] {request.event}: {request.data}")
    return {"success": True, "message": "Event recorded"}

