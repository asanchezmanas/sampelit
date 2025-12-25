# public-api/models/funnel_models.py
"""
Funnel System Models - Tree-based conversion paths with bandit optimization.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class FunnelStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NodeType(str, Enum):
    PAGE = "page"
    ACTION = "action"
    DECISION = "decision"
    EMAIL = "email"
    WAIT = "wait"


class ConversionType(str, Enum):
    URL = "url"
    EVENT = "event"
    CUSTOM = "custom"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CONVERTED = "converted"
    ABANDONED = "abandoned"
    TIMEOUT = "timeout"


class EdgeConditionType(str, Enum):
    ALWAYS = "always"
    VARIANT = "variant"
    SEGMENT = "segment"
    CUSTOM = "custom"


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSION GOAL CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

class ConversionGoalConfig(BaseModel):
    """Configuration for how conversion is detected."""
    url_pattern: Optional[str] = None  # "/thank-you" or regex
    event_name: Optional[str] = None   # "purchase", "signup"
    value_selector: Optional[str] = None  # CSS selector to extract value
    
    model_config = ConfigDict(extra="allow")


# ═══════════════════════════════════════════════════════════════════════════════
# NODE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class NodeConfig(BaseModel):
    """Configuration for a funnel node."""
    url_match: Optional[str] = None  # Page URL pattern
    wait_seconds: Optional[int] = None  # For wait nodes
    trigger_event: Optional[str] = None  # For action nodes
    email_template_id: Optional[str] = None  # For email nodes
    email_delay_minutes: Optional[int] = 0  # Delay before sending
    
    model_config = ConfigDict(extra="allow")


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class CreateFunnelRequest(BaseModel):
    """Create a new funnel."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    conversion_type: ConversionType = ConversionType.URL
    conversion_config: Optional[ConversionGoalConfig] = None
    session_timeout_hours: int = Field(default=168, ge=1, le=720)  # 168 = 7 days


class UpdateFunnelRequest(BaseModel):
    """Update funnel settings."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    conversion_type: Optional[ConversionType] = None
    conversion_config: Optional[ConversionGoalConfig] = None
    session_timeout_hours: Optional[int] = Field(None, ge=1, le=720)
    status: Optional[FunnelStatus] = None


class CreateNodeRequest(BaseModel):
    """Create a node in a funnel."""
    name: str = Field(..., min_length=1, max_length=255)
    node_type: NodeType
    parent_node_id: Optional[str] = None  # None = root node
    config: Optional[NodeConfig] = None
    is_conversion_node: bool = False
    is_entry_node: bool = False
    position_x: int = 0
    position_y: int = 0


class UpdateNodeRequest(BaseModel):
    """Update a node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    node_type: Optional[NodeType] = None
    parent_node_id: Optional[str] = None
    config: Optional[NodeConfig] = None
    is_conversion_node: Optional[bool] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None


class CreateEdgeRequest(BaseModel):
    """Create an edge between nodes."""
    from_node_id: str
    to_node_id: str
    condition_type: EdgeConditionType = EdgeConditionType.ALWAYS
    condition_config: Optional[Dict[str, Any]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class FunnelNodeResponse(BaseModel):
    """Response for a single node."""
    id: str
    funnel_id: str
    name: str
    node_type: NodeType
    node_order: int
    parent_node_id: Optional[str] = None
    experiment_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_conversion_node: bool
    is_entry_node: bool
    position_x: int
    position_y: int
    created_at: datetime


class FunnelEdgeResponse(BaseModel):
    """Response for an edge."""
    id: str
    funnel_id: str
    from_node_id: str
    to_node_id: str
    condition_type: EdgeConditionType
    condition_config: Optional[Dict[str, Any]] = None
    total_traversals: int
    successful_conversions: int
    created_at: datetime


class FunnelResponse(BaseModel):
    """Full funnel response with nodes and edges."""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    conversion_type: ConversionType
    conversion_config: Optional[Dict[str, Any]] = None
    session_timeout_hours: int
    status: FunnelStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    
    # Nested data
    nodes: Optional[List[FunnelNodeResponse]] = None
    edges: Optional[List[FunnelEdgeResponse]] = None
    
    # Stats
    total_sessions: Optional[int] = None
    conversion_rate: Optional[float] = None


class FunnelListResponse(BaseModel):
    """List item for funnels."""
    id: str
    name: str
    description: Optional[str] = None
    status: FunnelStatus
    node_count: int = 0
    total_sessions: int = 0
    conversion_rate: float = 0.0
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# TRACKER MODELS (SDK)
# ═══════════════════════════════════════════════════════════════════════════════

class FunnelEnterRequest(BaseModel):
    """User enters a funnel."""
    installation_token: str
    funnel_id: str
    user_identifier: str
    session_id: Optional[str] = None
    entry_node_id: Optional[str] = None  # Defaults to root
    metadata: Optional[Dict[str, Any]] = None


class FunnelStepRequest(BaseModel):
    """User moves to next step in funnel."""
    installation_token: str
    funnel_id: str
    user_identifier: str
    node_id: str
    variant_id: Optional[str] = None  # If A/B tested
    metadata: Optional[Dict[str, Any]] = None


class FunnelConvertRequest(BaseModel):
    """Conversion detected in funnel."""
    installation_token: str
    funnel_id: str
    user_identifier: str
    conversion_value: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class FunnelSessionResponse(BaseModel):
    """User's funnel session state."""
    session_id: str
    funnel_id: str
    current_node_id: Optional[str] = None
    path: List[Dict[str, Any]]
    status: SessionStatus
    started_at: datetime
    conversion_value: Optional[float] = None
