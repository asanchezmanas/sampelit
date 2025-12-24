# public_api/routers/metrics.py

"""
Metrics endpoint for Prometheus scraping
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from infrastructure.monitoring.prometheus_metrics import get_metrics_collector

router = APIRouter()


@router.get('/metrics')
async def metrics():
    """
    Prometheus metrics endpoint
    
    This endpoint is scraped by Prometheus every 15 seconds
    """
    collector = get_metrics_collector()
    
    return Response(
        content=collector.export_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
