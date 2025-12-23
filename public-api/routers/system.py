# public-api/routers/system.py

"""
System Diagnostics API
Monitors platform health, resource utilization (Redis), and operational metrics.
"""

from fastapi import APIRouter, Depends
import logging

from public_api.dependencies import get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from orchestration.services.service_factory import ServiceFactory

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/metrics")
async def get_operational_metrics(user_id: str = Depends(get_current_user)):
    """Retrieves high-level platform health and throughput indicators"""
    try:
        metrics = await ServiceFactory.get_metrics()
        if not metrics:
            raise APIError("Operational data unavailable", code=ErrorCodes.INTERNAL_ERROR, status=503)
            
        return {
            "throughput": {
                "day": metrics['last_24h'],
                "hour": metrics['last_hour'],
                "projected": metrics['projected_daily']
            },
            "buffer_tier": {
                "active": metrics['redis_activated'],
                "usage_pct": metrics['threshold_percentage']
            },
            "status": "operational"
        }
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"System metrics check failed: {e}")
        raise APIError("Health check failed", code=ErrorCodes.INTERNAL_ERROR, status=503)
