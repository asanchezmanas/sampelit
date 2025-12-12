# integration/email/__init__.py

"""
Email Service Integrations

📧 Coming Soon:
- Mailchimp
- SendGrid
- Mailgun
- Klaviyo
- Customer.io
"""

from .base import (
    EmailIntegration, 
    EmailIntegrationError,
    CampaignError,
    ABTestError,
    MailchimpIntegration,
    SendGridIntegration
)

__all__ = [
    'EmailIntegration',
    'EmailIntegrationError',
    'CampaignError',
    'ABTestError',
    'MailchimpIntegration',
    'SendGridIntegration'
]
