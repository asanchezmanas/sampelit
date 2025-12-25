# public-api/models/multi_element_models.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum

class OptimizationProtocol(str, Enum):
    """Orchestration protocols for high-dimensional testing"""
    INDEPENDENT = "independent"  # Atomic element optimization (Highest efficiency)
    FACTORIAL = "factorial"      # Interaction-aware matrix testing (Full coverage)

class SelectorSpec(BaseModel):
    """CSS/XPath target specification"""
    type: str = Field(..., pattern="^(css|xpath)$")
    query: str = Field(..., min_length=1)

class ContentPayload(BaseModel):
    """Variant content delivery package"""
    html: Optional[str] = None
    text: Optional[str] = None
    css: Optional[Dict[str, str]] = None
    attrs: Optional[Dict[str, str]] = None

class ElementSpec(BaseModel):
    """Specification for a single architectural component under test"""
    name: str = Field(..., min_length=1, max_length=255)
    selector: SelectorSpec
    category: str = Field(..., pattern="^(text|image|button|div|section|other)$")
    variations: List[ContentPayload] = Field(..., min_length=2)

class MultiElementOrchestrationRequest(BaseModel):
    """Full orchestration request for high-dimensional experiments"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    elements: List[ElementSpec] = Field(..., min_length=1)
    protocol: OptimizationProtocol = OptimizationProtocol.INDEPENDENT
    target_url: str = Field(..., min_length=1)
    allocation: float = Field(1.0, ge=0.0, le=1.0)

class CombinationPerformance(BaseModel):
    """Metrics for a specific element combination"""
    combination_id: str
    element_values: Dict[str, str]
    allocations: int
    conversions: int
    conversion_rate: float
    traffic_percentage: float
    is_winning: bool = False

class MultiElementStatusResponse(BaseModel):
    """Detailed real-time status of a high-dimensional experiment"""
    experiment_id: str
    name: str
    protocol: OptimizationProtocol
    total_combinations: int
    total_allocations: int
    total_conversions: int
    combinations: List[CombinationPerformance]

class MultiElementConversionRequest(BaseModel):
    """Direct conversion recording for multi-element orchestrations"""
    experiment_id: str
    user_identifier: str
    combination_id: str
    value: float = 0.0
