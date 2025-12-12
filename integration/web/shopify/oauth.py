# integration/web/shopify/oauth.py

"""
Shopify OAuth Integration

Integración con Shopify usando OAuth 2.0 y Admin API.
Shopify tiene excelente soporte para apps, webhooks y API.

Flow:
1. User clicks "Connect Shopify"
2. OAuth flow a su tienda Shopify
3. Access token guardado
4. Webhooks registrados automáticamente
5. Sincronización en tiempo real
"""

import aiohttp
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlencode
import os
import json

from ..base import WebIntegration, OAuthError, SyncError, WebhookError
import logging

logger = logging.getLogger(__name__)


class ShopifyIntegration(WebIntegration):
    """
    Shopify Integration via OAuth
    
    Shopify es ideal para A/B testing porque:
    - Excelente soporte de webhooks
    - API muy completa
    - Fácil de integrar
    """
    
    def __init__(self, installation_id: str, config: Dict[str, Any]):
        super().__init__(installation_id, config)
        
        # OAuth credentials
        self.api_key = os.getenv("SHOPIFY_API_KEY")
        self.api_secret = os.getenv("SHOPIFY_API_SECRET")
        
        # Shop-specific data
        self.shop_domain = config.get('shop_domain')  # ej: mystore.myshopify.com
        self.access_token = config.get('access_token')
        self.api_version = config.get('api_version', '2024-01')  # Latest stable
        
        # API base URL
        if self.shop_domain:
            self.api_base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
    
    def get_platform_name(self) -> str:
        return "shopify"
    
    # ============================================
    # OAuth Flow
    # ============================================
    
    async def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generar URL de autorización de Shopify
        
        El usuario será redirigido a su tienda Shopify para autorizar.
        """
        if not self.shop_domain:
            raise OAuthError("Shop domain not configured")
        
        # Scopes necesarios
        scopes = [
            'read_products',
            'write_products',
            'read_orders',
            'read_customers',
            'write_script_tags',  # Para inyectar tracker
            'read_themes',
            'write_themes'  # Para modificar tema (opcional)
        ]
        
        params = {
            'client_id': self.api_key,
            'scope': ','.join(scopes),
            'redirect_uri': redirect_uri,
            'state': state,
            'grant_options[]': 'per-user'  # Optional: per-user tokens
        }
        
        return f"https://{self.shop_domain}/admin/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambiar código por access token
        """
        if not self.shop_domain:
            raise OAuthError("Shop domain not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://{self.shop_domain}/admin/oauth/access_token"
                
                data = {
                    'client_id': self.api_key,
                    'client_secret': self.api_secret,
                    'code': code
                }
                
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OAuthError(f"Token exchange failed: {error_text}")
                    
                    result = await response.json()
                    
                    # Get shop info
                    shop_info = await self._get_shop_info(result['access_token'])
                    
                    return {
                        'access_token': result['access_token'],
                        'refresh_token': None,  # Shopify no usa refresh tokens
                        'expires_at': None,  # Los tokens no expiran
                        'scope': result['scope'],
                        'shop_info': shop_info
                    }
        
        except aiohttp.ClientError as e:
            raise OAuthError(f"Network error: {e}")
        except Exception as e:
            raise OAuthError(f"Unexpected error: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Shopify tokens no expiran, no necesita refresh
        """
        raise NotImplementedError("Shopify tokens don't expire")
    
    async def _get_shop_info(self, access_token: str) -> Dict[str, Any]:
        """
        Obtener información de la tienda
        """
        headers = {'X-Shopify-Access-Token': access_token}
        
        async with aiohttp.ClientSession() as session:
            url = f"https://{self.shop_domain}/admin/api/{self.api_version}/shop.json"
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise OAuthError(f"Failed to get shop info: {response.status}")
                
                data = await response.json()
                shop = data['shop']
                
                return {
                    'shop_id': shop['id'],
                    'name': shop['name'],
                    'email': shop['email'],
                    'domain': shop['domain'],
                    'myshopify_domain': shop['myshopify_domain'],
                    'currency': shop['currency'],
                    'timezone': shop['timezone'],
                    'iana_timezone': shop['iana_timezone'],
                    'plan_name': shop['plan_name'],
                    'country': shop.get('country', ''),
                    'primary_locale': shop.get('primary_locale', 'en')
                }
    
    # ============================================
    # Site Info
    # ============================================
    
    async def get_site_info(self) -> Dict[str, Any]:
        """
        Obtener información de la tienda Shopify
        """
        if not self.access_token:
            raise SyncError("No access token configured")
        
        return await self._get_shop_info(self.access_token)
    
    # ============================================
    # Experiment Sync
    # ============================================
    
    async def sync_experiment(self, experiment_id: str, experiment_data: Dict[str, Any]) -> bool:
        """
        Sincronizar experimento con Shopify
        
        Opciones:
        1. Crear script tag para inyectar el tracker
        2. Crear metafield en el shop con el experimento
        3. Modificar el tema (avanzado)
        """
        if not self.access_token:
            raise SyncError("Not authenticated")
        
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            # ✅ Método 1: Crear Script Tag (más simple y no invasivo)
            script_tag_created = await self._create_script_tag(experiment_id, headers)
            
            # ✅ Método 2: Guardar metadata en Metafield
            metafield_created = await self._create_experiment_metafield(
                experiment_id, 
                experiment_data, 
                headers
            )
            
            return script_tag_created and metafield_created
        
        except Exception as e:
            self.logger.error(f"Error syncing experiment: {e}")
            return False
    
    async def _create_script_tag(self, experiment_id: str, headers: Dict) -> bool:
        """
        Crear script tag en Shopify para el experimento
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base_url}/script_tags.json"
            
            # URL del tracker (dinámico según el experimento)
            tracker_url = f"https://cdn.samplit.com/tracker.js?exp={experiment_id}"
            
            data = {
                'script_tag': {
                    'event': 'onload',
                    'src': tracker_url,
                    'display_scope': 'all',  # Todas las páginas
                    'cache': False
                }
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    self.logger.info(f"Script tag created: {result['script_tag']['id']}")
                    return True
                else:
                    error = await response.text()
                    self.logger.error(f"Failed to create script tag: {error}")
                    return False
    
    async def _create_experiment_metafield(
        self, 
        experiment_id: str, 
        experiment_data: Dict, 
        headers: Dict
    ) -> bool:
        """
        Guardar metadata del experimento en Shopify Metafields
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base_url}/metafields.json"
            
            data = {
                'metafield': {
                    'namespace': 'samplit',
                    'key': f'experiment_{experiment_id}',
                    'value': json.dumps(experiment_data),
                    'type': 'json',
                    'owner_resource': 'shop'
                }
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 201:
                    self.logger.info(f"Metafield created for experiment {experiment_id}")
                    return True
                else:
                    error = await response.text()
                    self.logger.warning(f"Metafield creation failed: {error}")
                    return False  # No crítico
    
    async def remove_experiment(self, experiment_id: str) -> bool:
        """
        Eliminar experimento de Shopify
        """
        if not self.access_token:
            return False
        
        headers = {'X-Shopify-Access-Token': self.access_token}
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Eliminar script tags del experimento
                url = f"{self.api_base_url}/script_tags.json"
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    
                    for script_tag in data.get('script_tags', []):
                        if experiment_id in script_tag.get('src', ''):
                            delete_url = f"{self.api_base_url}/script_tags/{script_tag['id']}.json"
                            await session.delete(delete_url, headers=headers)
                
                # 2. Eliminar metafield
                metafields_url = f"{self.api_base_url}/metafields.json?namespace=samplit"
                async with session.get(metafields_url, headers=headers) as response:
                    data = await response.json()
                    
                    for metafield in data.get('metafields', []):
                        if metafield['key'] == f'experiment_{experiment_id}':
                            delete_url = f"{self.api_base_url}/metafields/{metafield['id']}.json"
                            await session.delete(delete_url, headers=headers)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Error removing experiment: {e}")
            return False
    
    # ============================================
    # Webhooks
    # ============================================
    
    async def register_webhooks(self, webhook_url: str) -> List[str]:
        """
        Registrar webhooks en Shopify
        
        Shopify tiene excelente soporte para webhooks en tiempo real.
        """
        if not self.access_token:
            raise SyncError("Not authenticated")
        
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        # Webhooks que nos interesan
        webhook_topics = [
            'orders/create',      # Nueva orden (conversión)
            'checkouts/create',   # Checkout iniciado
            'products/update',    # Producto actualizado
            'app/uninstalled'     # App desinstalada
        ]
        
        webhook_ids = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for topic in webhook_topics:
                    url = f"{self.api_base_url}/webhooks.json"
                    
                    data = {
                        'webhook': {
                            'topic': topic,
                            'address': f"{webhook_url}/shopify",
                            'format': 'json'
                        }
                    }
                    
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 201:
                            result = await response.json()
                            webhook_id = result['webhook']['id']
                            webhook_ids.append(str(webhook_id))
                            self.logger.info(f"Webhook registered: {topic} -> {webhook_id}")
                        else:
                            error = await response.text()
                            self.logger.error(f"Failed to register webhook {topic}: {error}")
            
            return webhook_ids
        
        except Exception as e:
            self.logger.error(f"Error registering webhooks: {e}")
            return []
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar webhook de Shopify
        """
        self.logger.info(f"Received Shopify webhook: {event_type}")
        
        # Shopify envía el topic en el header X-Shopify-Topic
        # Validamos la firma HMAC
        
        if event_type == 'orders/create':
            return await self._handle_order_created(payload)
        
        elif event_type == 'checkouts/create':
            return await self._handle_checkout_created(payload)
        
        elif event_type == 'app/uninstalled':
            return await self._handle_app_uninstalled(payload)
        
        return {'status': 'ignored', 'event_type': event_type}
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """
        Verificar firma HMAC del webhook de Shopify
        
        Shopify envía X-Shopify-Hmac-SHA256 header
        """
        if not self.api_secret:
            return False
        
        computed_hmac = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(computed_hmac, hmac_header)
    
    async def _handle_order_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar nueva orden (conversión confirmada)
        """
        order_id = payload.get('id')
        order_number = payload.get('order_number')
        total_price = payload.get('total_price')
        
        self.logger.info(f"Order created: #{order_number} - ${total_price}")
        
        # TODO: Registrar conversión en Samplit
        # Necesitamos identificar el usuario y el experimento
        
        return {
            'status': 'processed',
            'order_id': order_id,
            'conversion_registered': True
        }
    
    async def _handle_checkout_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar checkout iniciado (micro-conversión)
        """
        checkout_token = payload.get('token')
        
        self.logger.info(f"Checkout created: {checkout_token}")
        
        # TODO: Registrar micro-conversión
        
        return {
            'status': 'processed',
            'checkout_token': checkout_token
        }
    
    async def _handle_app_uninstalled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        App desinstalada - cleanup
        """
        self.logger.warning("App uninstalled from shop")
        
        # TODO: Marcar instalación como inactiva en BD
        # TODO: Limpiar datos sensibles
        
        return {'status': 'uninstalled'}
    
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
            headers = {'X-Shopify-Access-Token': self.access_token}
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/shop.json"
                
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        
        except:
            return False


# ============================================
# Helper Functions
# ============================================

def extract_shop_domain(shop_url: str) -> str:
    """
    Extraer el shop domain de una URL
    
    Ejemplos:
    - "mystore.myshopify.com" -> "mystore.myshopify.com"
    - "https://mystore.myshopify.com" -> "mystore.myshopify.com"
    - "mystore" -> "mystore.myshopify.com"
    """
    shop_url = shop_url.strip()
    
    # Remove protocol
    if '://' in shop_url:
        shop_url = shop_url.split('://')[1]
    
    # Remove path
    if '/' in shop_url:
        shop_url = shop_url.split('/')[0]
    
    # Add .myshopify.com if not present
    if '.myshopify.com' not in shop_url:
        shop_url = f"{shop_url}.myshopify.com"
    
    return shop_url
