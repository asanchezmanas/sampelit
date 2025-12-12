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

import aiohttp
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
import os

from ..base import WebIntegration, OAuthError, SyncError
import logging

logger = logging.getLogger(__name__)


class WordPressIntegration(WebIntegration):
    """
    WordPress Integration via OAuth
    
    Soporta:
    - WordPress.com sites
    - WooCommerce stores
    - Self-hosted WordPress con plugin
    """
    
    # OAuth endpoints
    OAUTH_AUTHORIZE_URL = "https://public-api.wordpress.com/oauth2/authorize"
    OAUTH_TOKEN_URL = "https://public-api.wordpress.com/oauth2/token"
    API_BASE_URL = "https://public-api.wordpress.com/rest/v1.1"
    
    def __init__(self, installation_id: str, config: Dict[str, Any]):
        super().__init__(installation_id, config)
        
        # OAuth credentials (from environment)
        self.client_id = os.getenv("WORDPRESS_CLIENT_ID")
        self.client_secret = os.getenv("WORDPRESS_CLIENT_SECRET")
        
        # Site-specific data
        self.site_url = config.get('site_url')
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.blog_id = config.get('blog_id')  # WordPress.com blog ID
    
    def get_platform_name(self) -> str:
        return "wordpress"
    
    # ============================================
    # OAuth Flow
    # ============================================
    
    async def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generar URL de autorización de WordPress
        
        El usuario será redirigido a WordPress.com para autorizar.
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': 'global',  # Full access (customize según necesidades)
        }
        
        return f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambiar código por access token
        """
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
                
                async with session.post(self.OAUTH_TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OAuthError(f"Token exchange failed: {error_text}")
                    
                    result = await response.json()
                    
                    # Get blog info
                    blog_info = await self._get_primary_blog(result['access_token'])
                    
                    return {
                        'access_token': result['access_token'],
                        'refresh_token': None,  # WordPress.com doesn't use refresh tokens
                        'expires_at': None,  # Tokens don't expire
                        'scope': result.get('scope', 'global'),
                        'shop_info': {
                            'blog_id': blog_info['ID'],
                            'name': blog_info['name'],
                            'url': blog_info['URL'],
                            'domain': blog_info.get('domain', ''),
                            'language': blog_info.get('lang', 'en')
                        }
                    }
        
        except aiohttp.ClientError as e:
            raise OAuthError(f"Network error during token exchange: {e}")
        except Exception as e:
            raise OAuthError(f"Unexpected error: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        WordPress.com tokens no expiran, no necesita refresh
        """
        raise NotImplementedError("WordPress.com tokens don't expire")
    
    async def _get_primary_blog(self, access_token: str) -> Dict[str, Any]:
        """
        Obtener el blog principal del usuario
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with aiohttp.ClientSession() as session:
            # Get user's blogs
            async with session.get(
                f"{self.API_BASE_URL}/me/sites",
                headers=headers
            ) as response:
                data = await response.json()
                
                if not data.get('sites'):
                    raise OAuthError("No sites found for this user")
                
                # Return first site (or primary site)
                sites = data['sites']
                primary = next((s for s in sites if s.get('is_primary')), sites[0])
                
                return primary
    
    # ============================================
    # Site Info
    # ============================================
    
    async def get_site_info(self) -> Dict[str, Any]:
        """
        Obtener información del sitio WordPress
        """
        if not self.access_token or not self.blog_id:
            raise SyncError("No access token or blog ID configured")
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.API_BASE_URL}/sites/{self.blog_id}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise SyncError(f"Failed to get site info: {response.status}")
                    
                    data = await response.json()
                    
                    return {
                        'name': data.get('name', ''),
                        'url': data.get('URL', ''),
                        'domain': data.get('domain', ''),
                        'platform_version': data.get('jetpack_version', 'Unknown'),
                        'language': data.get('lang', 'en'),
                        'timezone': data.get('timezone', 'UTC'),
                        'is_wpcom': data.get('is_wpcom', False),
                        'plan': data.get('plan', {}).get('product_name_short', 'Free')
                    }
        
        except aiohttp.ClientError as e:
            raise SyncError(f"Network error getting site info: {e}")
    
    # ============================================
    # Experiment Sync
    # ============================================
    
    async def sync_experiment(self, experiment_id: str, experiment_data: Dict[str, Any]) -> bool:
        """
        Sincronizar experimento con WordPress
        
        Esto puede ser:
        1. Crear un post con metadata del experimento
        2. Usar custom post type
        3. Almacenar en options table via API
        """
        if not self.access_token or not self.blog_id:
            raise SyncError("Not authenticated")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Crear custom post para el experimento
                post_data = {
                    'title': f"Samplit Experiment: {experiment_data.get('name', experiment_id)}",
                    'status': 'private',  # No público
                    'type': 'post',  # O un custom post type si el plugin lo soporta
                    'meta': {
                        'samplit_experiment_id': experiment_id,
                        'samplit_experiment_data': experiment_data
                    }
                }
                
                url = f"{self.API_BASE_URL}/sites/{self.blog_id}/posts/new"
                
                async with session.post(url, headers=headers, json=post_data) as response:
                    if response.status not in [200, 201]:
                        error = await response.text()
                        self.logger.error(f"Failed to sync experiment: {error}")
                        return False
                    
                    result = await response.json()
                    self.logger.info(f"Experiment {experiment_id} synced as post {result['ID']}")
                    return True
        
        except Exception as e:
            self.logger.error(f"Error syncing experiment: {e}")
            return False
    
    async def remove_experiment(self, experiment_id: str) -> bool:
        """
        Eliminar experimento de WordPress
        """
        if not self.access_token or not self.blog_id:
            return False
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Buscar post del experimento
                search_url = f"{self.API_BASE_URL}/sites/{self.blog_id}/posts"
                params = {
                    'meta_key': 'samplit_experiment_id',
                    'meta_value': experiment_id
                }
                
                async with session.get(search_url, headers=headers, params=params) as response:
                    data = await response.json()
                    posts = data.get('posts', [])
                    
                    if not posts:
                        self.logger.warning(f"No post found for experiment {experiment_id}")
                        return True  # Ya no existe
                    
                    # Eliminar cada post encontrado
                    for post in posts:
                        delete_url = f"{self.API_BASE_URL}/sites/{self.blog_id}/posts/{post['ID']}/delete"
                        await session.post(delete_url, headers=headers)
                    
                    return True
        
        except Exception as e:
            self.logger.error(f"Error removing experiment: {e}")
            return False
    
    # ============================================
    # Webhooks
    # ============================================
    
    async def register_webhooks(self, webhook_url: str) -> List[str]:
        """
        WordPress.com no soporta webhooks directamente
        
        Alternativas:
        1. Usar Jetpack webhooks
        2. Polling periódico
        3. Plugin custom que envíe webhooks
        """
        self.logger.warning("WordPress.com doesn't support custom webhooks natively")
        return []
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar webhook (si se implementa via plugin)
        """
        self.logger.info(f"Received webhook: {event_type}")
        
        # Verificar firma HMAC si viene del plugin
        if 'signature' in payload:
            if not self._verify_webhook_signature(payload):
                raise WebhookError("Invalid webhook signature")
        
        # Procesar según tipo
        if event_type == 'experiment_view':
            return await self._handle_experiment_view(payload)
        elif event_type == 'experiment_conversion':
            return await self._handle_conversion(payload)
        
        return {'status': 'ignored', 'event_type': event_type}
    
    def _verify_webhook_signature(self, payload: Dict[str, Any]) -> bool:
        """
        Verificar firma HMAC del webhook
        """
        if not self.client_secret:
            return False
        
        signature = payload.pop('signature', '')
        expected = hmac.new(
            self.client_secret.encode(),
            str(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    async def _handle_experiment_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar vista de experimento"""
        # TODO: Registrar view en analytics
        return {'status': 'processed'}
    
    async def _handle_conversion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar conversión"""
        # TODO: Registrar conversión
        return {'status': 'processed'}
    
    # ============================================
    # Health & Status
    # ============================================
    
    async def check_connection(self) -> bool:
        """
        Verificar que el access token sigue válido
        """
        if not self.access_token:
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_BASE_URL}/me",
                    headers=headers
                ) as response:
                    return response.status == 200
        
        except:
            return False


# ============================================
# Helper Functions
# ============================================

def generate_state_token() -> str:
    """
    Generar token aleatorio para CSRF protection
    """
    import secrets
    return secrets.token_urlsafe(32)


async def verify_state_token(state: str, expected_state: str) -> bool:
    """
    Verificar que el state token coincide
    """
    return hmac.compare_digest(state, expected_state)
