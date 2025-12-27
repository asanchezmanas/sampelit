# integration/webhooks/delivery.py

"""
Servicio de entrega de webhooks.
Maneja el envío HTTP, reintentos, y tracking de entregas.
"""

import httpx
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from integration.webhooks.models import (
    Webhook, WebhookDelivery, WebhookEventBase, DeliveryStatus
)
from integration.webhooks.signatures import get_signature_headers

logger = logging.getLogger(__name__)


# Configuración
MAX_FAILURES_BEFORE_DISABLE = 10
REQUEST_TIMEOUT = 10.0  # segundos
MAX_RESPONSE_BODY_SIZE = 1000  # chars


class WebhookDeliveryService:
    """
    Servicio para entregar webhooks a endpoints externos.
    
    Responsabilidades:
    - Crear registros de delivery
    - Enviar requests HTTP con firma
    - Manejar errores y reintentos
    - Auto-deshabilitar webhooks problemáticos
    
    Uso:
        service = WebhookDeliveryService(db)
        await service.queue_delivery(webhook, event)
    """
    
    def __init__(self, db):
        """
        Args:
            db: DatabaseManager instance
        """
        self.db = db
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtener cliente HTTP reutilizable"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=False,  # Seguridad: no seguir redirects
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Samplit-Webhook/1.0"
                }
            )
        return self._client
    
    async def queue_delivery(
        self,
        webhook: Webhook,
        event: WebhookEventBase
    ) -> WebhookDelivery:
        """
        Encolar entrega de webhook.
        
        Crea el registro de delivery e intenta entregar inmediatamente.
        Si falla, queda encolado para retry.
        
        Args:
            webhook: Webhook destino
            event: Evento a enviar
        
        Returns:
            WebhookDelivery creado
        """
        from data_access.repositories.webhook_repository import WebhookDeliveryRepository
        
        delivery_repo = WebhookDeliveryRepository(self.db)
        
        # Serializar evento a payload
        payload = event.model_dump(mode='json')
        
        # Crear registro de delivery
        delivery = await delivery_repo.create(
            webhook_id=webhook.id,
            event_type=event.type.value if hasattr(event.type, 'value') else event.type,
            event_id=event.id,
            payload=payload
        )
        
        logger.info(
            f"Queued delivery {delivery.id} for webhook {webhook.id} "
            f"(event: {event.type})"
        )
        
        # Intentar entrega inmediata (async, no bloquea)
        asyncio.create_task(self.attempt_delivery(delivery, webhook))
        
        return delivery
    
    async def attempt_delivery(
        self,
        delivery: WebhookDelivery,
        webhook: Optional[Webhook] = None
    ) -> bool:
        """
        Intentar entregar un webhook.
        
        Args:
            delivery: Registro de delivery
            webhook: Webhook (si no se provee, se obtiene de DB)
        
        Returns:
            True si la entrega fue exitosa
        """
        from data_access.repositories.webhook_repository import (
            WebhookRepository, WebhookDeliveryRepository
        )
        
        webhook_repo = WebhookRepository(self.db)
        delivery_repo = WebhookDeliveryRepository(self.db)
        
        # Obtener webhook si no se proveyó
        if webhook is None:
            # Necesitamos obtener el webhook de alguna forma
            # Por ahora asumimos que delivery tiene user_id o lo obtenemos de otra forma
            logger.warning(f"Webhook not provided for delivery {delivery.id}")
            return False
        
        # Verificar que webhook está activo
        if not webhook.is_active:
            logger.warning(f"Webhook {webhook.id} is not active, skipping delivery")
            await delivery_repo.mark_failed(
                delivery.id,
                "Webhook is disabled",
                schedule_retry=False
            )
            return False
        
        # Preparar payload
        payload_bytes = json.dumps(delivery.payload, default=str).encode('utf-8')
        
        # Generar headers de firma
        signature_headers = get_signature_headers(payload_bytes, webhook.secret)
        
        headers = {
            **signature_headers,
            "X-Samplit-Event": delivery.event_type,
            "X-Samplit-Delivery-Id": delivery.id,
        }
        
        try:
            client = await self._get_client()
            
            logger.debug(f"Sending webhook to {webhook.url}")
            
            response = await client.post(
                webhook.url,
                content=payload_bytes,
                headers=headers
            )
            
            # Capturar response body (truncado)
            response_body = response.text[:MAX_RESPONSE_BODY_SIZE] if response.text else None
            
            # Evaluar resultado
            if 200 <= response.status_code < 300:
                # Éxito
                await delivery_repo.mark_success(
                    delivery.id,
                    response.status_code,
                    response_body
                )
                
                # Resetear contador de fallos del webhook
                await webhook_repo.reset_failure_count(webhook.id)
                
                logger.info(
                    f"Delivery {delivery.id} successful "
                    f"(status: {response.status_code})"
                )
                return True
            
            else:
                # Error HTTP (4xx, 5xx)
                error_msg = f"HTTP {response.status_code}"
                if response_body:
                    error_msg += f": {response_body[:100]}"
                
                await self._handle_failure(
                    delivery, webhook, delivery_repo, webhook_repo,
                    error_msg, response.status_code
                )
                return False
        
        except httpx.TimeoutException:
            await self._handle_failure(
                delivery, webhook, delivery_repo, webhook_repo,
                "Request timeout"
            )
            return False
        
        except httpx.ConnectError as e:
            await self._handle_failure(
                delivery, webhook, delivery_repo, webhook_repo,
                f"Connection error: {str(e)[:100]}"
            )
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error delivering webhook: {e}", exc_info=True)
            await self._handle_failure(
                delivery, webhook, delivery_repo, webhook_repo,
                f"Unexpected error: {str(e)[:100]}"
            )
            return False
    
    async def _handle_failure(
        self,
        delivery: WebhookDelivery,
        webhook: Webhook,
        delivery_repo,
        webhook_repo,
        error_message: str,
        response_status: Optional[int] = None
    ):
        """Manejar fallo de entrega"""
        
        logger.warning(
            f"Delivery {delivery.id} failed: {error_message} "
            f"(attempt {delivery.attempt_count + 1})"
        )
        
        # Marcar delivery como fallido
        await delivery_repo.mark_failed(
            delivery.id,
            error_message,
            response_status,
            schedule_retry=True
        )
        
        # Incrementar contador de fallos del webhook
        failure_count = await webhook_repo.increment_failure_count(webhook.id)
        
        # Auto-deshabilitar si hay muchos fallos
        if failure_count >= MAX_FAILURES_BEFORE_DISABLE:
            await webhook_repo.auto_disable(
                webhook.id,
                f"Too many consecutive failures ({failure_count})"
            )
            
            # TODO: Enviar email al usuario notificando
            logger.warning(
                f"Webhook {webhook.id} auto-disabled after {failure_count} failures"
            )
    
    async def process_pending_retries(self, limit: int = 50) -> int:
        """
        Procesar entregas pendientes de retry.
        
        Este método debe ser llamado periódicamente por un worker.
        
        Args:
            limit: Máximo número de deliveries a procesar
        
        Returns:
            Número de deliveries procesados
        """
        from data_access.repositories.webhook_repository import (
            WebhookRepository, WebhookDeliveryRepository
        )
        
        webhook_repo = WebhookRepository(self.db)
        delivery_repo = WebhookDeliveryRepository(self.db)
        
        # Obtener deliveries pendientes
        pending = await delivery_repo.get_pending_retries(limit=limit)
        
        if not pending:
            return 0
        
        logger.info(f"Processing {len(pending)} pending webhook deliveries")
        
        processed = 0
        for delivery in pending:
            # Obtener webhook
            # Nota: Necesitamos una forma de obtener el webhook desde el delivery
            # Por ahora, hacemos un query directo
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT w.* FROM webhooks w
                    JOIN webhook_deliveries d ON d.webhook_id = w.id
                    WHERE d.id = $1
                    """,
                    delivery.id
                )
            
            if not row:
                logger.warning(f"Webhook not found for delivery {delivery.id}")
                continue
            
            webhook = webhook_repo._row_to_webhook(row)
            
            await self.attempt_delivery(delivery, webhook)
            processed += 1
        
        return processed
    
    async def manual_retry(self, delivery_id: str, user_id: str) -> bool:
        """
        Reintentar entrega manualmente.
        
        Args:
            delivery_id: ID de la entrega
            user_id: ID del usuario (para verificar ownership)
        
        Returns:
            True si se encoló el retry
        """
        from data_access.repositories.webhook_repository import (
            WebhookRepository, WebhookDeliveryRepository
        )
        
        delivery_repo = WebhookDeliveryRepository(self.db)
        
        # Verificar que el delivery existe y pertenece al usuario
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT d.*, w.user_id FROM webhook_deliveries d
                JOIN webhooks w ON w.id = d.webhook_id
                WHERE d.id = $1
                """,
                delivery_id
            )
        
        if not row:
            raise ValueError("Delivery not found")
        
        if str(row['user_id']) != user_id:
            raise ValueError("Delivery not found")  # No revelar que existe
        
        # Resetear para retry
        await delivery_repo.reset_for_retry(delivery_id)
        
        logger.info(f"Manual retry queued for delivery {delivery_id}")
        return True
    
    async def close(self):
        """Cerrar cliente HTTP"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# ═══════════════════════════════════════════════════════════════════════════
# WORKER
# ═══════════════════════════════════════════════════════════════════════════

async def run_retry_worker(db, interval: int = 30):
    """
    Worker que procesa reintentos de webhooks.
    
    Args:
        db: DatabaseManager instance
        interval: Segundos entre ciclos
    
    Uso:
        asyncio.create_task(run_retry_worker(db))
    """
    service = WebhookDeliveryService(db)
    
    logger.info("Webhook retry worker started")
    
    while True:
        try:
            processed = await service.process_pending_retries(limit=50)
            
            if processed > 0:
                logger.info(f"Processed {processed} webhook retries")
        
        except Exception as e:
            logger.error(f"Error in webhook retry worker: {e}", exc_info=True)
        
        await asyncio.sleep(interval)
