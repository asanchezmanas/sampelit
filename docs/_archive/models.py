# integration/webhooks/models.py

"""
Modelos Pydantic para el sistema de webhooks.
Define eventos, payloads, y schemas de API.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class WebhookEventType(str, Enum):
    """Tipos de eventos soportados"""
    # Experimentos
    EXPERIMENT_CREATED = "experiment.created"
    EXPERIMENT_STARTED = "experiment.started"
    EXPERIMENT_PAUSED = "experiment.paused"
    EXPERIMENT_STOPPED = "experiment.stopped"
    EXPERIMENT_SIGNIFICANCE_REACHED = "experiment.significance_reached"
    EXPERIMENT_WINNER_FOUND = "experiment.winner_found"
    EXPERIMENT_TRAFFIC_LOW = "experiment.traffic_low"
    
    # Conversiones (alto volumen, opt-in)
    CONVERSION_RECORDED = "conversion.recorded"
    
    # Sistema
    WEBHOOK_TEST = "webhook.test"


class DeliveryStatus(str, Enum):
    """Estados de entrega de webhook"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


# Lista de eventos "seguros" (bajo volumen)
SAFE_EVENTS = [
    WebhookEventType.EXPERIMENT_CREATED,
    WebhookEventType.EXPERIMENT_STARTED,
    WebhookEventType.EXPERIMENT_PAUSED,
    WebhookEventType.EXPERIMENT_STOPPED,
    WebhookEventType.EXPERIMENT_SIGNIFICANCE_REACHED,
    WebhookEventType.EXPERIMENT_WINNER_FOUND,
    WebhookEventType.EXPERIMENT_TRAFFIC_LOW,
    WebhookEventType.WEBHOOK_TEST,
]

# Eventos de alto volumen (requieren confirmación)
HIGH_VOLUME_EVENTS = [
    WebhookEventType.CONVERSION_RECORDED,
]


# ═══════════════════════════════════════════════════════════════════════════
# EVENT PAYLOADS
# ═══════════════════════════════════════════════════════════════════════════

class ExperimentData(BaseModel):
    """Datos de experimento incluidos en eventos"""
    id: str
    name: str
    url: Optional[str] = None
    status: str
    created_at: datetime


class VariantData(BaseModel):
    """Datos de variante"""
    id: str
    name: str
    is_control: bool = False


class WinnerData(BaseModel):
    """Datos del ganador de un experimento"""
    variant_id: str
    variant_name: str
    confidence: float = Field(ge=0, le=1)
    improvement: float  # Porcentaje de mejora vs control


class StatisticsData(BaseModel):
    """Estadísticas del experimento"""
    total_visitors: int
    total_conversions: int
    conversion_rate: float
    duration_days: int
    confidence: float


class ConversionData(BaseModel):
    """Datos de conversión"""
    id: str
    experiment_id: str
    variant_id: str
    user_identifier: str
    value: Optional[float] = None
    recorded_at: datetime


# ═══════════════════════════════════════════════════════════════════════════
# EVENT MODELS
# ═══════════════════════════════════════════════════════════════════════════

class WebhookEventBase(BaseModel):
    """Base para todos los eventos de webhook"""
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: WebhookEventType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExperimentCreatedEvent(WebhookEventBase):
    """Evento: Experimento creado"""
    type: Literal[WebhookEventType.EXPERIMENT_CREATED] = WebhookEventType.EXPERIMENT_CREATED
    data: Dict[str, Any]  # {"experiment": ExperimentData}


class ExperimentWinnerFoundEvent(WebhookEventBase):
    """Evento: Ganador identificado"""
    type: Literal[WebhookEventType.EXPERIMENT_WINNER_FOUND] = WebhookEventType.EXPERIMENT_WINNER_FOUND
    data: Dict[str, Any]  # {"experiment": ..., "winner": ..., "statistics": ...}


class WebhookTestEvent(WebhookEventBase):
    """Evento de prueba"""
    type: Literal[WebhookEventType.WEBHOOK_TEST] = WebhookEventType.WEBHOOK_TEST
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "message": "This is a test event from Samplit",
        "timestamp": datetime.utcnow().isoformat()
    })


# ═══════════════════════════════════════════════════════════════════════════
# API MODELS
# ═══════════════════════════════════════════════════════════════════════════

class WebhookCreate(BaseModel):
    """Request para crear webhook"""
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=10, max_length=2000)
    events: List[WebhookEventType] = Field(min_length=1)
    experiment_ids: Optional[List[str]] = None  # None = todos
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validar que sea HTTPS y no sea localhost"""
        if not v.startswith('https://'):
            raise ValueError('Only HTTPS URLs are allowed')
        
        # Validar que no sea localhost
        lower = v.lower()
        forbidden = ['localhost', '127.0.0.1', '0.0.0.0', '.local']
        if any(f in lower for f in forbidden):
            raise ValueError('Localhost and local URLs are not allowed')
        
        return v
    
    @field_validator('events')
    @classmethod
    def validate_events(cls, v: List[WebhookEventType]) -> List[WebhookEventType]:
        """Validar eventos"""
        if not v:
            raise ValueError('At least one event must be selected')
        return list(set(v))  # Eliminar duplicados


class WebhookUpdate(BaseModel):
    """Request para actualizar webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=10, max_length=2000)
    events: Optional[List[WebhookEventType]] = None
    experiment_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith('https://'):
            raise ValueError('Only HTTPS URLs are allowed')
        lower = v.lower()
        forbidden = ['localhost', '127.0.0.1', '0.0.0.0', '.local']
        if any(f in lower for f in forbidden):
            raise ValueError('Localhost and local URLs are not allowed')
        return v


class WebhookResponse(BaseModel):
    """Response de webhook"""
    id: str
    name: str
    url: str
    secret: str  # Solo se muestra al crear
    events: List[str]
    experiment_ids: Optional[List[str]]
    is_active: bool
    failure_count: int
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Response de listado"""
    id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    failure_count: int
    last_triggered_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    """Response de entrega"""
    id: str
    webhook_id: str
    event_type: str
    event_id: str
    status: DeliveryStatus
    response_status: Optional[int]
    error_message: Optional[str]
    attempt_count: int
    created_at: datetime
    delivered_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL MODELS
# ═══════════════════════════════════════════════════════════════════════════

class Webhook(BaseModel):
    """Modelo interno de webhook"""
    id: str
    user_id: str
    name: str
    url: str
    secret: str
    events: List[str]
    experiment_ids: Optional[List[str]]
    is_active: bool
    failure_count: int
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
    disabled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WebhookDelivery(BaseModel):
    """Modelo interno de entrega"""
    id: str
    webhook_id: str
    event_type: str
    event_id: str
    payload: Dict[str, Any]
    status: DeliveryStatus
    response_status: Optional[int]
    response_body: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    attempt_count: int
    
    class Config:
        from_attributes = True
