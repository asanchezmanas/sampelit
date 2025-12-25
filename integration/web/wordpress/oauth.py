# integration/web/wordpress/oauth.py

"""
WordPress OAuth Integration

Integración con WordPress usando OAuth 2.0 y REST API.
Permite conectar sitios WordPress de forma segura.

Flow:
1. User clicks "Connect WordPress"
2. OAuth flow a WordPress.com o WooCommerce
3. Access token guardado
4. Sincronización automática
"""

import hmac
import hashlib
import logging
import secrets
import json
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


def generate_state_token(user_id: str) -> str:
    """
    Generate a secure state token for OAuth CSRF protection.
    Format: random_hex.hmac(random_hex + user_id)
    """
    random_part = secrets.token_hex(16)
    payload = f"{random_part}:{user_id}"
    
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{random_part}.{signature}"


def verify_state_token(state: str, user_id: str) -> bool:
    """
    Verify a state token for OAuth CSRF protection.
    """
    try:
        if '.' not in state:
            return False
            
        random_part, signature = state.split('.', 1)
        payload = f"{random_part}:{user_id}"
        
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


class WordPressIntegration:
    """
    ✅ FIXED: WordPress OAuth and webhook integration
    
    Features:
    - Robust webhook signature verification
    - Raw bytes verification before parsing
    - Proper error handling
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.logger = logging.getLogger(f"{__name__}.WordPressIntegration")
    
    # ========================================================================
    # OAUTH FLOW
    # ========================================================================
    
    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        
        base_url = "https://public-api.wordpress.com/oauth2/authorize"
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'global',  # Adjust as needed
            'state': state
        }
        
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        
        url = "https://public-api.wordpress.com/oauth2/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                
                self.logger.info("✅ Successfully exchanged code for token")
                
                return token_data
            
            except httpx.HTTPError as e:
                self.logger.error(f"OAuth token exchange failed: {e}")
                raise HTTPException(500, "Failed to exchange code for token")
    
    # ========================================================================
    # WEBHOOK SIGNATURE VERIFICATION - ✅ FIXED
    # ========================================================================
    
    def verify_webhook_signature(
        self,
        raw_payload: bytes,
        signature_header: str
    ) -> bool:
        """
        ✅ FIXED: Robust webhook signature verification
        
        CRITICAL: Always verify BEFORE parsing JSON
        
        Args:
            raw_payload: Raw request body as bytes
            signature_header: Value of X-Signature or X-Hub-Signature header
        
        Returns:
            True if signature is valid, False otherwise
        
        Example:
            @app.post("/webhooks/wordpress")
            async def webhook(request: Request):
                raw_body = await request.body()
                signature = request.headers.get('X-Signature')
                
                if not integration.verify_webhook_signature(raw_body, signature):
                    raise HTTPException(401, "Invalid signature")
                
                # NOW safe to parse
                payload = await request.json()
        """
        
        if not self.client_secret:
            self.logger.error("❌ client_secret not configured")
            return False
        
        if not signature_header:
            self.logger.error("❌ No signature header provided")
            return False
        
        try:
            # Compute expected signature
            expected_signature = hmac.new(
                self.client_secret.encode('utf-8'),
                raw_payload,  # ✅ Raw bytes, NOT parsed
                hashlib.sha256
            ).hexdigest()
            
            # Extract signature from header (may have prefix like "sha256=")
            if '=' in signature_header:
                # Format: "sha256=abcdef..."
                _, provided_signature = signature_header.split('=', 1)
            else:
                # Format: "abcdef..."
                provided_signature = signature_header
            
            # ✅ Constant-time comparison
            is_valid = hmac.compare_digest(
                expected_signature,
                provided_signature
            )
            
            if not is_valid:
                self.logger.warning(
                    "❌ Webhook signature verification failed. "
                    "Possible reasons: "
                    "1) Wrong client_secret, "
                    "2) Payload was modified, "
                    "3) Signature header incorrect"
                )
            else:
                self.logger.debug("✅ Webhook signature verified")
            
            return is_valid
        
        except Exception as e:
            self.logger.error(f"❌ Signature verification error: {e}")
            return False
    
    # ========================================================================
    # API CALLS
    # ========================================================================
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get WordPress user info"""
        
        url = "https://public-api.wordpress.com/rest/v1.1/me"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
            
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to get user info: {e}")
                raise HTTPException(500, "Failed to get user info")
    
    async def get_sites(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's WordPress sites"""
        
        url = "https://public-api.wordpress.com/rest/v1.1/me/sites"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get('sites', [])
            
            except httpx.HTTPError as e:
                self.logger.error(f"Failed to get sites: {e}")
                raise HTTPException(500, "Failed to get sites")


# ============================================================================
# ROUTER EXAMPLE - ✅ CORRECT USAGE
# ============================================================================

"""
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

integration = WordPressIntegration(
    client_id=settings.WORDPRESS_OAUTH_CLIENT_ID,
    client_secret=settings.WORDPRESS_OAUTH_CLIENT_SECRET,
    redirect_uri=settings.WORDPRESS_OAUTH_REDIRECT_URI
)

@router.post("/webhooks/wordpress")
async def wordpress_webhook(request: Request):
    '''
    ✅ CORRECT: Verify signature BEFORE parsing
    '''
    
    # 1. Get raw body FIRST
    raw_payload = await request.body()
    
    # 2. Get signature header
    signature = request.headers.get('X-Signature')
    
    # 3. Verify signature BEFORE parsing
    if not integration.verify_webhook_signature(raw_payload, signature):
        logger.warning(
            f"Invalid webhook signature from IP: {request.client.host}"
        )
        raise HTTPException(401, "Invalid signature")
    
    # 4. NOW safe to parse
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")
    
    # 5. Process webhook
    event_type = payload.get('event')
    
    if event_type == 'post_published':
        # Handle post published
        pass
    
    return {"status": "ok"}


@router.get("/auth/wordpress/callback")
async def wordpress_callback(code: str, state: str):
    '''
    OAuth callback handler
    '''
    
    # Verify state (CSRF protection)
    # ... verify state ...
    
    # Exchange code for token
    token_data = await integration.exchange_code_for_token(code)
    
    # Store token
    # ... store token ...
    
    return {"status": "success"}
"""
