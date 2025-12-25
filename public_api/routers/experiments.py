# public-api/routers/experiments.py

"""
Experiments Management API
Provides robust CRUD and optimization controls for experiments.
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional, Dict, Any
import logging

from data_access.database import DatabaseManager
from orchestration.services.service_factory import ServiceFactory
from public_api.models import (
    CreateExperimentRequest,
    UpdateExperimentRequest,
    ExperimentListResponse,
    ExperimentDetailResponse,
    ExperimentStatus,
    APIResponse,
    PaginatedResponse,
    ErrorCodes
)
from public_api.dependencies import get_db, check_rate_limit, get_current_user, PaginationParams, get_pagination
from public_api.middleware.error_handler import APIError

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=APIResponse, status_code=201)
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Create new experiment and initialize optimization strategy"""
    try:
        from orchestration.services.multi_element_service import create_multi_element_service
        
        # 1. Create base experiment in main repo
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        
        experiment_id = await exp_repo.create({
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "url": request.url,
            "status": "draft"
        })
        
        # 2. Use MultiElementService to handle elements and variants
        service = await create_multi_element_service(db)
        
        elements_config = []
        for elem in request.elements:
            elements_config.append({
                'name': elem.name,
                'selector': {
                    'type': elem.selector.type.value if hasattr(elem.selector.type, 'value') else elem.selector.type,
                    'selector': elem.selector.selector
                },
                'element_type': elem.element_type.value if hasattr(elem.element_type, 'value') else elem.element_type,
                'original_content': elem.original_content.dict(),
                'variants': [v.dict() for v in elem.variants]
            })
            
        result = await service.create_multi_element_experiment(
            experiment_id=experiment_id,
            elements_config=elements_config,
            combination_mode="independent"  # Default for now
        )
        
        return APIResponse(
            success=True,
            message="Experiment created successfully",
            data={
                "id": experiment_id,
                "elements": result['elements']
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}", exc_info=True)
        raise APIError(f"Failed to create experiment: {str(e)}", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/", response_model=PaginatedResponse[ExperimentListResponse])
async def list_experiments(
    status_filter: Optional[ExperimentStatus] = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """List experiments with pagination and status filtering"""
    try:
        async with db.pool.acquire() as conn:
            # Base query
            query = """
                SELECT 
                    e.*,
                    (SELECT COUNT(*) FROM variants v WHERE v.experiment_id = e.id) as variant_count
                FROM experiments e
                WHERE e.user_id = $1
            """
            params = [user_id]
            
            if status_filter:
                query += " AND e.status = $2"
                params.append(status_filter.value)
            
            query += " ORDER BY e.created_at DESC LIMIT $3 OFFSET $4"
            params.extend([pagination.per_page, pagination.offset])
            
            rows = await conn.fetch(query, *params)
            
            # Get total count for pagination
            total_query = "SELECT COUNT(*) FROM experiments WHERE user_id = $1"
            total_params = [user_id]
            if status_filter:
                total_query += " AND status = $2"
                total_params.append(status_filter.value)
            
            total = await conn.fetchval(total_query, *total_params)
            
        items = [
            ExperimentListResponse(
                id=str(row['id']),
                name=row['name'],
                description=row['description'],
                status=row['status'],
                optimization_strategy=row.get('optimization_strategy', 'adaptive'),
                created_at=row['created_at'],
                started_at=row.get('started_at'),
                variant_count=row['variant_count'],
                total_users=row.get('total_allocations', 0),
                conversion_rate=float(row.get('conversion_rate', 0))
            )
            for row in rows
        ]
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}", exc_info=True)
        raise APIError("Failed to fetch experiments", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get full experiment details and hierarchical performance.
    
    Returns standard ExperimentDetailResponse with unified multi-element structure.
    """
    try:
        from orchestration.services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
        
        async with db.pool.acquire() as conn:
            # 1. Get experiment basic info
            experiment = await conn.fetchrow(
                "SELECT * FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            
            if not experiment:
                raise APIError("Experiment not found or access denied", code=ErrorCodes.NOT_FOUND, status=404)
            
            # 2. Get elements
            elements_rows = await conn.fetch(
                """
                SELECT * FROM experiment_elements 
                WHERE experiment_id = $1 
                ORDER BY element_order
                """,
                experiment_id
            )
            
            # 3. Get all variants for these elements in one go
            variant_rows = await conn.fetch(
                """
                SELECT ev.*, ee.experiment_id 
                FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ee.experiment_id = $1
                ORDER BY ev.element_id, ev.variant_order
                """,
                experiment_id
            )
            
            # Group variants by element_id
            variants_by_element = {}
            for v in variant_rows:
                eid = str(v['element_id'])
                if eid not in variants_by_element:
                    variants_by_element[eid] = []
                variants_by_element[eid].append(dict(v))
            
            # 4. Prepare data for AnalyticsService
            elements_data = []
            for e in elements_rows:
                eid = str(e['id'])
                elements_data.append({
                    "id": eid,
                    "name": e['name'],
                    "element_type": e['element_type'],
                    "variants": variants_by_element.get(eid, [])
                })
            
            # 5. Run Hierarchical Analysis
            analysis = await analytics.analyze_hierarchical_experiment(
                experiment_id,
                elements_data
            )
            
        # Map to ExperimentDetailResponse
        return ExperimentDetailResponse(
            id=str(experiment['id']),
            name=experiment['name'],
            description=experiment.get('description'),
            status=experiment['status'],
            url=experiment.get('url', ''),
            traffic_allocation=float(experiment.get('traffic_allocation', 1.0)),
            confidence_threshold=float(experiment.get('confidence_threshold', 0.95)),
            created_at=experiment['created_at'],
            started_at=experiment.get('started_at'),
            # Hierarchical elements with performance
            elements=analysis['elements'],
            # Overall stats
            total_visitors=analysis['total_visitors'],
            total_conversions=analysis['total_conversions'],
            overall_conversion_rate=analysis['overall_conversion_rate']
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment {experiment_id}: {e}", exc_info=True)
        raise APIError("Failed to retrieve experiment details", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.patch("/{experiment_id}/status", response_model=APIResponse)
async def update_experiment_status(
    experiment_id: str,
    new_status: str = Query(..., pattern="^(draft|active|paused|completed)$"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Update experiment life-cycle status"""
    try:
        async with db.pool.acquire() as conn:
            # Check ownership and state transition if needed
            result = await conn.execute(
                """
                UPDATE experiments 
                SET status = $1, 
                    started_at = CASE WHEN $1 = 'active' AND started_at IS NULL THEN NOW() ELSE started_at END,
                    updated_at = NOW()
                WHERE id = $2 AND user_id = $3
                """,
                new_status, experiment_id, user_id
            )
            
            if result == "UPDATE 0":
                raise APIError("Experiment not found or permission denied", code=ErrorCodes.FORBIDDEN, status=403)
        
        return APIResponse(
            success=True,
            message=f"Experiment status updated to {new_status}"
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to update status for {experiment_id}: {e}")
        raise APIError("Failed to update status", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.delete("/{experiment_id}", response_model=APIResponse)
async def delete_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Soft delete (archive) an experiment"""
    try:
        async with db.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE experiments SET status = 'archived', updated_at = NOW() WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            
            if result == "UPDATE 0":
                raise APIError("Experiment not found or permission denied", code=ErrorCodes.FORBIDDEN, status=403)
        
        return APIResponse(success=True, message="Experiment archived successfully")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete {experiment_id}: {e}")
        raise APIError("Failed to archive experiment", code=ErrorCodes.DATABASE_ERROR, status=500)


# Public endpoints (Legacy support, though tracker/assign is preferred)
@router.get("/{experiment_id}/assign", dependencies=[Depends(check_rate_limit)])
async def legacy_assign(
    experiment_id: str,
    user_identifier: str = Query(...),
    db: DatabaseManager = Depends(get_db)
):
    """Legacy endpoint for variant assignment (redirects to tracker logic)"""
    service = await ServiceFactory.create_experiment_service(db)
    result = await service.allocate_user_to_variant(experiment_id, user_identifier)
    if not result:
        raise APIError("Experiment not found", code=ErrorCodes.NOT_FOUND, status=404)
    return result
