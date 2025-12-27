# tests/integration/test_webhooks.py

"""
Tests para el sistema de webhooks.

Ejecutar:
    pytest tests/integration/test_webhooks.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import time

import sys
sys.path.insert(0, '/home/claude/sampelit-webhooks')

from integration.webhooks.models import (
    WebhookEventType, DeliveryStatus,
    WebhookCreate, WebhookUpdate,
    Webhook, WebhookDelivery, WebhookEventBase
)
from integration.webhooks.signatures import (
    generate_secret, sign_payload, verify_signature,
    get_signature_headers
)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_webhook():
    """Webhook de ejemplo para tests"""
    return Webhook(
        id="whk_test123",
        user_id="usr_test456",
        name="Test Webhook",
        url="https://example.com/webhook",
        secret="whsec_abcdef123456",
        events=["experiment.winner_found"],
        experiment_ids=None,
        is_active=True,
        failure_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_triggered_at=None,
        disabled_at=None
    )


@pytest.fixture
def sample_event():
    """Evento de ejemplo"""
    return WebhookEventBase(
        id="evt_test789",
        type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
        created_at=datetime.utcnow(),
        data={
            "experiment": {"id": "exp_123", "name": "Test Experiment"},
            "winner": {"variant_id": "var_456", "confidence": 0.97}
        },
        metadata={"user_id": "usr_test456"}
    )


@pytest.fixture
def sample_payload():
    """Payload JSON de ejemplo"""
    return json.dumps({
        "id": "evt_test",
        "type": "experiment.winner_found",
        "data": {"test": True}
    }).encode('utf-8')


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Signatures
# ═══════════════════════════════════════════════════════════════════════════

class TestSignatures:
    """Tests para el módulo de firmas"""
    
    def test_generate_secret_format(self):
        """Test que el secret tiene el formato correcto"""
        secret = generate_secret()
        
        assert secret.startswith("whsec_")
        assert len(secret) == 70  # whsec_ (6) + 64 hex chars
    
    def test_generate_secret_unique(self):
        """Test que cada secret es único"""
        secrets = [generate_secret() for _ in range(100)]
        unique_secrets = set(secrets)
        
        assert len(unique_secrets) == 100
    
    def test_sign_payload_format(self, sample_payload):
        """Test que la firma tiene el formato correcto"""
        secret = "whsec_test123"
        signature, timestamp = sign_payload(sample_payload, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) == 71  # sha256= (7) + 64 hex chars
        assert isinstance(timestamp, int)
    
    def test_sign_payload_deterministic(self, sample_payload):
        """Test que la firma es determinística con mismo timestamp"""
        secret = "whsec_test123"
        ts = 1234567890
        
        sig1, _ = sign_payload(sample_payload, secret, ts)
        sig2, _ = sign_payload(sample_payload, secret, ts)
        
        assert sig1 == sig2
    
    def test_sign_payload_different_with_different_secret(self, sample_payload):
        """Test que diferentes secrets producen diferentes firmas"""
        ts = 1234567890
        
        sig1, _ = sign_payload(sample_payload, "whsec_secret1", ts)
        sig2, _ = sign_payload(sample_payload, "whsec_secret2", ts)
        
        assert sig1 != sig2
    
    def test_verify_signature_valid(self, sample_payload):
        """Test verificación de firma válida"""
        secret = "whsec_test123"
        signature, timestamp = sign_payload(sample_payload, secret)
        
        is_valid = verify_signature(
            sample_payload,
            signature,
            secret,
            str(timestamp)
        )
        
        assert is_valid is True
    
    def test_verify_signature_invalid_signature(self, sample_payload):
        """Test que firma inválida es rechazada"""
        secret = "whsec_test123"
        _, timestamp = sign_payload(sample_payload, secret)
        
        is_valid = verify_signature(
            sample_payload,
            "sha256=invalid_signature",
            secret,
            str(timestamp)
        )
        
        assert is_valid is False
    
    def test_verify_signature_wrong_secret(self, sample_payload):
        """Test que secret incorrecto es rechazado"""
        secret1 = "whsec_correct"
        secret2 = "whsec_wrong"
        
        signature, timestamp = sign_payload(sample_payload, secret1)
        
        is_valid = verify_signature(
            sample_payload,
            signature,
            secret2,
            str(timestamp)
        )
        
        assert is_valid is False
    
    def test_verify_signature_expired_timestamp(self, sample_payload):
        """Test que timestamp antiguo es rechazado"""
        secret = "whsec_test123"
        old_timestamp = int(time.time()) - 400  # 400 segundos = > 5 min
        
        signature, _ = sign_payload(sample_payload, secret, old_timestamp)
        
        is_valid = verify_signature(
            sample_payload,
            signature,
            secret,
            str(old_timestamp),
            tolerance=300
        )
        
        assert is_valid is False
    
    def test_get_signature_headers(self, sample_payload):
        """Test generación de headers completos"""
        secret = "whsec_test123"
        headers = get_signature_headers(sample_payload, secret)
        
        assert "X-Samplit-Signature" in headers
        assert "X-Samplit-Timestamp" in headers
        assert headers["X-Samplit-Signature"].startswith("sha256=")


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Models
# ═══════════════════════════════════════════════════════════════════════════

class TestModels:
    """Tests para los modelos Pydantic"""
    
    def test_webhook_create_valid(self):
        """Test creación de webhook válido"""
        data = WebhookCreate(
            name="Test Webhook",
            url="https://example.com/hook",
            events=[WebhookEventType.EXPERIMENT_WINNER_FOUND]
        )
        
        assert data.name == "Test Webhook"
        assert data.url == "https://example.com/hook"
        assert len(data.events) == 1
    
    def test_webhook_create_rejects_http(self):
        """Test que HTTP (no HTTPS) es rechazado"""
        with pytest.raises(ValueError) as exc_info:
            WebhookCreate(
                name="Test",
                url="http://example.com/hook",
                events=[WebhookEventType.EXPERIMENT_WINNER_FOUND]
            )
        
        assert "HTTPS" in str(exc_info.value)
    
    def test_webhook_create_rejects_localhost(self):
        """Test que localhost es rechazado"""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="Test",
                url="https://localhost/hook",
                events=[WebhookEventType.EXPERIMENT_WINNER_FOUND]
            )
    
    def test_webhook_create_rejects_127001(self):
        """Test que 127.0.0.1 es rechazado"""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="Test",
                url="https://127.0.0.1/hook",
                events=[WebhookEventType.EXPERIMENT_WINNER_FOUND]
            )
    
    def test_webhook_create_requires_events(self):
        """Test que se requiere al menos un evento"""
        with pytest.raises(ValueError):
            WebhookCreate(
                name="Test",
                url="https://example.com/hook",
                events=[]
            )
    
    def test_webhook_create_deduplicates_events(self):
        """Test que eventos duplicados se eliminan"""
        data = WebhookCreate(
            name="Test",
            url="https://example.com/hook",
            events=[
                WebhookEventType.EXPERIMENT_WINNER_FOUND,
                WebhookEventType.EXPERIMENT_WINNER_FOUND
            ]
        )
        
        assert len(data.events) == 1
    
    def test_webhook_event_base_auto_id(self):
        """Test que los eventos generan ID automáticamente"""
        event = WebhookEventBase(
            type=WebhookEventType.WEBHOOK_TEST,
            data={"test": True}
        )
        
        assert event.id.startswith("evt_")
        assert len(event.id) > 10


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Event Types
# ═══════════════════════════════════════════════════════════════════════════

class TestEventTypes:
    """Tests para los tipos de eventos"""
    
    def test_all_event_types_have_values(self):
        """Test que todos los eventos tienen valores string"""
        for event_type in WebhookEventType:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0
    
    def test_event_type_format(self):
        """Test que el formato es resource.action"""
        for event_type in WebhookEventType:
            parts = event_type.value.split(".")
            assert len(parts) == 2, f"{event_type.value} should have format 'resource.action'"
    
    def test_winner_found_event_value(self):
        """Test valor específico de evento winner_found"""
        assert WebhookEventType.EXPERIMENT_WINNER_FOUND.value == "experiment.winner_found"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Delivery Status
# ═══════════════════════════════════════════════════════════════════════════

class TestDeliveryStatus:
    """Tests para los estados de entrega"""
    
    def test_all_statuses_exist(self):
        """Test que existen todos los estados esperados"""
        expected = ["pending", "success", "failed", "retrying"]
        actual = [s.value for s in DeliveryStatus]
        
        assert sorted(expected) == sorted(actual)
    
    def test_status_values_lowercase(self):
        """Test que los valores son lowercase"""
        for status in DeliveryStatus:
            assert status.value == status.value.lower()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Dispatcher (con mocks)
# ═══════════════════════════════════════════════════════════════════════════

class TestDispatcher:
    """Tests para el EventDispatcher"""
    
    @pytest.mark.asyncio
    async def test_emit_creates_event_id(self):
        """Test que emit genera un event_id"""
        from integration.webhooks.dispatcher import EventDispatcher
        
        mock_db = MagicMock()
        dispatcher = EventDispatcher(mock_db)
        
        # Mock el delivery service
        dispatcher._delivery_service = MagicMock()
        dispatcher._delivery_service.queue_delivery = AsyncMock()
        
        # Mock el webhook repo
        with patch('integration.webhooks.dispatcher.WebhookRepository') as MockRepo:
            mock_repo = MagicMock()
            mock_repo.get_subscribed_webhooks = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo
            
            event_id = await dispatcher.emit(
                event_type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
                user_id="usr_test",
                data={"test": True}
            )
        
        assert event_id.startswith("evt_")
    
    @pytest.mark.asyncio
    async def test_emit_calls_delivery_for_subscribed_webhooks(self, sample_webhook):
        """Test que emit llama a delivery para webhooks suscritos"""
        from integration.webhooks.dispatcher import EventDispatcher
        
        mock_db = MagicMock()
        dispatcher = EventDispatcher(mock_db)
        
        # Mock el delivery service
        mock_delivery = MagicMock()
        mock_delivery.queue_delivery = AsyncMock()
        dispatcher._delivery_service = mock_delivery
        
        # Mock el webhook repo para devolver un webhook
        with patch('integration.webhooks.dispatcher.WebhookRepository') as MockRepo:
            mock_repo = MagicMock()
            mock_repo.get_subscribed_webhooks = AsyncMock(return_value=[sample_webhook])
            MockRepo.return_value = mock_repo
            
            await dispatcher.emit(
                event_type=WebhookEventType.EXPERIMENT_WINNER_FOUND,
                user_id="usr_test456",
                data={"test": True}
            )
        
        # Verificar que se llamó a queue_delivery
        mock_delivery.queue_delivery.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Delivery Service (con mocks)
# ═══════════════════════════════════════════════════════════════════════════

class TestDeliveryService:
    """Tests para WebhookDeliveryService"""
    
    @pytest.mark.asyncio
    async def test_attempt_delivery_success(self, sample_webhook, sample_event):
        """Test entrega exitosa"""
        from integration.webhooks.delivery import WebhookDeliveryService
        
        mock_db = MagicMock()
        service = WebhookDeliveryService(mock_db)
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        service._client = mock_client
        
        delivery = WebhookDelivery(
            id="dlv_test",
            webhook_id=sample_webhook.id,
            event_type=sample_event.type.value,
            event_id=sample_event.id,
            payload={"test": True},
            status=DeliveryStatus.PENDING,
            response_status=None,
            response_body=None,
            error_message=None,
            created_at=datetime.utcnow(),
            delivered_at=None,
            next_retry_at=None,
            attempt_count=0
        )
        
        # Mock repos
        with patch('integration.webhooks.delivery.WebhookRepository') as MockWR, \
             patch('integration.webhooks.delivery.WebhookDeliveryRepository') as MockDR:
            
            mock_delivery_repo = MagicMock()
            mock_delivery_repo.mark_success = AsyncMock()
            MockDR.return_value = mock_delivery_repo
            
            mock_webhook_repo = MagicMock()
            mock_webhook_repo.reset_failure_count = AsyncMock()
            MockWR.return_value = mock_webhook_repo
            
            result = await service.attempt_delivery(delivery, sample_webhook)
        
        assert result is True
        mock_delivery_repo.mark_success.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_attempt_delivery_failure_schedules_retry(self, sample_webhook, sample_event):
        """Test que fallo programa retry"""
        from integration.webhooks.delivery import WebhookDeliveryService
        import httpx
        
        mock_db = MagicMock()
        service = WebhookDeliveryService(mock_db)
        
        # Mock httpx client para simular timeout
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.is_closed = False
        service._client = mock_client
        
        delivery = WebhookDelivery(
            id="dlv_test",
            webhook_id=sample_webhook.id,
            event_type=sample_event.type.value,
            event_id=sample_event.id,
            payload={"test": True},
            status=DeliveryStatus.PENDING,
            response_status=None,
            response_body=None,
            error_message=None,
            created_at=datetime.utcnow(),
            delivered_at=None,
            next_retry_at=None,
            attempt_count=0
        )
        
        # Mock repos
        with patch('integration.webhooks.delivery.WebhookRepository') as MockWR, \
             patch('integration.webhooks.delivery.WebhookDeliveryRepository') as MockDR:
            
            mock_delivery_repo = MagicMock()
            mock_delivery_repo.mark_failed = AsyncMock()
            MockDR.return_value = mock_delivery_repo
            
            mock_webhook_repo = MagicMock()
            mock_webhook_repo.increment_failure_count = AsyncMock(return_value=1)
            MockWR.return_value = mock_webhook_repo
            
            result = await service.attempt_delivery(delivery, sample_webhook)
        
        assert result is False
        mock_delivery_repo.mark_failed.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Integration Flow
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegrationFlow:
    """Tests de flujo completo"""
    
    def test_signature_roundtrip(self):
        """Test ciclo completo de firma y verificación"""
        # Simular servidor enviando
        payload = json.dumps({
            "id": "evt_abc123",
            "type": "experiment.winner_found",
            "data": {"winner": {"variant_id": "var_xyz"}}
        }).encode('utf-8')
        
        secret = generate_secret()
        headers = get_signature_headers(payload, secret)
        
        # Simular receptor verificando
        is_valid = verify_signature(
            payload,
            headers["X-Samplit-Signature"],
            secret,
            headers["X-Samplit-Timestamp"]
        )
        
        assert is_valid is True
    
    def test_tampered_payload_rejected(self):
        """Test que payload modificado es rechazado"""
        original_payload = b'{"amount": 100}'
        tampered_payload = b'{"amount": 999}'
        
        secret = generate_secret()
        signature, timestamp = sign_payload(original_payload, secret)
        
        # Intentar verificar con payload modificado
        is_valid = verify_signature(
            tampered_payload,
            signature,
            secret,
            str(timestamp)
        )
        
        assert is_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
