# public-api/models/experiment_models.py

"""
Modelos Unificados - Todo es Multi-Elemento

Simplificación: eliminamos la distinción entre "traditional" y "multi-element"
TODO es multi-elemento, solo que algunos experimentos tienen 1 elemento y otros varios.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ElementType(str, Enum):
    TEXT = "text"
    BUTTON = "button"
    HEADLINE = "headline"
    IMAGE = "image"
    LINK = "link"
    FORM = "form"
    SECTION = "section"
    GENERIC = "generic"

class SelectorType(str, Enum):
    CSS = "css"
    XPATH = "xpath"
    ID = "id"
    CLASS = "class"

# ============================================
# SELECTOR & ELEMENT CONFIG
# ============================================

class SelectorConfig(BaseModel):
    """Cómo encontrar el elemento en la página"""
    type: SelectorType
    selector: str
    fallback_selectors: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "css",
                "selector": "#hero-cta",
                "fallback_selectors": [".cta-button", "[data-test='cta']"]
            }
        }
    )

class VariantContent(BaseModel):
    """Contenido de una variante"""
    text: Optional[str] = None
    html: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    styles: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Get Started Free",
                "styles": {"background": "#FF5733", "color": "white"}
            }
        }
    )

class ElementConfig(BaseModel):
    """Configuración de un elemento testeable"""
    name: str = Field(..., description="Nombre descriptivo del elemento")
    selector: SelectorConfig
    element_type: ElementType
    original_content: VariantContent
    variants: List[VariantContent] = Field(..., min_length=1)
    
    @field_validator('variants')
    @classmethod
    def validate_variants(cls, v):
        if len(v) < 1:
            raise ValueError('Necesitas al menos 1 variante')
        return v

    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Hero CTA Button",
                "selector": {
                    "type": "css",
                    "selector": "#hero-cta"
                },
                "element_type": "button",
                "original_content": {
                    "text": "Sign Up"
                },
                "variants": [
                    {"text": "Get Started Free"},
                    {"text": "Try it Now"},
                    {"text": "Start Your Trial"}
                ]
            }
        }
    )

# ============================================
# EXPERIMENT REQUESTS
# ============================================

class CreateExperimentRequest(BaseModel):
    """Crear experimento - TODO es multi-elemento"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., description="URL donde corre el experimento")
    
    # Elementos a testear (1 o más)
    elements: List[ElementConfig] = Field(..., min_length=1)
    
    # Configuración opcional
    traffic_allocation: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_threshold: float = Field(default=0.95, ge=0.8, le=0.99)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL debe empezar con http:// o https://')
        return v

    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Homepage CTA Test",
                "description": "Testing different CTA button texts",
                "url": "https://mysite.com",
                "elements": [
                    {
                        "name": "Main CTA",
                        "selector": {"type": "css", "selector": "#main-cta"},
                        "element_type": "button",
                        "original_content": {"text": "Sign Up"},
                        "variants": [
                            {"text": "Get Started Free"},
                            {"text": "Try it Now"}
                        ]
                    }
                ]
            }
        }
    )

class UpdateExperimentRequest(BaseModel):
    """Actualizar experimento"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    traffic_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)


# ============================================
# EXPERIMENT RESPONSES
# ============================================

class DailyStat(BaseModel):
    """Estadísticas diarias para gráficos"""
    date: str
    variant_stats: List[Dict[str, Any]]  # [{name, conversion_rate, conversions}]

class TrafficStats(BaseModel):
    """Estadísticas por fuente de tráfico"""
    source: str  # mobile, desktop, direct, social, etc
    visitors: int
    conversion_rate: float

class VariantPerformance(BaseModel):
    """Performance de una variante de un elemento"""
    variant_index: int
    content: VariantContent
    allocations: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    confidence_score: float = 0.0
    uplift: float = 0.0 # Added for convenience

class ElementPerformance(BaseModel):
    """Performance de un elemento completo"""
    element_id: str
    name: str
    element_type: ElementType
    variants: List[VariantPerformance]
    best_variant_index: Optional[int] = None
    statistical_significance: bool = False
    bayesian_stats: Optional[Dict[str, Any]] = None
    daily_stats: Optional[List[Dict[str, Any]]] = None
    traffic_breakdown: Optional[List[TrafficStats]] = None

class ExperimentListResponse(BaseModel):
    """Respuesta de lista de experimentos"""
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    url: str
    created_at: datetime
    started_at: Optional[datetime]
    
    # Stats agregadas
    variant_count: int
    total_visitors: int = 0
    overall_conversion_rate: float = 0.0

class ExperimentDetailResponse(BaseModel):
    """Respuesta detallada de experimento"""
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    url: str
    traffic_allocation: float
    confidence_threshold: float
    created_at: datetime
    started_at: Optional[datetime]
    
    # Elementos con performance
    elements: List[ElementPerformance]
    
    # Stats generales
    total_visitors: int = 0
    total_conversions: int = 0
    overall_conversion_rate: float = 0.0

# ============================================
# ASSIGNMENT (para el SDK/GTM)
# ============================================

class AssignmentRequest(BaseModel):
    """Request de asignación (desde SDK)"""
    experiment_id: str
    user_id: str = Field(..., description="ID único del usuario/visitante")
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ElementAssignment(BaseModel):
    """Asignación de un elemento"""
    element_id: str
    element_name: str
    variant_index: int
    content: VariantContent
    selector: SelectorConfig

class AssignmentResponse(BaseModel):
    """Respuesta con asignaciones para todos los elementos"""
    experiment_id: str
    assignments: List[ElementAssignment]
    new_assignment: bool

# ============================================
# CONVERSION
# ============================================

class ConversionRequest(BaseModel):
    """Registrar conversión"""
    experiment_id: str
    user_id: str
    conversion_value: float = Field(default=1.0, ge=0)
    metadata: Optional[Dict[str, Any]] = None

class ConversionResponse(BaseModel):
    """Respuesta de conversión"""
    success: bool
    message: str

# ============================================
# ANALYTICS
# ============================================

class BayesianInsights(BaseModel):
    """Insights Bayesianos"""
    best_variant: Optional[str] = None
    confidence: float = 0.0
    threshold_met: bool = False
    recommendation: str

class ExperimentAnalytics(BaseModel):
    """Analytics completas del experimento"""
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    
    elements: List[ElementPerformance]
    
    # Stats globales
    total_visitors: int
    total_conversions: int
    overall_conversion_rate: float
    
    # Insights
    bayesian_insights: Optional[BayesianInsights] = None
    recommendations: List[str] = []
    
    # Timeline
    created_at: datetime
    started_at: Optional[datetime]
    runtime_hours: Optional[float] = None
