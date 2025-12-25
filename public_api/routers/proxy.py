# public-api/routers/proxy.py

"""
Proxy Edge Middleware
Intercepts traffic from the customer's server to inject the tracking snippet dynamically.
This endpoint is public and accessed by end-users of the customer's site.
"""

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import Response
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db
from public_api.middleware.error_handler import APIError, ErrorCodes
from integration.proxy.proxy_middleware import ProxyMiddleware
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global middleware instance for connection pooling reuse
edge_middleware = ProxyMiddleware(api_url=settings.BASE_URL)

@router.get("/{installation_token}/{path:path}")
async def edge_proxy(
    installation_token: str,
    path: str,
    request: Request,
    db: DatabaseManager = Depends(get_db)
):
    """Injects the Samplit runtime into the proxied HTML stream"""
    try:
        async with db.pool.acquire() as conn:
            inst = await conn.fetchrow(
                "SELECT site_url, status FROM platform_installations WHERE installation_token = $1",
                installation_token
            )
        
        if not inst:
            raise APIError("Secure tunnel endpoint not found", code=ErrorCodes.NOT_FOUND, status=404)
        
        if inst['status'] != 'active':
            raise APIError(f"Secure tunnel is {inst['status']}", code=ErrorCodes.FORBIDDEN, status=403)
        
        # Reconstruct the origin target URL
        origin_target = f"https://{inst['site_url']}/{path}"
        if request.url.query:
            origin_target += f"?{request.url.query}"
            
        return await edge_middleware.process_request(
            request=request,
            installation_token=installation_token,
            original_url=origin_target
        )
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Edge proxy interception failure: {e}")
        raise APIError("Interception service unavailable", code=ErrorCodes.INTERNAL_ERROR, status=503)


@router.get("/{installation_token}")
async def edge_proxy_root(installation_token: str, request: Request, db: DatabaseManager = Depends(get_db)):
    """Handles root-level edge proxying"""
    return await edge_proxy(installation_token, "", request, db)
