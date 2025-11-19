# public-api/routers/experiments.py

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from orchestration.services.experiment_service import ExperimentService
from data_access.database import get_database, DatabaseManager
from public_api.routers.auth import get_current_user

router = APIRouter()

# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class VariantRequest(BaseModel):
    """Variant creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Dict[str, Any] = Field(default_factory=dict)

class CreateExperimentRequest(BaseModel):
    """Create experiment request"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    variants: List[VariantRequest] = Field(..., min_items=2)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target_url: Optional[str] = None

class ExperimentResponse(BaseModel):
    """Experiment list response"""
    id: str
    name: str
    description: Optional[str]
    status: str
    optimization_strategy: str
    created_at: datetime
    started_at: Optional[datetime]
    variant_count: int
    total_users: int
    conversion_rate: float

class VariantResponse(BaseModel):
    """Variant response"""
    id: str
    name: str
    description: Optional[str]
    content: Dict[str, Any]
    total_allocations: int
    total_conversions: int
    observed_conversion_rate: float
    is_active: bool

class ExperimentDetailResponse(BaseModel):
    """Detailed experiment response"""
    id: str
    name: str
    description: Optional[str]
    status: str
    optimization_strategy: str
    config: Dict[str, Any]
    target_url: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    variants: List[VariantResponse]

class AssignmentResponse(BaseModel):
    """Assignment response"""
    variant_id: str
    content: Dict[str, Any]
    assignment_id: str
    new_assignment: bool

class ConversionRequest(BaseModel):
    """Conversion recording request"""
    user_identifier: str = Field(..., min_length=1, max_length=255)
    value: float = Field(default=1.0, ge=0)

# ============================================
# ENDPOINTS
# ============================================

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Create new experiment
    
    Creates an experiment with multiple variants and initializes
    the optimization algorithm (Thompson Sampling by default).
    """
    
    try:
        service = ExperimentService(db)
        
        # Convert variants to dict format
        variants_data = [
            {
                'name': v.name,
                'description': v.description,
                'content': v.content
            }
            for v in request.variants
        ]
        
        result = await service.create_experiment(
            user_id=user_id,
            name=request.name,
            description=request.description,
            variants_data=variants_data,
            config=request.config or {}
        )
        
        return {
            "experiment_id": result['experiment_id'],
            "variant_ids": result['variant_ids'],
            "message": "Experiment created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}"
        )

@router.get("/", response_model=List[ExperimentResponse])
async def list_experiments(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    List all experiments for current user
    
    Returns summary of all experiments with basic metrics.
    """
    
    try:
        from data_access.repositories.experiment_repository import ExperimentRepository
        
        repo = ExperimentRepository(db.pool)
        experiments = await repo.find_by_user(user_id)
        
        # Filter by status if requested
        if status_filter:
            experiments = [
                exp for exp in experiments 
                if exp['status'] == status_filter
            ]
        
        return [
            ExperimentResponse(
                id=str(exp['id']),
                name=exp['name'],
                description=exp.get('description'),
                status=exp['status'],
                optimization_strategy=exp.get('optimization_strategy', 'adaptive'),
                created_at=exp['created_at'],
                started_at=exp.get('started_at'),
                variant_count=exp.get('variant_count', 0),
                total_users=exp.get('total_users', 0),
                conversion_rate=float(exp.get('conversion_rate', 0))
            )
            for exp in experiments
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list experiments: {str(e)}"
        )

@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get experiment details
    
    Returns full experiment data including all variants and configuration.
    """
    
    try:
        from data_access.repositories.experiment_repository import ExperimentRepository
        from data_access.repositories.variant_repository import VariantRepository
        
        exp_repo = ExperimentRepository(db.pool)
        var_repo = VariantRepository(db.pool)
        
        # Get experiment
        experiment = await exp_repo.find_by_id(experiment_id)
        
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Verify ownership
        if str(experiment['user_id']) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get variants (public data only)
        async with db.pool.acquire() as conn:
            variant_rows = await conn.fetch(
                """
                SELECT 
                    id, name, description, content, is_active,
                    total_allocations, total_conversions,
                    observed_conversion_rate
                FROM variants
                WHERE experiment_id = $1 AND is_active = true
                ORDER BY created_at
                """,
                experiment_id
            )
        
        variants = [
            VariantResponse(
                id=str(row['id']),
                name=row['name'],
                description=row['description'],
                content=row['content'],
                total_allocations=row['total_allocations'],
                total_conversions=row['total_conversions'],
                observed_conversion_rate=float(row['observed_conversion_rate']),
                is_active=row['is_active']
            )
            for row in variant_rows
        ]
        
        return ExperimentDetailResponse(
            id=str(experiment['id']),
            name=experiment['name'],
            description=experiment.get('description'),
            status=experiment['status'],
            optimization_strategy=experiment.get('optimization_strategy', 'adaptive'),
            config=experiment.get('config', {}),
            target_url=experiment.get('target_url'),
            created_at=experiment['created_at'],
            started_at=experiment.get('started_at'),
            variants=variants
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment: {str(e)}"
        )

@router.patch("/{experiment_id}/status")
async def update_experiment_status(
    experiment_id: str,
    new_status: str = Query(..., regex="^(draft|active|paused|completed)$"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Update experiment status
    
    Allowed transitions:
    - draft -> active
    - active -> paused
    - paused -> active
    - active -> completed
    """
    
    try:
        from data_access.repositories.experiment_repository import ExperimentRepository
        
        repo = ExperimentRepository(db.pool)
        
        # Update status
        success = await repo.update_status(experiment_id, new_status, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or access denied"
            )
        
        return {
            "experiment_id": experiment_id,
            "status": new_status,
            "message": f"Experiment status updated to {new_status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )

@router.get("/{experiment_id}/assign", response_model=AssignmentResponse)
async def assign_user_to_variant(
    experiment_id: str,
    user_identifier: str = Query(..., description="Unique user identifier"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    db: DatabaseManager = Depends(get_database)
):
    """
    Assign user to variant
    
    This is the main allocation endpoint. Uses Thompson Sampling (adaptive strategy)
    to intelligently allocate traffic to variants.
    
    PUBLIC ENDPOINT - No auth required for visitor allocation.
    """
    
    try:
        service = ExperimentService(db)
        
        # Prepare context
        context = {}
        if session_id:
            context['session_id'] = session_id
        
        # Allocate user
        result = await service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=user_identifier,
            context=context
        )
        
        return AssignmentResponse(
            variant_id=result['variant_id'],
            content=result['variant']['content'],
            assignment_id=result.get('assignment_id', ''),
            new_assignment=result.get('new_assignment', False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assignment failed: {str(e)}"
        )

@router.post("/{experiment_id}/convert")
async def record_conversion(
    experiment_id: str,
    request: ConversionRequest,
    db: DatabaseManager = Depends(get_database)
):
    """
    Record conversion
    
    Updates the optimization algorithm with conversion data.
    This is how the system learns which variants perform better.
    
    PUBLIC ENDPOINT - No auth required.
    """
    
    try:
        service = ExperimentService(db)
        
        await service.record_conversion(
            experiment_id=experiment_id,
            user_identifier=request.user_identifier,
            value=request.value
        )
        
        return {
            "status": "success",
            "message": "Conversion recorded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record conversion: {str(e)}"
        )

@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Delete experiment (soft delete - archives it)
    
    This doesn't actually delete data, just marks as archived.
    """
    
    try:
        from data_access.repositories.experiment_repository import ExperimentRepository
        
        repo = ExperimentRepository(db.pool)
        success = await repo.delete(experiment_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or access denied"
            )
        
        return {
            "status": "success",
            "message": "Experiment archived"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete experiment: {str(e)}"
        )
