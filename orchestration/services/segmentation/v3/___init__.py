"""
Context Extractor V3
Extracts and normalizes context from user data, integrating with V2 Feature Engineering.

Key Improvements over Original:
- Uses FeatureEngineeringService from V2 (Fase 2)
- Leverages existing feature normalization
- Consistent with clustering features
- Richer context extraction (15-20 features)

Copyright (c) 2024 Samplit Technologies
"""

import hashlib
import json
from typing import Dict, Any, List, Optional, Set, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextExtractor:
    """
    Extracts and normalizes context from user data
    
    V3 Enhancement: Integrates with FeatureEngineeringService (V2 Fase 2)
    to leverage existing feature extraction and normalization.
    
    Handles:
    - UTM parameters (source, medium, campaign)
    - Device detection (mobile, tablet, desktop)
    - Geographic info (country, region)
    - Temporal context (hour, day_of_week, is_weekend)
    - Behavioral signals (session depth, time on site)
    - User agent parsing
    
    Integration with V2:
        >>> from orchestration.services.segmentation.feature_engineering_service import FeatureEngineeringService
        >>> 
        >>> feature_service = FeatureEngineeringService(db_pool)
        >>> await feature_service.initialize()
        >>> 
        >>> extractor = ContextExtractor(feature_service)
        >>> context = await extractor.extract_async(raw_context)
    """
    
    # Standard context keys (for backward compatibility)
    CONTEXT_KEYS = {
        'source', 'medium', 'campaign',  # UTM
        'device', 'os', 'browser',  # Device
        'country', 'region',  # Geo
        'hour', 'day_of_week', 'is_weekend',  # Temporal
        'session_depth', 'time_on_site',  # Behavioral
    }
    
    def __init__(self, feature_service=None):
        """
        Initialize ContextExtractor
        
        Args:
            feature_service: Optional FeatureEngineeringService from V2
                            If provided, uses V2 feature extraction
                            If None, uses legacy extraction
        """
        self.feature_service = feature_service
        self.logger = logging.getLogger(f"{__name__}.ContextExtractor")
    
    async def extract_async(
        self, 
        raw_context: Dict[str, Any],
        use_v2_features: bool = True
    ) -> Dict[str, Any]:
        """
        Extract and normalize context (async version)
        
        Args:
            raw_context: Raw context dict from request
            use_v2_features: Whether to use V2 feature engineering
        
        Returns:
            Normalized context dict with standard keys
        """
        if use_v2_features and self.feature_service:
            # Use V2 feature engineering
            return await self._extract_with_v2(raw_context)
        else:
            # Use legacy extraction
            return self.extract(raw_context)
    
    async def _extract_with_v2(
        self,
        raw_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract context using V2 FeatureEngineeringService
        
        This leverages the same feature extraction used for clustering,
        ensuring consistency.
        """
        self.logger.debug("Extracting context with V2 feature engineering")
        
        # Extract features using V2 service
        features = await self.feature_service.extract_features(raw_context)
        
        # Convert to standard context format
        # V2 features are already normalized to [0, 1]
        context = {}
        
        # ─────────────────────────────────────────────────────────────
        # Map V2 features to context keys
        # ─────────────────────────────────────────────────────────────
        
        # UTM/Source (one-hot encoded in V2)
        for source in ['google', 'facebook', 'instagram', 'twitter', 'linkedin', 'email', 'direct']:
            key = f'source_{source}'
            if key in features and features[key] > 0.5:
                context['source'] = source
                break
        
        if 'source' not in context:
            context['source'] = 'other'
        
        # Device (one-hot encoded in V2)
        for device in ['mobile', 'tablet', 'desktop']:
            key = f'device_{device}'
            if key in features and features[key] > 0.5:
                context['device'] = device
                break
        
        if 'device' not in context:
            context['device'] = 'unknown'
        
        # Geographic (one-hot encoded in V2)
        for country in ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'ES', 'IT']:
            key = f'country_{country}'
            if key in features and features[key] > 0.5:
                context['country'] = country
                break
        
        if 'country' not in context:
            context['country'] = 'other'
        
        # Behavioral (normalized in V2)
        context['session_depth'] = features.get('session_depth', 0.0)
        context['time_on_site'] = features.get('time_on_site', 0.0)
        context['scroll_depth'] = features.get('scroll_depth', 0.0)
        
        # Temporal (cyclic encoded in V2)
        # Decode from sin/cos back to hour
        if 'hour_sin' in features and 'hour_cos' in features:
            import numpy as np
            hour_sin = features['hour_sin']
            hour_cos = features['hour_cos']
            hour = int(np.arctan2(hour_sin, hour_cos) * 24 / (2 * np.pi))
            if hour < 0:
                hour += 24
            context['hour'] = hour
        
        # Day of week (similar decoding)
        if 'day_sin' in features and 'day_cos' in features:
            import numpy as np
            day_sin = features['day_sin']
            day_cos = features['day_cos']
            day = int(np.arctan2(day_sin, day_cos) * 7 / (2 * np.pi))
            if day < 0:
                day += 7
            context['day_of_week'] = day
            context['is_weekend'] = day >= 5
        
        # User type
        context['is_returning'] = features.get('is_returning', 0.0) > 0.5
        
        self.logger.debug(f"Extracted V2 context: {list(context.keys())}")
        
        return context
    
    @staticmethod
    def extract(raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize context (legacy sync version)
        
        Args:
            raw_context: Raw context dict from request
        
        Returns:
            Normalized context dict with standard keys
        """
        normalized = {}
        
        # ─────────────────────────────────────────────────────────────
        # UTM parameters
        # ─────────────────────────────────────────────────────────────
        normalized['source'] = ContextExtractor._normalize_source(
            raw_context.get('utm_source') or 
            raw_context.get('source') or 
            'direct'
        )
        
        normalized['medium'] = ContextExtractor._normalize_value(
            raw_context.get('utm_medium') or 
            raw_context.get('medium') or 
            'none'
        )
        
        normalized['campaign'] = ContextExtractor._normalize_value(
            raw_context.get('utm_campaign') or 
            raw_context.get('campaign') or 
            'none'
        )
        
        # ─────────────────────────────────────────────────────────────
        # Device detection
        # ─────────────────────────────────────────────────────────────
        user_agent = raw_context.get('user_agent', '')
        normalized['device'] = ContextExtractor._detect_device(user_agent)
        normalized['os'] = ContextExtractor._detect_os(user_agent)
        normalized['browser'] = ContextExtractor._detect_browser(user_agent)
        
        # ─────────────────────────────────────────────────────────────
        # Geographic
        # ─────────────────────────────────────────────────────────────
        normalized['country'] = ContextExtractor._normalize_country(
            raw_context.get('country') or 
            raw_context.get('country_code') or 
            'unknown'
        )
        
        normalized['region'] = ContextExtractor._normalize_value(
            raw_context.get('region') or 
            raw_context.get('state') or 
            'unknown'
        )
        
        # ─────────────────────────────────────────────────────────────
        # Temporal (if timestamp provided)
        # ─────────────────────────────────────────────────────────────
        timestamp = raw_context.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = datetime.now()
            
            normalized['hour'] = timestamp.hour
            normalized['day_of_week'] = timestamp.weekday()
            normalized['is_weekend'] = timestamp.weekday() >= 5
        else:
            # Use current time
            now = datetime.now()
            normalized['hour'] = now.hour
            normalized['day_of_week'] = now.weekday()
            normalized['is_weekend'] = now.weekday() >= 5
        
        # ─────────────────────────────────────────────────────────────
        # Behavioral signals
        # ─────────────────────────────────────────────────────────────
        session = raw_context.get('session', {})
        normalized['session_depth'] = session.get('pages_viewed', 1)
        normalized['time_on_site'] = session.get('time_seconds', 0)
        normalized['scroll_depth'] = session.get('scroll_depth', 0.0)
        
        # User type
        normalized['is_returning'] = raw_context.get('returning_user', False)
        
        return normalized
    
    # ========================================================================
    # NORMALIZATION HELPERS
    # ========================================================================
    
    @staticmethod
    def _normalize_source(source: str) -> str:
        """Normalize source to standard names"""
        source = source.lower().strip()
        
        # Map common variations
        mappings = {
            'google': ['google', 'google.com', 'google.es', 'google.co.uk'],
            'facebook': ['facebook', 'fb', 'facebook.com'],
            'instagram': ['instagram', 'ig', 'instagram.com'],
            'twitter': ['twitter', 'x', 'x.com', 'twitter.com'],
            'linkedin': ['linkedin', 'linkedin.com'],
            'youtube': ['youtube', 'youtube.com'],
            'email': ['email', 'newsletter', 'mail'],
            'direct': ['direct', '(direct)', 'none'],
        }
        
        for standard, variations in mappings.items():
            if source in variations:
                return standard
        
        return 'other'
    
    @staticmethod
    def _normalize_country(country: str) -> str:
        """Normalize country code to ISO 2-letter"""
        country = country.upper().strip()
        
        # Common variations
        mappings = {
            'US': ['US', 'USA', 'UNITED STATES'],
            'UK': ['UK', 'GB', 'UNITED KINGDOM'],
            'CA': ['CA', 'CANADA'],
            'AU': ['AU', 'AUSTRALIA'],
            'DE': ['DE', 'GERMANY', 'DEUTSCHLAND'],
            'FR': ['FR', 'FRANCE'],
            'ES': ['ES', 'SPAIN', 'ESPAÑA'],
            'IT': ['IT', 'ITALY', 'ITALIA'],
        }
        
        for standard, variations in mappings.items():
            if country in variations:
                return standard
        
        return country[:2] if len(country) >= 2 else 'XX'
    
    @staticmethod
    def _normalize_value(value: str) -> str:
        """Generic value normalization"""
        return value.lower().strip() if value else 'unknown'
    
    @staticmethod
    def _detect_device(user_agent: str) -> str:
        """Detect device type from user agent"""
        ua = user_agent.lower()
        
        # Mobile indicators
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
        if any(keyword in ua for keyword in mobile_keywords):
            return 'mobile'
        
        # Tablet indicators
        tablet_keywords = ['tablet', 'ipad', 'kindle', 'playbook']
        if any(keyword in ua for keyword in tablet_keywords):
            return 'tablet'
        
        # Default to desktop
        return 'desktop'
    
    @staticmethod
    def _detect_os(user_agent: str) -> str:
        """Detect OS from user agent"""
        ua = user_agent.lower()
        
        if 'windows' in ua:
            return 'windows'
        elif 'mac' in ua or 'macos' in ua:
            return 'macos'
        elif 'linux' in ua:
            return 'linux'
        elif 'android' in ua:
            return 'android'
        elif 'ios' in ua or 'iphone' in ua or 'ipad' in ua:
            return 'ios'
        
        return 'unknown'
    
    @staticmethod
    def _detect_browser(user_agent: str) -> str:
        """Detect browser from user agent"""
        ua = user_agent.lower()
        
        # Order matters - check more specific first
        if 'edg' in ua or 'edge' in ua:
            return 'edge'
        elif 'chrome' in ua:
            return 'chrome'
        elif 'firefox' in ua:
            return 'firefox'
        elif 'safari' in ua:
            return 'safari'
        elif 'opera' in ua or 'opr' in ua:
            return 'opera'
        
        return 'unknown'
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    @staticmethod
    def build_segment_key(
        context: Dict[str, Any],
        features: List[str]
    ) -> str:
        """
        Build segment key from context
        
        Example:
            context = {'source': 'instagram', 'device': 'mobile', 'country': 'ES'}
            features = ['source', 'device']
            → 'device:mobile|source:instagram'
        
        Args:
            context: Normalized context dict
            features: List of feature keys to include
        
        Returns:
            Segment key string
        """
        if not features:
            return 'global'
        
        # Build key from selected features (sorted for consistency)
        parts = []
        for feature in sorted(features):
            value = context.get(feature, 'unknown')
            parts.append(f"{feature}:{value}")
        
        return '|'.join(parts)
    
    @staticmethod
    def parse_segment_key(segment_key: str) -> Dict[str, str]:
        """
        Parse segment key back to context dict
        
        Example:
            'device:mobile|source:instagram' 
            → {'device': 'mobile', 'source': 'instagram'}
        
        Args:
            segment_key: Segment key string
        
        Returns:
            Dict of feature -> value
        """
        if segment_key == 'global':
            return {}
        
        result = {}
        for part in segment_key.split('|'):
            if ':' in part:
                key, value = part.split(':', 1)
                result[key] = value
        
        return result
    
    @staticmethod
    def get_context_hash(context: Dict[str, Any]) -> str:
        """
        Generate deterministic hash of context
        
        Useful for caching and deduplication.
        """
        # Sort keys for deterministic hash
        sorted_items = sorted(context.items())
        context_str = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
