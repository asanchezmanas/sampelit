# integration/web/__init__.py

"""
Web Platform Integrations

WordPress, Shopify, WooCommerce, etc.
"""

from .base import WebIntegration, IntegrationError, OAuthError, SyncError
from .wordpress.oauth import WordPressIntegration
from .shopify.oauth import ShopifyIntegration

__all__ = [
    'WebIntegration',
    'IntegrationError',
    'OAuthError',
    'SyncError',
    'WordPressIntegration',
    'ShopifyIntegration'
]
