# sampelit/orchestration/services/segmentation/context_extractor_v2.py

"""
Context Extractor V2 for Segmentation System
Now uses FeatureEngineeringService for professional feature extraction.

BACKWARD COMPATIBLE: Old methods still work, but new code should use V2.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging

# Import new feature engineering
from .feature_engineering_service import FeatureEngineeringService

class ChannelType(str, Enum):
    WEB = "web"
    EMAIL = "email"
    FUNNEL = "funnel"
    API = "api"

class ContextExtractor:
    """
    Context extractor with professional feature engineering
    
    ✅ V2: Uses FeatureEngineeringService (normalized, one-hot encoded, etc.)
    ⚠️  V1: Old methods kept for backward compatibility
    """
    
    def __init__(self, db_pool=None):
        self.logger = logging.getLogger(f"{__name__}.ContextExtractor")
        
        # ✅ NEW: Feature engineering service
        self.feature_service = FeatureEngineeringService(db_pool=db_pool)
        self._initialized = False
    
    async def initialize(self, experiment_id: Optional[str] = None):
        """
        Initialize feature engineering service
        
        Call this once at startup to fit normalizer.
        """
        if not self._initialized:
            await self.feature_service.initialize(
                experiment_id=experiment_id,
                auto_fit=True
            )
            self._initialized = True
            self.logger.info("✅ ContextExtractor initialized with FeatureEngineeringService")
    
    # ========================================================================
    # V2 METHODS (NEW - RECOMMENDED)
    # ========================================================================
    
    async def extract_features_v2(
        self, 
        raw_context: Dict[str, Any],
        user_identifier: Optional[str] = None
    ) -> Dict[str, float]:
        """
        ✅ NEW: Professional feature extraction with normalization
        
        Returns normalized features ready for clustering.
        
        This is the recommended method for new code.
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.feature_service.extract_features(
            raw_context,
            user_identifier=user_identifier
        )
    
    async def get_clustering_vector_v2(
        self,
        raw_context: Dict[str, Any],
        user_identifier: Optional[str] = None
    ) -> List[float]:
        """
        ✅ NEW: Get clustering vector with proper normalization
        
        Returns:
            List of floats ready for K-means
        """
        features = await self.extract_features_v2(raw_context, user_identifier)
        return self.feature_service.get_feature_vector(features)
    
    def get_feature_names_v2(self) -> List[str]:
        """
        ✅ NEW: Get ordered list of feature names
        
        Useful for debugging and visualization.
        """
        return self.feature_service.get_feature_names()
    
    # ========================================================================
    # V1 METHODS (DEPRECATED BUT KEPT FOR BACKWARD COMPATIBILITY)
    # ========================================================================
    
    def extract_features(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️  DEPRECATED: Use extract_features_v2() instead
        
        Kept for backward compatibility.
        """
        self.logger.warning(
            "extract_features() is deprecated. Use extract_features_v2() for better results."
        )
        
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
        ⚠️  DEPRECATED: Use get_clustering_vector_v2() instead
        
        Old method with NO normalization (bad for K-means).
        Kept for backward compatibility only.
        """
        self.logger.warning(
            "get_clustering_vector() is deprecated and has poor normalization. "
            "Use get_clustering_vector_v2() instead."
        )
        
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


# ============================================================================
# MIGRATION HELPER
# ============================================================================

async def migrate_to_v2(extractor: ContextExtractor, experiment_id: Optional[str] = None):
    """
    Migrate existing ContextExtractor to V2
    
    Usage:
        extractor = ContextExtractor()
        await migrate_to_v2(extractor, experiment_id='exp_123')
    """
    await extractor.initialize(experiment_id=experiment_id)
    logging.info("✅ Migrated to ContextExtractor V2")
