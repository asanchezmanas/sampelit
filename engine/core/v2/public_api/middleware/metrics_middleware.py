# public_api/middleware/metrics_middleware.py

"""
FastAPI middleware for automatic metrics collection
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

from infrastructure.monitoring.prometheus_metrics import get_metrics_collector


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP metrics
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = get_metrics_collector()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics"""
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        self.metrics.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration_seconds=duration
        )
        
        return response
