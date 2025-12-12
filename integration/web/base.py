# integration/web/base.py

"""
Base Web Integration Class

Clase base para todas las integraciones web (WordPress, Shopify, etc.)
Define la interfaz común y funcionalidad compartida.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WebIntegration(ABC):
    """
    Base class for web platform integrations
    
    Todas las integraciones web deben heredar de esta clase
    y implementar los métodos abstractos.
    """
    
    def __init__(self, installation_id: str, config: Dict[str, Any]):
        self.installation_id = installation_id
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{installation_id[:8]}")
    
    # ============================================
    # OAuth Flow (obligatorio)
    # ============================================
    
    @abstractmethod
    async def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generar URL de OAuth
        
        Args:
            redirect_uri: URL donde redirigir después del OAuth
            state: Estado para CSRF protection
        
        Returns:
            URL completa de autorización
        """
        pass
    
    @abstractmethod
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambiar código OAuth por access token
        
        Args:
            code: Authorization code
            redirect_uri: Redirect URI usado en el paso anterior
        
        Returns:
            {
                'access_token': str,
                'refresh_token': Optional[str],
                'expires_at': Optional[datetime],
                'scope': str,
                'shop_info': Optional[Dict]  # Info adicional de la tienda/sitio
            }
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refrescar access token (si aplica)
        
        Returns:
            Mismo formato que exchange_code_for_token
        """
        pass
    
    # ============================================
    # Site Info (obligatorio)
    # ============================================
    
    @abstractmethod
    async def get_site_info(self) -> Dict[str, Any]:
        """
        Obtener información del sitio
        
        Returns:
            {
                'name': str,
                'url': str,
                'domain': str,
                'platform_version': str,
                'currency': Optional[str],
                'language': Optional[str],
                'timezone': Optional[str]
            }
        """
        pass
    
    # ============================================
    # Experiment Sync (obligatorio)
    # ============================================
    
    @abstractmethod
    async def sync_experiment(self, experiment_id: str, experiment_data: Dict[str, Any]) -> bool:
        """
        Sincronizar experimento con la plataforma
        
        Args:
            experiment_id: ID del experimento en Samplit
            experiment_data: Datos del experimento
        
        Returns:
            True si la sincronización fue exitosa
        """
        pass
    
    @abstractmethod
    async def remove_experiment(self, experiment_id: str) -> bool:
        """
        Eliminar experimento de la plataforma
        """
        pass
    
    # ============================================
    # Webhooks (obligatorio)
    # ============================================
    
    @abstractmethod
    async def register_webhooks(self, webhook_url: str) -> List[str]:
        """
        Registrar webhooks necesarios
        
        Args:
            webhook_url: URL base donde recibir webhooks
        
        Returns:
            Lista de IDs de webhooks registrados
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar webhook recibido
        
        Returns:
            Respuesta procesada o None
        """
        pass
    
    # ============================================
    # Health & Status (obligatorio)
    # ============================================
    
    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Verificar que la conexión sigue activa
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado completo de la integración
        """
        try:
            is_connected = await self.check_connection()
            site_info = await self.get_site_info() if is_connected else {}
            
            return {
                'connected': is_connected,
                'installation_id': self.installation_id,
                'platform': self.get_platform_name(),
                'site_info': site_info,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    # ============================================
    # Helper Methods
    # ============================================
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Retornar nombre de la plataforma (ej: 'wordpress', 'shopify')"""
        pass
    
    def get_installation_id(self) -> str:
        """Obtener installation ID"""
        return self.installation_id
    
    async def log_event(self, event_type: str, message: str, metadata: Optional[Dict] = None):
        """
        Log de evento de integración
        
        Útil para debugging y auditoría
        """
        self.logger.info(
            f"[{event_type}] {message}",
            extra={'metadata': metadata or {}}
        )


class IntegrationError(Exception):
    """Base exception para errores de integración"""
    pass


class OAuthError(IntegrationError):
    """Error durante OAuth flow"""
    pass


class SyncError(IntegrationError):
    """Error durante sincronización"""
    pass


class WebhookError(IntegrationError):
    """Error procesando webhook"""
    pass
