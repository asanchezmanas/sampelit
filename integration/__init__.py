# integration/__init__.py

"""
Samplit Integrations Module

Integraciones con plataformas externas:
- Web: WordPress, Shopify, WooCommerce
- Email: Mailchimp, SendGrid (coming soon)
- Proxy: HTML injection middleware
"""

from .web.base import WebIntegration, IntegrationError
from .email.base import EmailIntegration, EmailIntegrationError

__all__ = [
    'WebIntegration',
    'EmailIntegration',
    'IntegrationError',
    'EmailIntegrationError'
]
