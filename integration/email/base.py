# integration/email/base.py

"""
Base Email Integration Class

📧 PREPARADO PARA FUTURO

Clase base para integraciones de email (Mailchimp, SendGrid, etc.)
Define la interfaz común para proveedores de email.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailIntegration(ABC):
    """
    Base class for email service integrations
    
    Futuras integraciones como:
    - Mailchimp
    - SendGrid
    - Mailgun
    - ActiveCampaign
    - Klaviyo
    - Customer.io
    """
    
    def __init__(self, installation_id: str, config: Dict[str, Any]):
        self.installation_id = installation_id
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{installation_id[:8]}")
    
    # ============================================
    # OAuth Flow (si aplica)
    # ============================================
    
    @abstractmethod
    async def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generar URL de OAuth (si el provider lo usa)"""
        pass
    
    @abstractmethod
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Intercambiar código OAuth por API key"""
        pass
    
    # ============================================
    # Lists & Audiences
    # ============================================
    
    @abstractmethod
    async def get_lists(self) -> List[Dict[str, Any]]:
        """
        Obtener listas de email
        
        Returns:
            [
                {
                    'id': str,
                    'name': str,
                    'subscribers': int,
                    'created_at': datetime
                }
            ]
        """
        pass
    
    @abstractmethod
    async def get_list_subscribers(self, list_id: str) -> List[Dict[str, Any]]:
        """Obtener subscribers de una lista"""
        pass
    
    # ============================================
    # Campaigns
    # ============================================
    
    @abstractmethod
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """
        Crear campaña de email
        
        Args:
            campaign_data: {
                'name': str,
                'subject': str,
                'from_email': str,
                'from_name': str,
                'list_id': str,
                'template_id': Optional[str],
                'html_content': str,
                'variants': List[Dict]  # Para A/B testing
            }
        
        Returns:
            campaign_id
        """
        pass
    
    @abstractmethod
    async def send_campaign(self, campaign_id: str) -> bool:
        """Enviar campaña"""
        pass
    
    @abstractmethod
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de campaña
        
        Returns:
            {
                'sent': int,
                'opens': int,
                'clicks': int,
                'conversions': int,
                'open_rate': float,
                'click_rate': float,
                'conversion_rate': float
            }
        """
        pass
    
    # ============================================
    # A/B Testing (lo interesante para Samplit)
    # ============================================
    
    @abstractmethod
    async def create_ab_test(self, ab_test_data: Dict[str, Any]) -> str:
        """
        Crear A/B test de email
        
        Args:
            ab_test_data: {
                'name': str,
                'list_id': str,
                'variants': [
                    {'subject': str, 'content': str},
                    {'subject': str, 'content': str}
                ],
                'test_percentage': float,
                'winner_criteria': str  # 'opens', 'clicks', 'conversions'
            }
        """
        pass
    
    @abstractmethod
    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        Obtener resultados del A/B test
        """
        pass
    
    # ============================================
    # Webhooks
    # ============================================
    
    @abstractmethod
    async def register_webhooks(self, webhook_url: str) -> List[str]:
        """
        Registrar webhooks para eventos de email
        
        Eventos típicos:
        - email_sent
        - email_opened
        - email_clicked
        - email_bounced
        - unsubscribed
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar webhook"""
        pass
    
    # ============================================
    # Health & Status
    # ============================================
    
    @abstractmethod
    async def check_connection(self) -> bool:
        """Verificar que la conexión sigue activa"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Nombre del proveedor (mailchimp, sendgrid, etc)"""
        pass


class EmailIntegrationError(Exception):
    """Base exception para errores de integración de email"""
    pass


class CampaignError(EmailIntegrationError):
    """Error durante creación/envío de campaña"""
    pass


class ABTestError(EmailIntegrationError):
    """Error durante A/B test"""
    pass


# ============================================
# PLACEHOLDER: Ejemplo de integración futura
# ============================================

class MailchimpIntegration(EmailIntegration):
    """
    📧 PLACEHOLDER - Mailchimp Integration
    
    Esta clase está preparada pero no implementada aún.
    Se implementará cuando se añada el módulo de email optimization.
    """
    
    def get_platform_name(self) -> str:
        return "mailchimp"
    
    async def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def get_lists(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def get_list_subscribers(self, list_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def send_campaign(self, campaign_id: str) -> bool:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def create_ab_test(self, ab_test_data: Dict[str, Any]) -> str:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def register_webhooks(self, webhook_url: str) -> List[str]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Mailchimp integration coming soon")
    
    async def check_connection(self) -> bool:
        raise NotImplementedError("Mailchimp integration coming soon")


class SendGridIntegration(EmailIntegration):
    """
    📧 PLACEHOLDER - SendGrid Integration
    
    Coming soon...
    """
    
    def get_platform_name(self) -> str:
        return "sendgrid"
    
    # ... same NotImplementedError methods as Mailchimp
