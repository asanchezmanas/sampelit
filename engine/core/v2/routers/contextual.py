# public_api/routers/contextual.py

"""
Contextual Bandits API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from engine.services.contextual_service import ContextualService
from data_access.database import get_database

router = APIRouter()


class SegmentPerformance(BaseModel):
    segment_key: str
    context: dict
    visits: int
    conversions: int
    conversion_rate: float
    best_variant: Optional[str]


class SegmentLift(BaseModel):
    segment_key: str
    context: dict
    variant: str
    segment_cr: float
    global_cr: float
    lift_percent: float
    traffic: int
    samples: int


class SegmentInsights(BaseModel):
    summary: dict
    top_segments: List[SegmentPerformance]
    high_performing_segments: List[SegmentLift]
    underperforming_segments: List[SegmentLift]
    traffic_distribution: List[dict]
    recommendations: List[str]


@router.get('/experiments/{experiment_id}/segments', response_model=List[SegmentPerformance])
async def get_segments(
    experiment_id: str,
    limit: int = Query(10, ge=1, le=100),
    min_samples: int = Query(50, ge=10),
    db = Depends(get_database)
):
    """Get top performing segments for experiment"""
    
    service = ContextualService(db.pool)
    
    segments = await service.get_top_segments(
        experiment_id,
        limit=limit,
        min_samples=min_samples
    )
    
    return segments


@router.get('/experiments/{experiment_id}/segments/lift', response_model=List[SegmentLift])
async def get_segment_lift(
    experiment_id: str,
    min_samples: int = Query(50, ge=10),
    db = Depends(get_database)
):
    """Get segment lift analysis"""
    
    service = ContextualService(db.pool)
    
    lift_data = await service.get_segment_lift_analysis(
        experiment_id,
        min_samples=min_samples
    )
    
    return lift_data


@router.get('/experiments/{experiment_id}/segments/insights', response_model=SegmentInsights)
async def get_segment_insights(
    experiment_id: str,
    db = Depends(get_database)
):
    """Get AI-generated insights about segments"""
    
    service = ContextualService(db.pool)
    
    insights = await service.get_segment_insights(experiment_id)
    
    return insights


@router.post('/analytics/refresh')
async def refresh_analytics(
    db = Depends(get_database)
):
    """Refresh segment analytics materialized view"""
    
    service = ContextualService(db.pool)
    
    await service.refresh_analytics()
    
    return {'message': 'Analytics refreshed successfully'}


@router.get('/experiments/{experiment_id}/segments/{segment_key}/variants')
async def get_segment_variant_performance(
    experiment_id: str,
    segment_key: str,
    db = Depends(get_database)
):
    """Get variant performance for specific segment"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                ev.id,
                ev.name,
                vsp.conversion_rate,
                vsp.samples,
                vsp.alpha,
                vsp.beta,
                vsp.credible_interval_lower,
                vsp.credible_interval_upper
            FROM variant_segment_performance vsp
            JOIN element_variants ev ON ev.id = vsp.variant_id
            JOIN context_segments cs ON cs.id = vsp.segment_id
            WHERE cs.experiment_id = $1
            AND cs.segment_key = $2
            ORDER BY vsp.conversion_rate DESC
        """, experiment_id, segment_key)
    
    if not rows:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return {
        'segment_key': segment_key,
        'variants': [
            {
                'id': str(row['id']),
                'name': row['name'],
                'conversion_rate': row['conversion_rate'],
                'samples': row['samples'],
                'confidence_interval': {
                    'lower': row['credible_interval_lower'],
                    'upper': row['credible_interval_upper']
                },
                'state': {
                    'alpha': row['alpha'],
                    'beta': row['beta']
                }
            }
            for row in rows
        ]
    }
