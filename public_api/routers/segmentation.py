"""
Segmentation Configuration API
Endpoints for managing segmentation settings, auto-clustering, and recommendations.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from public_api.routers.auth import get_current_user
from data_access.database import DatabaseManager, get_db
from orchestration.services.segmentation.eligibility_service import EligibilityService
from orchestration.services.segmentation.segmentation_service import SegmentationService
from orchestration.services.segmentation.clustering_service import ClusteringService

router = APIRouter()

# ============================================
# MODELS
# ============================================

class UpdateSegmentationConfigRequest(BaseModel):
    """Update segmentation configuration"""
    mode: str = Field(..., pattern="^(disabled|manual|auto)$")
    segment_by: Optional[List[str]] = Field(None, description="Fields to segment by (manual mode)")
    min_samples_per_segment: Optional[int] = Field(100, ge=50, le=1000)
    n_clusters: Optional[int] = Field(None, ge=2, le=10, description="Number of clusters (auto mode)")
    auto_activation_enabled: Optional[bool] = Field(False)
    auto_activation_threshold: Optional[int] = Field(1000, ge=100)

class SegmentationConfigResponse(BaseModel):
    """Current segmentation configuration"""
    experiment_id: str
    mode: str
    segment_by: Optional[List[str]]
    min_samples_per_segment: int
    auto_clustering_enabled: bool
    n_clusters: Optional[int]
    auto_activation_enabled: bool
    auto_activation_threshold: int
    created_at: datetime
    updated_at: datetime

class EligibilityResponse(BaseModel):
    """Eligibility check response"""
    eligible_for_segmentation: bool
    eligible_for_clustering: bool
    avg_daily_visitors: float
    recommendations: List[Dict[str, Any]]

class SegmentPerformanceResponse(BaseModel):
    """Segment performance stats"""
    segment_key: str
    allocations: int
    conversions: int
    conversion_rate: float
    updated_at: datetime

# ============================================
# ENDPOINTS
# ============================================

@router.get("/{experiment_id}/config", response_model=SegmentationConfigResponse)
async def get_segmentation_config(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get current segmentation configuration"""
    async with db.pool.acquire() as conn:
        config = await conn.fetchrow(
            "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
            UUID(experiment_id)
        )
        
        if not config:
            # Create default config if not exists
            await conn.execute(
                "INSERT INTO experiment_segmentation_config (experiment_id) VALUES ($1) ON CONFLICT DO NOTHING",
                UUID(experiment_id)
            )
            config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                UUID(experiment_id)
            )
            
    return SegmentationConfigResponse(**dict(config))

@router.put("/{experiment_id}/config")
async def update_segmentation_config(
    experiment_id: str,
    request: UpdateSegmentationConfigRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Update segmentation configuration"""
    # Logic to update config and potentially trigger initial clustering training
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE experiment_segmentation_config
            SET mode = $2, segment_by = $3, min_samples_per_segment = $4,
                auto_clustering_enabled = $5, n_clusters = $6,
                auto_activation_enabled = $7, auto_activation_threshold = $8,
                updated_at = NOW()
            WHERE experiment_id = $1
            """,
            UUID(experiment_id), request.mode, request.segment_by, request.min_samples_per_segment,
            request.mode == 'auto', request.n_clusters, request.auto_activation_enabled,
            request.auto_activation_threshold
        )
    return {"status": "success", "message": "Config updated"}

@router.get("/{experiment_id}/eligibility", response_model=EligibilityResponse)
async def check_eligibility(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Check if experiment is eligible for segmentation"""
    service = EligibilityService(db.pool)
    result = await service.analyze_eligibility(UUID(experiment_id))
    return EligibilityResponse(
        eligible_for_segmentation=result['status'] != 'ineligible',
        eligible_for_clustering=result['status'] == 'eligible_auto',
        avg_daily_visitors=result['daily_avg'],
        recommendations=[{"type": result['status'], "text": result['recommendation']}]
    )

@router.get("/{experiment_id}/segments", response_model=List[SegmentPerformanceResponse])
async def get_segments(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get breakdown by segment"""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM segments WHERE experiment_id = $1",
            UUID(experiment_id)
        )
    return [SegmentPerformanceResponse(
        segment_key=row['segment_key'],
        allocations=row['total_visitors'],
        conversions=row['total_conversions'],
        conversion_rate=float(row['conversion_rate']),
        updated_at=row['updated_at']
    ) for row in rows]
