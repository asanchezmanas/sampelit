# public-api/routers/system.py
"""
System metrics endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from orchestration.services.service_factory import ServiceFactory
from public_api.routers.auth import get_current_user

router = APIRouter()


@router.get("/metrics")
async def get_system_metrics(
    user_id: str = Depends(get_current_user)
):
    """
    Get system metrics
    
    Shows:
    - Current request volume
    - Redis status
    - Threshold progress
    """
    
    metrics = await ServiceFactory.get_metrics()
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics service not available"
        )
    
    return {
        "requests": {
            "last_24h": metrics['last_24h'],
            "last_hour": metrics['last_hour'],
            "projected_daily": metrics['projected_daily']
        },
        "threshold": {
            "value": metrics['threshold'],
            "percentage": metrics['threshold_percentage'],
            "reached": metrics['redis_recommended']
        },
        "redis": {
            "recommended": metrics['redis_recommended'],
            "activated": metrics['redis_activated']
        }
    }
