# public-api/routers/analytics.py

"""
Analytics Router - VERSIÓN PREMIUM
Exposes dedicated endpoints for experiment analysis and insights.
"""

from fastapi import APIRouter, Depends, Path, Query
import logging
from typing import Dict, Any

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user, check_rate_limit
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse, ExperimentAnalytics
from orchestration.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/experiment/{experiment_id}", response_model=ExperimentAnalytics)
async def get_experiment_analytics(
    experiment_id: str = Path(..., description="The ID of the experiment to analyze"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get detailed Bayesian analytics for an experiment.
    
    Returns high-dimensional metrics including probability of being the winner,
    expected loss, and credible intervals for each variant.
    """
    try:
        service = AnalyticsService()
        
        async with db.pool.acquire() as conn:
            # 1. Fetch experiment and verify ownership
            experiment = await conn.fetchrow(
                "SELECT * FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            
            if not experiment:
                raise APIError("Experiment not found or access denied", code=ErrorCodes.NOT_FOUND, status=404)
            
            # 2. Fetch elements and variants
            elements_rows = await conn.fetch(
                "SELECT * FROM experiment_elements WHERE experiment_id = $1 ORDER BY element_order",
                experiment_id
            )
            
            variant_rows = await conn.fetch(
                """
                SELECT ev.* FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ee.experiment_id = $1
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
            
            # Prepare data for service
            elements_data = []
            for e in elements_rows:
                eid = str(e['id'])
                elements_data.append({
                    "id": eid,
                    "name": e['name'],
                    "element_type": e['element_type'],
                    "variants": variants_by_element.get(eid, [])
                })
            
            # 3. Perform analysis
            analysis = await service.analyze_hierarchical_experiment(
                experiment_id,
                elements_data
            )
            
            # Map to ExperimentAnalytics model
            # Note: ExperimentAnalytics in models/experiment_models.py needs to be compatible
            return ExperimentAnalytics(
                experiment_id=str(experiment['id']),
                experiment_name=experiment['name'],
                status=experiment['status'],
                elements=analysis['elements'],
                total_visitors=analysis['total_visitors'],
                total_conversions=analysis['total_conversions'],
                overall_conversion_rate=analysis['overall_conversion_rate'],
                created_at=experiment['created_at'],
                started_at=experiment.get('started_at')
            )
            
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for experiment {experiment_id}: {e}", exc_info=True)
        raise APIError("Failed to perform experiment analysis", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/experiment/{experiment_id}/insights", response_model=APIResponse)
async def get_experiment_insights(
    experiment_id: str = Path(..., description="The ID of the experiment"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Get actionable AI-driven insights and recommendations.
    
    Analyzes performance trends and suggests whether to continue testing,
    deploy a winner, or refine the experiment parameters.
    """
    try:
        service = AnalyticsService()
        
        async with db.pool.acquire() as conn:
            # Verification logic similar to above...
            experiment = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            if not experiment:
                raise APIError("Experiment not found", code=ErrorCodes.NOT_FOUND, status=404)
            
            # Fetch variants for a flat analysis for recommendations
            variant_rows = await conn.fetch(
                """
                SELECT ev.* FROM element_variants ev
                JOIN experiment_elements ee ON ev.element_id = ee.id
                WHERE ee.experiment_id = $1
                """,
                experiment_id
            )
            
            if not variant_rows:
                return APIResponse(success=True, message="No data available yet", data={"recommendations": []})
            
            # Single-level analysis for recommendations if multi-element is independent
            flat_analysis = await service.analyze_experiment(experiment_id, [dict(v) for v in variant_rows])
            
            return APIResponse(
                success=True,
                message="Insights generated successfully",
                data={
                    "recommendations": flat_analysis['recommendations'],
                    "bayesian_summary": flat_analysis['bayesian_analysis'].get('winner')
                }
            )
            
    except Exception as e:
        logger.error(f"Insight generation failed for {experiment_id}: {e}")
        raise APIError("Failed to generate experiment insights", code=ErrorCodes.INTERNAL_ERROR, status=500)
