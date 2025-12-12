# public-api/routers/integrations.py

"""
Integrations API

Endpoints para conectar WordPress, Shopify y otras plataformas.
✅ Simple OAuth flow - el usuario solo hace click
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import secrets

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
from integration.web.wordpress.oauth import WordPressIntegration, generate_state_token
from integration.web.shopify.oauth import ShopifyIntegration, extract_shop_domain

router = APIRouter()

# ============================================
# MODELS
# ============================================

class IntegrationPlatform(str):
    """Plataformas soportadas"""
    WORDPRESS = "wordpress"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"  # WordPress + WooCommerce

class StartIntegrationRequest(BaseModel):
    """Iniciar integración"""
    platform: str
    shop_domain: Optional[str] = None  # Para Shopify
    return_url: Optional[str] = None  # URL de retorno después del OAuth

class IntegrationResponse(BaseModel):
    """Respuesta de integración"""
    id: str
    platform: str
    status: str
    site_name: Optional[str]
    site_url: Optional[str]
    connected_at: Optional[datetime]
    last_sync: Optional[datetime]

# ============================================
# LISTAR INTEGRACIONES
# ============================================

@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Listar todas las integraciones del usuario
    """
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id, platform, status, site_name, site_url,
                    verified_at as connected_at, last_activity as last_sync
                FROM platform_installations
                WHERE user_id = $1 
                  AND installation_method IN ('wordpress_plugin', 'shopify_app')
                  AND status != 'archived'
                ORDER BY created_at DESC
                """,
                user_id
            )
        
        return [
            IntegrationResponse(
                id=str(row['id']),
                platform=row['platform'],
                status=row['status'],
                site_name=row['site_name'],
                site_url=row['site_url'],
                connected_at=row['connected_at'],
                last_sync=row['last_sync']
            )
            for row in rows
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list integrations: {str(e)}"
        )

# ============================================
# INICIAR INTEGRACIÓN (STEP 1: Redirect a OAuth)
# ============================================

@router.post("/connect/{platform}")
async def start_integration(
    platform: str,
    shop_domain: Optional[str] = Query(None, description="Required for Shopify"),
    return_url: Optional[str] = Query(None, description="URL to return after OAuth"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database),
    request: Request = None
):
    """
    Iniciar integración - Redirect a OAuth
    
    Flow:
    1. User clicks "Connect WordPress" o "Connect Shopify"
    2. Este endpoint redirige a OAuth
    3. OAuth callback regresa a /integrations/callback
    4. ✅ Listo! Integración conectada
    """
    
    if platform not in [IntegrationPlatform.WORDPRESS, IntegrationPlatform.SHOPIFY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {platform}"
        )
    
    try:
        # Generate state token (CSRF protection)
        state_token = generate_state_token()
        
        # Save state in session/DB (simplificado: usamos una tabla temporal)
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO oauth_states (user_id, state_token, platform, shop_domain, return_url)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, state_token, platform, shop_domain, return_url
            )
        
        # OAuth redirect URI (nuestro callback)
        base_url = request.base_url
        redirect_uri = f"{base_url}api/v1/integrations/callback/{platform}"
        
        # Generate OAuth URL según plataforma
        if platform == IntegrationPlatform.WORDPRESS:
            # WordPress OAuth
            integration = WordPressIntegration(
                installation_id="temp",
                config={}
            )
            oauth_url = await integration.get_oauth_url(redirect_uri, state_token)
        
        elif platform == IntegrationPlatform.SHOPIFY:
            # Shopify OAuth
            if not shop_domain:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="shop_domain is required for Shopify"
                )
            
            shop_domain = extract_shop_domain(shop_domain)
            
            integration = ShopifyIntegration(
                installation_id="temp",
                config={'shop_domain': shop_domain}
            )
            oauth_url = await integration.get_oauth_url(redirect_uri, state_token)
        
        # ✅ Redirect al OAuth
        return RedirectResponse(url=oauth_url, status_code=302)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start integration: {str(e)}"
        )

# ============================================
# OAUTH CALLBACK (STEP 2: Recibir token)
# ============================================

@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="State token for CSRF protection"),
    shop: Optional[str] = Query(None, description="Shopify shop domain"),
    db: DatabaseManager = Depends(get_database),
    request: Request = None
):
    """
    OAuth Callback - Step 2
    
    Este endpoint recibe el código de OAuth y lo intercambia por access token.
    """
    
    try:
        # Verificar state token
        async with db.pool.acquire() as conn:
            state_data = await conn.fetchrow(
                """
                SELECT user_id, shop_domain, return_url
                FROM oauth_states
                WHERE state_token = $1 AND platform = $2
                  AND created_at > NOW() - INTERVAL '10 minutes'
                """,
                state, platform
            )
            
            if not state_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired state token"
                )
            
            user_id = str(state_data['user_id'])
            return_url = state_data['return_url'] or "/"
            
            # Delete used state
            await conn.execute(
                "DELETE FROM oauth_states WHERE state_token = $1",
                state
            )
        
        # OAuth redirect URI
        base_url = request.base_url
        redirect_uri = f"{base_url}api/v1/integrations/callback/{platform}"
        
        # Exchange code for token
        if platform == IntegrationPlatform.WORDPRESS:
            integration = WordPressIntegration(
                installation_id="temp",
                config={}
            )
            token_data = await integration.exchange_code_for_token(code, redirect_uri)
            
            site_url = token_data['shop_info']['url']
            site_name = token_data['shop_info']['name']
            blog_id = token_data['shop_info']['blog_id']
            
            # Create installation
            async with db.pool.acquire() as conn:
                installation_id = await conn.fetchval(
                    """
                    INSERT INTO platform_installations (
                        user_id, platform, installation_method,
                        site_url, site_name,
                        installation_token, api_token,
                        status, verified_at,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), $9)
                    RETURNING id
                    """,
                    user_id,
                    'wordpress',
                    'wordpress_plugin',
                    site_url,
                    site_name,
                    f"wp_{secrets.token_urlsafe(16)}",
                    token_data['access_token'],
                    'active',
                    {
                        'blog_id': blog_id,
                        'scope': token_data['scope']
                    }
                )
        
        elif platform == IntegrationPlatform.SHOPIFY:
            shop_domain = shop or state_data['shop_domain']
            if not shop_domain:
                raise HTTPException(400, "Shop domain missing")
            
            integration = ShopifyIntegration(
                installation_id="temp",
                config={'shop_domain': shop_domain}
            )
            token_data = await integration.exchange_code_for_token(code, redirect_uri)
            
            site_url = token_data['shop_info']['domain']
            site_name = token_data['shop_info']['name']
            
            # Create installation
            async with db.pool.acquire() as conn:
                installation_id = await conn.fetchval(
                    """
                    INSERT INTO platform_installations (
                        user_id, platform, installation_method,
                        site_url, site_name,
                        installation_token, api_token,
                        status, verified_at,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), $9)
                    RETURNING id
                    """,
                    user_id,
                    'shopify',
                    'shopify_app',
                    site_url,
                    site_name,
                    f"shop_{secrets.token_urlsafe(16)}",
                    token_data['access_token'],
                    'active',
                    {
                        'shop_domain': shop_domain,
                        'shop_id': token_data['shop_info']['shop_id'],
                        'currency': token_data['shop_info']['currency'],
                        'plan': token_data['shop_info']['plan_name']
                    }
                )
                
                # ✅ Registrar webhooks automáticamente
                integration_instance = ShopifyIntegration(
                    installation_id=str(installation_id),
                    config={
                        'shop_domain': shop_domain,
                        'access_token': token_data['access_token']
                    }
                )
                
                webhook_url = f"{base_url}api/v1/webhooks"
                webhook_ids = await integration_instance.register_webhooks(webhook_url)
                
                # Guardar webhook IDs
                await conn.execute(
                    """
                    UPDATE platform_installations
                    SET metadata = metadata || $1::jsonb
                    WHERE id = $2
                    """,
                    {'webhook_ids': webhook_ids},
                    installation_id
                )
        
        # ✅ Redirect de vuelta a la app con éxito
        success_url = f"{return_url}?integration=success&platform={platform}&id={installation_id}"
        return RedirectResponse(url=success_url, status_code=302)
    
    except HTTPException:
        raise
    except Exception as e:
        # Redirect con error
        error_url = f"{return_url}?integration=error&message={str(e)}"
        return RedirectResponse(url=error_url, status_code=302)

# ============================================
# DESCONECTAR INTEGRACIÓN
# ============================================

@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Desconectar integración
    """
    try:
        async with db.pool.acquire() as conn:
            # Verify ownership
            installation = await conn.fetchrow(
                """
                SELECT platform, api_token, metadata
                FROM platform_installations
                WHERE id = $1 AND user_id = $2
                """,
                integration_id, user_id
            )
            
            if not installation:
                raise HTTPException(404, "Integration not found")
            
            # TODO: Cleanup resources (webhooks, script tags, etc)
            # según la plataforma
            
            # Mark as archived
            await conn.execute(
                """
                UPDATE platform_installations
                SET status = 'archived', updated_at = NOW()
                WHERE id = $1
                """,
                integration_id
            )
        
        return {"status": "disconnected", "integration_id": integration_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect: {str(e)}"
        )

# ============================================
# TEST CONNECTION
# ============================================

@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Probar que la integración sigue funcionando
    """
    try:
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT platform, api_token, site_url, metadata
                FROM platform_installations
                WHERE id = $1 AND user_id = $2
                """,
                integration_id, user_id
            )
            
            if not installation:
                raise HTTPException(404, "Integration not found")
            
            # Create integration instance
            platform = installation['platform']
            
            if platform == 'wordpress':
                integration = WordPressIntegration(
                    installation_id=integration_id,
                    config={
                        'access_token': installation['api_token'],
                        'blog_id': installation['metadata'].get('blog_id')
                    }
                )
            elif platform == 'shopify':
                integration = ShopifyIntegration(
                    installation_id=integration_id,
                    config={
                        'shop_domain': installation['metadata'].get('shop_domain'),
                        'access_token': installation['api_token']
                    }
                )
            else:
                raise HTTPException(400, f"Unsupported platform: {platform}")
            
            # Test connection
            is_connected = await integration.check_connection()
            
            if is_connected:
                # Update last activity
                await conn.execute(
                    """
                    UPDATE platform_installations
                    SET last_activity = NOW()
                    WHERE id = $1
                    """,
                    integration_id
                )
            
            return {
                "connected": is_connected,
                "integration_id": integration_id,
                "platform": platform,
                "tested_at": datetime.utcnow().isoformat()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )

# ============================================
# SYNC STATUS
# ============================================

@router.get("/{integration_id}/status")
async def get_integration_status(
    integration_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Obtener estado completo de la integración
    """
    try:
        async with db.pool.acquire() as conn:
            installation = await conn.fetchrow(
                """
                SELECT 
                    platform, status, site_name, site_url,
                    verified_at, last_activity,
                    metadata
                FROM platform_installations
                WHERE id = $1 AND user_id = $2
                """,
                integration_id, user_id
            )
            
            if not installation:
                raise HTTPException(404, "Integration not found")
            
            # Count synced experiments
            experiment_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM experiments
                WHERE user_id = $1 
                  AND url LIKE $2
                  AND status = 'active'
                """,
                user_id,
                f"%{installation['site_url']}%"
            )
        
        return {
            "integration_id": integration_id,
            "platform": installation['platform'],
            "status": installation['status'],
            "site_name": installation['site_name'],
            "site_url": installation['site_url'],
            "connected_at": installation['verified_at'],
            "last_sync": installation['last_activity'],
            "active_experiments": experiment_count or 0,
            "metadata": installation['metadata']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )
