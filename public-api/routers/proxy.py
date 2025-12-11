# public-api/routers/proxy.py

"""
Proxy Middleware Endpoints

Intercepta requests del sitio del usuario e inyecta el tracker automáticamente.
PÚBLICO - No requiere auth (es el sitio del usuario quien hace las requests).

"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import Response
import logging

from integration.proxy.proxy_middleware import ProxyMiddleware
from config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

proxy_middleware = ProxyMiddleware(api_url=settings.BASE_URL)

# ============================================
# PROXY REQUESTS
# ============================================

@router.get("/{installation_token}/{path:path}")
async def proxy_request(
    installation_token: str,
    path: str,
    request: Request
):
    """
    Endpoint de proxy - recibe requests del sitio del usuario
    
    El servidor del usuario está configurado para hacer proxy a través de aquí.
    Nosotros interceptamos el HTML e inyectamos el tracker automáticamente.
    
    Flow:
    1. Nginx/Apache del usuario → aquí
    2. Nosotros → sitio original del usuario
    3. Interceptamos HTML
    4. Inyectamos tracker
    5. Retornamos HTML modificado
    """
    try:
        # Verificar que la instalación existe y está activa
        db = request.app.state.db
        
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT id, site_url, status
                FROM platform_installations
                WHERE installation_token = $1
                """,
                installation_token
            )
        
        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Installation not found"
            )
        
        if installation['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Installation is {installation['status']}"
            )
        
        # Construir URL original
        original_url = f"https://{installation['site_url']}/{path}"
        if request.url.query:
            original_url += f"?{request.url.query}"
        
        logger.info(f"Proxying request: {original_url}")
        
        # Procesar a través del middleware
        response = await proxy_middleware.process_request(
            request=request,
            installation_token=installation_token,
            original_url=original_url
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proxy request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Proxy error"
        )


@router.get("/{installation_token}")
async def proxy_root(
    installation_token: str,
    request: Request
):
    """
    Proxy para la raíz del sitio
    
    Simplemente delega a proxy_request con path vacío.
    """
    return await proxy_request(installation_token, "", request)
