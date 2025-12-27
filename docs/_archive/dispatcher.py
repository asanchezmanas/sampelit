# integration/webhooks/dispatcher.py

"""
Event Dispatcher para webhooks.
Sistema pub/sub interno que coordina la emisión de eventos
y su entrega a webhooks suscritos.
"""

import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import uuid
import logging

from integration.webhooks.models import (
    WebhookEventType, WebhookEventBase,
    ExperimentData, WinnerData, StatisticsData
)

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Dispatcher central de eventos para webhooks.
    
    Coordina:
    - Emisión de eventos desde servicios
    - Búsqueda de webhooks suscritos
    - Creación de deliveries para procesamiento async
    
    Uso:
        dispatcher = EventDispatcher(db)
        
        # Emitir evento
        await dispatcher.emit(
            event_type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
            user_id="usr_123",
            data={"experiment": {...}, "winner": {...}}
        )
    """
    
    def __init__(self, db, delivery_service=None):
        """
        Args:
            db: DatabaseManager instance
            delivery_service: WebhookDeliveryService (opcional, se crea si no se provee)
        """
        self.db = db
        self._delivery_service = delivery_service
        self._listeners: Dict[str, List[Callable]] = {}
    
    @property
    def delivery_service(self):
        """Lazy initialization del delivery service"""
        if self._delivery_service is None:
            from integration.webhooks.delivery import WebhookDeliveryService
            self._delivery_service = WebhookDeliveryService(self.db)
        return self._delivery_service
    
    async def emit(
        self,
        event_type: WebhookEventType,
        user_id: str,
        data: Dict[str, Any],
        experiment_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Emitir un evento a todos los webhooks suscritos.
        
        Args:
            event_type: Tipo de evento
            user_id: ID del usuario propietario
            data: Datos del evento
            experiment_id: ID del experimento relacionado (para filtrar webhooks)
            metadata: Metadata adicional
        
        Returns:
            ID del evento emitido
        
        Example:
            event_id = await dispatcher.emit(
                event_type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
                user_id="usr_123",
                data={
                    "experiment": {"id": "exp_456", "name": "Test"},
                    "winner": {"variant_id": "var_789", "confidence": 0.97}
                }
            )
        """
        # Crear evento
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        event = WebhookEventBase(
            id=event_id,
            type=event_type,
            created_at=datetime.utcnow(),
            data=data,
            metadata={
                "user_id": user_id,
                "environment": "production",
                **(metadata or {})
            }
        )
        
        logger.info(f"Emitting event {event_type.value} ({event_id}) for user {user_id}")
        
        # Buscar webhooks suscritos
        from data_access.repositories.webhook_repository import WebhookRepository
        webhook_repo = WebhookRepository(self.db)
        
        webhooks = await webhook_repo.get_subscribed_webhooks(
            event_type=event_type.value,
            user_id=user_id,
            experiment_id=experiment_id
        )
        
        if not webhooks:
            logger.debug(f"No webhooks subscribed to {event_type.value}")
            return event_id
        
        logger.info(f"Found {len(webhooks)} webhooks for event {event_type.value}")
        
        # Crear deliveries para cada webhook
        delivery_tasks = []
        for webhook in webhooks:
            task = self.delivery_service.queue_delivery(
                webhook=webhook,
                event=event
            )
            delivery_tasks.append(task)
        
        # Ejecutar en paralelo
        await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Notificar listeners internos (para testing/debugging)
        await self._notify_listeners(event_type, event)
        
        return event_id
    
    async def emit_experiment_created(
        self,
        user_id: str,
        experiment: Dict[str, Any]
    ) -> str:
        """Helper para emitir evento de experimento creado"""
        return await self.emit(
            event_type=WebhookEventType.EXPERIMENT_CREATED,
            user_id=user_id,
            experiment_id=experiment.get('id'),
            data={"experiment": experiment}
        )
    
    async def emit_experiment_started(
        self,
        user_id: str,
        experiment: Dict[str, Any]
    ) -> str:
        """Helper para emitir evento de experimento iniciado"""
        return await self.emit(
            event_type=WebhookEventType.EXPERIMENT_STARTED,
            user_id=user_id,
            experiment_id=experiment.get('id'),
            data={"experiment": experiment}
        )
    
    async def emit_significance_reached(
        self,
        user_id: str,
        experiment: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> str:
        """Helper para emitir evento de significancia alcanzada"""
        return await self.emit(
            event_type=WebhookEventType.EXPERIMENT_SIGNIFICANCE_REACHED,
            user_id=user_id,
            experiment_id=experiment.get('id'),
            data={
                "experiment": experiment,
                "statistics": statistics
            }
        )
    
    async def emit_winner_found(
        self,
        user_id: str,
        experiment: Dict[str, Any],
        winner: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> str:
        """
        Helper para emitir evento de ganador encontrado.
        
        Args:
            user_id: ID del usuario
            experiment: Datos del experimento
            winner: Datos del ganador (variant_id, variant_name, confidence, improvement)
            statistics: Estadísticas del experimento
        """
        return await self.emit(
            event_type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
            user_id=user_id,
            experiment_id=experiment.get('id'),
            data={
                "experiment": experiment,
                "winner": winner,
                "statistics": statistics
            }
        )
    
    async def emit_traffic_low(
        self,
        user_id: str,
        experiment: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> str:
        """Helper para emitir alerta de tráfico bajo"""
        return await self.emit(
            event_type=WebhookEventType.EXPERIMENT_TRAFFIC_LOW,
            user_id=user_id,
            experiment_id=experiment.get('id'),
            data={
                "experiment": experiment,
                "statistics": statistics,
                "message": "Experiment has low traffic and may take longer to reach significance"
            }
        )
    
    async def emit_test(self, user_id: str, webhook_id: str) -> str:
        """
        Emitir evento de prueba a un webhook específico.
        
        Args:
            user_id: ID del usuario
            webhook_id: ID del webhook a probar
        """
        from data_access.repositories.webhook_repository import WebhookRepository
        webhook_repo = WebhookRepository(self.db)
        
        webhook = await webhook_repo.get_by_id(webhook_id, user_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")
        
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        event = WebhookEventBase(
            id=event_id,
            type=WebhookEventType.WEBHOOK_TEST,
            created_at=datetime.utcnow(),
            data={
                "message": "This is a test event from Samplit",
                "webhook_id": webhook_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata={
                "user_id": user_id,
                "environment": "production",
                "is_test": True
            }
        )
        
        # Enviar directamente (no buscar otros webhooks)
        await self.delivery_service.queue_delivery(
            webhook=webhook,
            event=event
        )
        
        return event_id
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTERNAL LISTENERS (para testing/debugging)
    # ═══════════════════════════════════════════════════════════════════════
    
    def add_listener(self, event_type: str, callback: Callable):
        """Añadir listener interno para un tipo de evento"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def remove_listener(self, event_type: str, callback: Callable):
        """Remover listener interno"""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type]
                if cb != callback
            ]
    
    async def _notify_listeners(self, event_type: WebhookEventType, event: WebhookEventBase):
        """Notificar listeners internos"""
        listeners = self._listeners.get(event_type.value, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_dispatcher_instance: Optional[EventDispatcher] = None


def get_event_dispatcher(db=None) -> EventDispatcher:
    """
    Obtener instancia singleton del dispatcher.
    
    Args:
        db: DatabaseManager (requerido en primera llamada)
    """
    global _dispatcher_instance
    
    if _dispatcher_instance is None:
        if db is None:
            raise ValueError("db is required on first call")
        _dispatcher_instance = EventDispatcher(db)
    
    return _dispatcher_instance


def reset_dispatcher():
    """Resetear singleton (para testing)"""
    global _dispatcher_instance
    _dispatcher_instance = None
