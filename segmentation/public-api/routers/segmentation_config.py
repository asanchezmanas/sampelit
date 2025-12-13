# public-api/routers/segmentation_config.py

"""
Segmentation Configuration API

Endpoints para configurar y gestionar segmentación:
- Enable/disable segmentation
- Configure manual segments
- Enable auto-clustering
- View recommendations
- View segment performance
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
from orchestration.services.segmentation import (
    EligibilityService,
    SegmentationService,
    ClusteringService
)

router = APIRouter()

# ============================================
# MODELS
# ============================================

class SegmentationMode(str):
    DISABLED = "disabled"
    MANUAL = "manual"
    AUTO = "auto"

class UpdateSegmentationConfigRequest(BaseModel):
    """Update segmentation configuration"""
    mode: str = Field(..., regex="^(disabled|manual|auto)$")
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
    traffic_quality: str
    recommendations: List[Dict[str, Any]]

class SegmentPerformanceResponse(BaseModel):
    """Segment performance stats"""
    segment_key: str
    segment_type: str
    display_name: str
    allocations: int
    conversions: int
    conversion_rate: float
    characteristics: Dict[str, Any]

class ClusteringStatusResponse(BaseModel):
    """Clustering training status"""
    is_trained: bool
    n_clusters: Optional[int]
    algorithm: Optional[str]
    trained_at: Optional[datetime]
    silhouette_score: Optional[float]
    samples_trained_on: Optional[int]

# ============================================
# GET CONFIGURATION
# ============================================

@router.get("/{experiment_id}/config", response_model=SegmentationConfigResponse)
async def get_segmentation_config(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get current segmentation configuration"""
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Get config
        async with db.pool.acquire() as conn:
            config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                experiment_id
            )
        
        if not config:
            # Create default config
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO experiment_segmentation_config (experiment_id)
                    VALUES ($1)
                    """,
                    experiment_id
                )
                
                config = await conn.fetchrow(
                    "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                    experiment_id
                )
        
        return SegmentationConfigResponse(
            experiment_id=str(config['experiment_id']),
            mode=config['mode'],
            segment_by=config['segment_by'],
            min_samples_per_segment=config['min_samples_per_segment'],
            auto_clustering_enabled=config['auto_clustering_enabled'],
            n_clusters=config['n_clusters'],
            auto_activation_enabled=config['auto_activation_enabled'],
            auto_activation_threshold=config['auto_activation_threshold'],
            created_at=config['created_at'],
            updated_at=config['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )

# ============================================
# UPDATE CONFIGURATION
# ============================================

@router.put("/{experiment_id}/config")
async def update_segmentation_config(
    experiment_id: str,
    request: UpdateSegmentationConfigRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Update segmentation configuration
    
    Examples:
    - Enable manual segmentation by source
    - Enable auto-clustering
    - Enable auto-activation
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id, status FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Can't change config on active experiments (safety)
        if exp['status'] == 'active' and request.mode != 'disabled':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify segmentation on active experiment. Pause it first."
            )
        
        # Validate mode-specific requirements
        if request.mode == 'manual' and not request.segment_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="segment_by required for manual mode"
            )
        
        # Update config
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE experiment_segmentation_config
                SET 
                    mode = $2,
                    segment_by = $3,
                    min_samples_per_segment = $4,
                    auto_clustering_enabled = $5,
                    n_clusters = $6,
                    auto_activation_enabled = $7,
                    auto_activation_threshold = $8,
                    updated_at = NOW()
                WHERE experiment_id = $1
                """,
                experiment_id,
                request.mode,
                request.segment_by or [],
                request.min_samples_per_segment,
                request.mode == 'auto',
                request.n_clusters,
                request.auto_activation_enabled,
                request.auto_activation_threshold
            )
        
        # If enabling auto-clustering, train model
        if request.mode == 'auto':
            clustering_service = ClusteringService(db.pool)
            try:
                await clustering_service.train_clustering_model(
                    experiment_id,
                    n_clusters=request.n_clusters
                )
            except ValueError as e:
                # Not enough data yet
                pass
        
        return {
            "status": "success",
            "mode": request.mode,
            "message": f"Segmentation {request.mode} configured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )

# ============================================
# CHECK ELIGIBILITY
# ============================================

@router.get("/{experiment_id}/eligibility", response_model=EligibilityResponse)
async def check_eligibility(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Check if experiment is eligible for segmentation features
    
    Returns recommendations if eligible
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Check eligibility
        eligibility_service = EligibilityService(db.pool)
        result = await eligibility_service.check_experiment_eligibility(experiment_id)
        
        return EligibilityResponse(
            eligible_for_segmentation=result['eligible_for_segmentation'],
            eligible_for_clustering=result['eligible_for_clustering'],
            avg_daily_visitors=result['avg_daily_visitors'],
            traffic_quality=result['traffic_quality'],
            recommendations=result['recommendations']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check eligibility: {str(e)}"
        )

# ============================================
# VIEW SEGMENT PERFORMANCE
# ============================================

@router.get("/{experiment_id}/segments", response_model=List[SegmentPerformanceResponse])
async def get_segment_performance(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get performance breakdown by segment
    
    Shows how each segment is performing
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Get segment stats
        segmentation_service = SegmentationService(db.pool)
        segments = await segmentation_service.get_segment_stats(experiment_id)
        
        return [
            SegmentPerformanceResponse(
                segment_key=seg['segment_key'],
                segment_type=seg['segment_type'],
                display_name=seg['display_name'],
                allocations=seg['allocations'],
                conversions=seg['conversions'],
                conversion_rate=seg['conversion_rate'],
                characteristics=seg['characteristics']
            )
            for seg in segments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get segments: {str(e)}"
        )

# ============================================
# CLUSTERING OPERATIONS
# ============================================

@router.get("/{experiment_id}/clustering/status", response_model=ClusteringStatusResponse)
async def get_clustering_status(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get clustering model status"""
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Get active model
        async with db.pool.acquire() as conn:
            model = await conn.fetchrow(
                """
                SELECT * FROM clustering_models
                WHERE experiment_id = $1 AND is_active = true
                ORDER BY trained_at DESC
                LIMIT 1
                """,
                experiment_id
            )
        
        if not model:
            return ClusteringStatusResponse(
                is_trained=False,
                n_clusters=None,
                algorithm=None,
                trained_at=None,
                silhouette_score=None,
                samples_trained_on=None
            )
        
        # Get sample count
        async with db.pool.acquire() as conn:
            sample_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM assignments
                WHERE experiment_id = $1
                  AND assigned_at >= $2
                """,
                experiment_id,
                model['trained_at']
            )
        
        return ClusteringStatusResponse(
            is_trained=True,
            n_clusters=model['n_clusters'],
            algorithm=model['algorithm'],
            trained_at=model['trained_at'],
            silhouette_score=float(model['silhouette_score']) if model['silhouette_score'] else None,
            samples_trained_on=sample_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get clustering status: {str(e)}"
        )

@router.post("/{experiment_id}/clustering/train")
async def train_clustering_model(
    experiment_id: str,
    n_clusters: Optional[int] = Query(None, ge=2, le=10),
    force_retrain: bool = Query(False),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Train clustering model
    
    This can take a few seconds for large datasets
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Train model
        clustering_service = ClusteringService(db.pool)
        result = await clustering_service.train_clustering_model(
            experiment_id,
            n_clusters=n_clusters,
            force_retrain=force_retrain
        )
        
        return {
            "status": "success",
            "model_id": result['model_id'],
            "n_clusters": result['n_clusters'],
            "algorithm": result['algorithm'],
            "silhouette_score": result.get('performance', {}).get('silhouette_score'),
            "samples_trained_on": result.get('samples_trained_on'),
            "message": f"Clustering model trained with {result['n_clusters']} clusters"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train clustering model: {str(e)}"
        )

# ============================================
# RECOMMENDATIONS
# ============================================

@router.get("/{experiment_id}/recommendations")
async def get_recommendations(
    experiment_id: str,
    status_filter: str = Query("pending", regex="^(pending|accepted|dismissed)$"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get segmentation recommendations
    
    Shows proactive suggestions based on traffic patterns
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
        
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Get recommendations
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM segmentation_recommendations
                WHERE experiment_id = $1 AND status = $2
                ORDER BY created_at DESC
                """,
                experiment_id, status_filter
            )
        
        return {
            "recommendations": [dict(row) for row in rows],
            "count": len(rows)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@router.post("/{experiment_id}/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    experiment_id: str,
    recommendation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Accept and apply recommendation
    
    Automatically configures segmentation based on recommendation
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id, user_id
            )
            
            if not exp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found"
                )
            
            # Get recommendation
            recommendation = await conn.fetchrow(
                """
                SELECT * FROM segmentation_recommendations
                WHERE id = $1 AND experiment_id = $2
                """,
                recommendation_id, experiment_id
            )
            
            if not recommendation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recommendation not found"
                )
            
            # Apply suggested config
            suggested_config = recommendation['suggested_config']
            
            if recommendation['recommendation_type'] == 'enable_segmentation':
                await conn.execute(
                    """
                    UPDATE experiment_segmentation_config
                    SET 
                        mode = $2,
                        segment_by = $3,
                        updated_at = NOW()
                    WHERE experiment_id = $1
                    """,
                    experiment_id,
                    suggested_config.get('mode', 'manual'),
                    suggested_config.get('segment_by', [])
                )
            
            elif recommendation['recommendation_type'] == 'enable_clustering':
                await conn.execute(
                    """
                    UPDATE experiment_segmentation_config
                    SET 
                        mode = 'auto',
                        auto_clustering_enabled = true,
                        updated_at = NOW()
                    WHERE experiment_id = $1
                    """,
                    experiment_id
                )
            
            # Mark recommendation as accepted
            await conn.execute(
                """
                UPDATE segmentation_recommendations
                SET status = 'accepted', updated_at = NOW()
                WHERE id = $1
                """,
                recommendation_id
            )
        
        return {
            "status": "success",
            "message": "Recommendation accepted and applied"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept recommendation: {str(e)}"
        )

@router.post("/{experiment_id}/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    experiment_id: str,
    recommendation_id: str,
    reason: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Dismiss recommendation"""
    
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE segmentation_recommendations
                SET 
                    status = 'dismissed',
                    dismissed_reason = $3,
                    updated_at = NOW()
                WHERE id = $1 AND experiment_id = $2
                """,
                recommendation_id, experiment_id, reason
            )
        
        return {"status": "success", "message": "Recommendation dismissed"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss recommendation: {str(e)}"
        )
