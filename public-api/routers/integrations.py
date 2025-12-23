# public-api/routers/integrations.py

"""
External Platform Integrations API - VERSIÓN PREMIUM
Supports automated OAuth-based connections for WordPress, Shopify, and WooCommerce.
Ensures secure handshakes and transparent synchronization status.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
import secrets
import logging
from typing import List, Optional, Dict, Any

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse
from public_api.models.integration_models import IntegrationSummary
from integration.web.wordpress.oauth import WordPressIntegration, generate_state_token
from integration.web.shopify.oauth import ShopifyIntegration, extract_shop_domain

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=List[IntegrationSummary])
async def list_integrations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Lists all automated integrations currently active in the user account.
    
    Returns connection status and synchronization metadata for verified platforms.
    """
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, platform, status, site_name, site_url, verified_at, last_activity
                FROM platform_installations
                WHERE user_id = $1 AND installation_method IN ('wordpress_plugin', 'shopify_app') AND status != 'archived'
                ORDER BY created_at DESC
                """,
                user_id
            )
            
        return [
            IntegrationSummary(
                id=str(row['id']),
                platform=row['platform'],
                status=row['status'],
                site_name=row['site_name'],
                site_url=row['site_url'],
                connected_at=row['verified_at'],
                last_sync=row['last_activity']
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to list integrations for {user_id}: {e}")
        raise APIError("Operation failed while retrieving integrations", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/connect/{platform}")
async def initiate_oauth(
    platform: str,
    request: Request,
    shop_domain: Optional[str] = Query(None),
    return_url: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Starts the OAuth handshake with the specified external platform.
    
    Generates a secure state token and redirects the user to the platform's authorization portal.
    """
    if platform not in ['wordpress', 'shopify']:
        raise APIError(f"Unsupported integration platform: {platform}", code=ErrorCodes.INVALID_INPUT, status=400)
    
    try:
        state = generate_state_token()
        async with db.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO oauth_states (user_id, state_token, platform, shop_domain, return_url) VALUES ($1, $2, $3, $4, $5)",
                user_id, state, platform, shop_domain, return_url
            )
            
        base_url = str(request.base_url).rstrip('/')
        callback_url = f"{base_url}/api/v1/integrations/callback/{platform}"
        
        if platform == 'wordpress':
            wp = WordPressIntegration(installation_id="pending", config={})
            url = await wp.get_oauth_url(callback_url, state)
        elif platform == 'shopify':
            if not shop_domain:
                raise APIError("Shop domain is required for Shopify authorization", code=ErrorCodes.INVALID_INPUT, status=400)
            shop = extract_shop_domain(shop_domain)
            sh = ShopifyIntegration(installation_id="pending", config={'shop_domain': shop})
            url = await sh.get_oauth_url(callback_url, state)
            
        return RedirectResponse(url=url)
        
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"OAuth initiation failed for {user_id} on {platform}: {e}")
        raise APIError("External authorization service is temporarily unreachable", code=ErrorCodes.INTERNAL_ERROR, status=503)


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    shop: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db)
):
    """
    Handles the return redirect from OAuth providers and finalizes the connection.
    
    Verifies the state token, exchanges the authorization code for an API token, and persists the installation.
    """
    try:
        async with db.pool.acquire() as conn:
            st = await conn.fetchrow(
                "SELECT user_id, shop_domain, return_url FROM oauth_states WHERE state_token = $1 AND platform = $2 AND created_at > NOW() - INTERVAL '10 minutes'", 
                state, platform
            )
            if not st:
                raise APIError("Authorization session expired or security token invalid", code=ErrorCodes.INVALID_TOKEN, status=400)
            
            user_id = st['user_id']
            ret_url = st['return_url'] or "/"
            await conn.execute("DELETE FROM oauth_states WHERE state_token = $1", state)
            
        base_url = str(request.base_url).rstrip('/')
        callback_url = f"{base_url}/api/v1/integrations/callback/{platform}"
        
        if platform == 'wordpress':
            wp = WordPressIntegration(installation_id="pending", config={})
            data = await wp.exchange_code_for_token(code, callback_url)
            
            async with db.pool.acquire() as conn:
                inst_id = await conn.fetchval(
                    """
                    INSERT INTO platform_installations (user_id, platform, installation_method, site_url, site_name, installation_token, api_token, status, verified_at, metadata)
                    VALUES ($1, 'wordpress', 'wordpress_plugin', $2, $3, $4, $5, 'active', NOW(), $6) RETURNING id
                    """,
                    user_id, data['shop_info']['url'], data['shop_info']['name'], f"wp_{secrets.token_urlsafe(16)}", data['access_token'], {'blog_id': data['shop_info']['blog_id']}
                )
                
        elif platform == 'shopify':
            shop_domain = shop or st['shop_domain']
            sh = ShopifyIntegration(installation_id="pending", config={'shop_domain': shop_domain})
            data = await sh.exchange_code_for_token(code, callback_url)
            
            async with db.pool.acquire() as conn:
                inst_id = await conn.fetchval(
                    """
                    INSERT INTO platform_installations (user_id, platform, installation_method, site_url, site_name, installation_token, api_token, status, verified_at, metadata)
                    VALUES ($1, 'shopify', 'shopify_app', $2, $3, $4, $5, 'active', NOW(), $6) RETURNING id
                    """,
                    user_id, data['shop_info']['domain'], data['shop_info']['name'], f"shop_{secrets.token_urlsafe(16)}", data['access_token'], {
                        'shop_domain': shop_domain, 'shop_id': data['shop_info']['shop_id'], 'currency': data['shop_info']['currency']
                    }
                )
                
        success_url = f"{ret_url}?integration=success&platform={platform}&id={inst_id}"
        return RedirectResponse(url=success_url)
        
    except Exception as e:
        logger.error(f"Integrations callback failure: {e}", exc_info=True)
        # We redirect with an error message instead of raising APIError to keep the user in the UI flow
        return RedirectResponse(url=f"/?integration=error&msg=Authorization failed")


@router.delete("/{id}", response_model=APIResponse)
async def disconnect_integration(
    id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Severs the link between Samplit and the external platform.
    
    Archives the installation and stops all data synchronization.
    """
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE platform_installations SET status = 'archived', updated_at = NOW() WHERE id = $1 AND user_id = $2", 
            id, user_id
        )
        if result == "UPDATE 0":
            raise APIError("Integration not found or unauthorized", code=ErrorCodes.NOT_FOUND, status=404)
            
    return APIResponse(success=True, message="Platform connection severed successfully")
