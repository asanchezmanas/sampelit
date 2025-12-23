"""
Context Extractor for Segmentation System
Handles normalization and feature extraction from different sources.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging

class ChannelType(str, Enum):
    WEB = "web"
    EMAIL = "email"
    FUNNEL = "funnel"
    API = "api"

class ContextExtractor:
    """
    Extracts and normalizes features from raw request/visitor context.
    Prepares data for clustering and segmentation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ContextExtractor")

    def extract_features(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for feature extraction.
        """
        features = {
            "channel": self._detect_channel(raw_context),
            "device": self._normalize_device(raw_context.get("user_agent", "")),
            "region": raw_context.get("geo", {}).get("country", "unknown"),
            "behavioral": self._extract_behavioral_metrics(raw_context),
            "technical": self._extract_technical_features(raw_context)
        }
        return features

    def _detect_channel(self, context: Dict[str, Any]) -> ChannelType:
        """Detects the interaction channel."""
        if "email_id" in context or "campaign" in context:
            return ChannelType.EMAIL
        if "step_id" in context:
            return ChannelType.FUNNEL
        return ChannelType.WEB

    def _normalize_device(self, ua: str) -> str:
        """Simple device normalization."""
        ua = ua.lower()
        if "mobile" in ua: return "mobile"
        if "tablet" in ua or "ipad" in ua: return "tablet"
        return "desktop"

    def _extract_behavioral_metrics(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extracts numerical features for K-means."""
        return {
            "session_depth": float(context.get("pages_viewed", 1)),
            "time_on_site": float(context.get("time_seconds", 0)),
            "is_returning": 1.0 if context.get("returning_user") else 0.0
        }

    def _extract_technical_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Technical metadata."""
        return {
            "encoding": context.get("encoding", "utf-8"),
            "language": context.get("lang", "en")[:2]
        }

    def get_clustering_vector(self, features: Dict[str, Any]) -> List[float]:
        """
        Converts normalized features into a numerical vector for K-means.
        """
        b = features.get("behavioral", {})
        # Vector: [session_depth, time_on_site, is_returning, channel_encoded]
        channel_map = {ChannelType.WEB: 0, ChannelType.EMAIL: 1, ChannelType.FUNNEL: 2, ChannelType.API: 3}
        channel_val = channel_map.get(features.get("channel", ChannelType.WEB), 0)
        
        return [
            float(b.get("session_depth", 1)),
            float(b.get("time_on_site", 0)),
            float(b.get("is_returning", 0)),
            float(channel_val)
        ]
