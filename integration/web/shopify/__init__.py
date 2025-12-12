# integration/web/shopify/__init__.py

"""
Shopify Integration Module
"""

from .oauth import ShopifyIntegration, extract_shop_domain

__all__ = ['ShopifyIntegration', 'extract_shop_domain']
