# sampelit/orchestration/services/feature_engineering_service.py

"""
Feature Engineering Service
Orchestrates feature extraction, normalization, and caching.

Copyright (c) 2024 Samplit Technologies
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging
from datetime import datetime, timedelta
import hashlib
import json

from .feature_normalizer import FeatureNormalizer, FeatureDefinition, FeatureType

logger = logging.getLogger(__name__)


class FeatureEngineeringService:
    """
    High-level service for feature engineering
    
    Responsibilities:
    1. Extract raw features from context
    2. Enrich with derived features
    3. Normalize using FeatureNormalizer
    4. Cache computed features
    5. Handle missing values intelligently
    
    Example:
        >>> service = FeatureEngineeringService()
        >>> await service.initialize()
        >>> 
        >>> raw_context = {
        ...     'user_agent': 'Mozilla/5.0 (iPhone...)',
        ...     'geo': {'country': 'US', 'region': 'CA'},
        ...     'session': {'pages_viewed': 5, 'time_seconds': 120},
        ...     'referrer': 'https://google.com',
        ...     'timestamp': '2024-12-24T14:30:00Z'
        ... }
        >>> 
        >>> features = await service.extract_features(raw_context)
        >>> vector = service.get_feature_vector(features)
    """
    
    def __init__(self, db_pool=None, enable_cache: bool = True):
        self.db = db_pool
        self.enable_cache = enable_cache
        
        # Feature normalizer (will be fitted)
        self.normalizer = FeatureNormalizer()
        
        # Cache for computed features (in-memory)
        self._feature_cache: Dict[str, Dict[str, float]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)
        
        self.logger = logging.getLogger(f"{__name__}.FeatureEngineeringService")
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    async def initialize(
        self,
        experiment_id: Optional[UUID] = None,
        auto_fit: bool = True
    ) -> None:
        """
        Initialize service and fit normalizer
        
        Args:
            experiment_id: If provided, fit on historical data from this experiment
            auto_fit: If True, fit normalizer on available data
        """
        self.logger.info("Initializing FeatureEngineeringService")
        
        # Define features
        self.normalizer.add_default_web_features()
        
        # Fit normalizer if requested
        if auto_fit:
            if experiment_id and self.db:
                await self._fit_on_experiment_data(experiment_id)
            else:
                # Fit on synthetic data (for testing/demo)
                self._fit_on_defaults()
        
        self.logger.info("✅ FeatureEngineeringService initialized")
    
    async def _fit_on_experiment_data(self, experiment_id: UUID) -> None:
        """
        Fit normalizer on historical experiment data
        
        This learns the actual distribution of features in your traffic.
        """
        self.logger.info(f"Fitting normalizer on experiment {experiment_id} data")
        
        async with self.db.acquire() as conn:
            # Get historical contexts from assignments
            rows = await conn.fetch(
                """
                SELECT context
                FROM assignments
                WHERE experiment_id = $1
                  AND context IS NOT NULL
                  AND assigned_at > NOW() - INTERVAL '30 days'
                LIMIT 10000
                """,
                experiment_id
            )
        
        if not rows:
            self.logger.warning("No historical data found, using defaults")
            self._fit_on_defaults()
            return
        
        # Parse contexts
        raw_contexts = []
        for row in rows:
            try:
                if isinstance(row['context'], str):
                    context = json.loads(row['context'])
                else:
                    context = row['context']
                raw_contexts.append(context)
            except Exception as e:
                self.logger.warning(f"Failed to parse context: {e}")
                continue
        
        if raw_contexts:
            # Extract features and fit
            extracted = [
                self._extract_raw_features(ctx) 
                for ctx in raw_contexts
            ]
            self.normalizer.fit(extracted)
            self.logger.info(f"✅ Fitted on {len(extracted)} samples")
        else:
            self._fit_on_defaults()
    
    def _fit_on_defaults(self) -> None:
        """
        Fit on reasonable default values
        
        Used when no historical data is available.
        """
        self.logger.info("Fitting normalizer on default ranges")
        
        # Generate synthetic samples covering typical ranges
        synthetic_samples = []
        
        for pages in [1, 3, 5, 10, 20, 50]:
            for time_seconds in [0, 30, 60, 120, 300, 600]:
                for device in ['mobile', 'tablet', 'desktop']:
                    for country in ['US', 'UK', 'CA', 'other']:
                        for hour in range(0, 24, 6):
                            sample = {
                                'pages_viewed': pages,
                                'time_seconds': time_seconds,
                                'device': device,
                                'country': country,
                                'hour_of_day': hour,
                                'day_of_week': 1,
                                'returning_user': False,
                                'scroll_depth': 75.0,
                                'utm_source': 'direct'
                            }
                            synthetic_samples.append(sample)
        
        self.normalizer.fit(synthetic_samples)
        self.logger.info(f"✅ Fitted on {len(synthetic_samples)} synthetic samples")
    
    # ========================================================================
    # FEATURE EXTRACTION
    # ========================================================================
    
    async def extract_features(
        self,
        raw_context: Dict[str, Any],
        user_identifier: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Extract and normalize features from raw context
        
        This is the main entry point for feature engineering.
        
        Args:
            raw_context: Raw context from tracker/request
            user_identifier: Optional user ID for caching
            
        Returns:
            Dictionary of normalized features ready for clustering
        """
        # Check cache
        if user_identifier and self.enable_cache:
            cached = self._get_from_cache(user_identifier)
            if cached:
                self.logger.debug(f"Cache hit for user {user_identifier}")
                return cached
        
        # Extract raw features
        raw_features = self._extract_raw_features(raw_context)
        
        # Normalize
        normalized = self.normalizer.transform(raw_features)
        
        # Cache result
        if user_identifier and self.enable_cache:
            self._save_to_cache(user_identifier, normalized)
        
        return normalized
    
    def _extract_raw_features(self, raw_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract raw features from context
        
        This method enriches the context with derived features.
        """
        features = {}
        
        # ─────────────────────────────────────────────────────────────────
        # BEHAVIORAL FEATURES
        # ─────────────────────────────────────────────────────────────────
        
        # Pages viewed
        features['pages_viewed'] = self._safe_extract(
            raw_context, ['session', 'pages_viewed'], default=1
        )
        
        # Time on site
        features['time_seconds'] = self._safe_extract(
            raw_context, ['session', 'time_seconds'], default=0
        )
        
        # Scroll depth
        features['scroll_depth'] = self._safe_extract(
            raw_context, ['session', 'scroll_depth'], default=0
        )
        
        # Returning user
        features['returning_user'] = self._safe_extract(
            raw_context, ['returning_user'], default=False
        )
        
        # ─────────────────────────────────────────────────────────────────
        # DEVICE & TECHNICAL
        # ─────────────────────────────────────────────────────────────────
        
        # Device type (parsed from user_agent or explicit)
        features['device'] = self._extract_device(raw_context)
        
        # ─────────────────────────────────────────────────────────────────
        # GEOGRAPHIC
        # ─────────────────────────────────────────────────────────────────
        
        # Country
        features['country'] = self._safe_extract(
            raw_context, ['geo', 'country'], default='other'
        )
        
        # Normalize country codes
        country = features['country'].upper()
        if country not in ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'ES', 'IT']:
            features['country'] = 'other'
        else:
            features['country'] = country
        
        # ─────────────────────────────────────────────────────────────────
        # TEMPORAL FEATURES
        # ─────────────────────────────────────────────────────────────────
        
        # Hour of day and day of week (from timestamp or current time)
        timestamp = self._safe_extract(
            raw_context, ['timestamp'], default=None
        )
        
        if timestamp:
            dt = self._parse_timestamp(timestamp)
        else:
            dt = datetime.utcnow()
        
        features['hour_of_day'] = dt.hour
        features['day_of_week'] = dt.weekday()  # 0=Monday, 6=Sunday
        
        # ─────────────────────────────────────────────────────────────────
        # TRAFFIC SOURCE
        # ─────────────────────────────────────────────────────────────────
        
        # UTM source
        utm_source = self._safe_extract(
            raw_context, ['utm_source'], default='direct'
        )
        
        # Normalize traffic sources
        utm_source_lower = utm_source.lower()
        
        known_sources = ['google', 'facebook', 'twitter', 'linkedin', 'email', 'direct']
        
        if any(src in utm_source_lower for src in known_sources):
            for src in known_sources:
                if src in utm_source_lower:
                    features['utm_source'] = src
                    break
        else:
            features['utm_source'] = 'other'
        
        return features
    
    def _extract_device(self, raw_context: Dict[str, Any]) -> str:
        """
        Extract device type from user_agent or explicit field
        """
        # Check explicit device field
        device = self._safe_extract(raw_context, ['device'], default=None)
        if device:
            return device.lower()
        
        # Parse from user_agent
        user_agent = self._safe_extract(raw_context, ['user_agent'], default='')
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'iphone' in user_agent_lower or 'android' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        else:
            return 'desktop'
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _safe_extract(
        self, 
        context: Dict[str, Any], 
        keys: List[str], 
        default: Any = None
    ) -> Any:
        """
        Safely extract nested value from context
        
        Example:
            _safe_extract({'geo': {'country': 'US'}}, ['geo', 'country'])
            → 'US'
        """
        value = context
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp string to datetime"""
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                pass
        
        # Fallback to current time
        return datetime.utcnow()
    
    def get_feature_vector(self, normalized_features: Dict[str, float]) -> List[float]:
        """
        Convert normalized features to vector for ML
        
        Returns values in consistent order (sorted by key).
        """
        return self.normalizer.get_feature_vector(normalized_features)
    
    def get_feature_names(self) -> List[str]:
        """Get ordered list of feature names"""
        return self.normalizer.get_feature_names()
    
    # ========================================================================
    # CACHING
    # ========================================================================
    
    def _get_cache_key(self, user_identifier: str) -> str:
        """Generate cache key"""
        return f"features_{hashlib.md5(user_identifier.encode()).hexdigest()}"
    
    def _get_from_cache(self, user_identifier: str) -> Optional[Dict[str, float]]:
        """Get features from cache if not expired"""
        key = self._get_cache_key(user_identifier)
        
        if key not in self._feature_cache:
            return None
        
        # Check expiration
        timestamp = self._cache_timestamps.get(key)
        if timestamp and (datetime.utcnow() - timestamp) > self._cache_ttl:
            # Expired
            del self._feature_cache[key]
            del self._cache_timestamps[key]
            return None
        
        return self._feature_cache[key]
    
    def _save_to_cache(self, user_identifier: str, features: Dict[str, float]) -> None:
        """Save features to cache"""
        key = self._get_cache_key(user_identifier)
        self._feature_cache[key] = features
        self._cache_timestamps[key] = datetime.utcnow()
        
        # Cleanup old cache entries if too many
        if len(self._feature_cache) > 10000:
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, ts in self._cache_timestamps.items()
            if (now - ts) > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._feature_cache[key]
            del self._cache_timestamps[key]
        
        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================
    
    async def get_feature_statistics(
        self,
        experiment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about extracted features
        
        Useful for debugging and monitoring feature quality.
        """
        if not self.normalizer.fitted:
            return {'error': 'Normalizer not fitted'}
        
        return {
            'fitted': True,
            'feature_names': self.get_feature_names(),
            'n_features': len(self.get_feature_names()),
            'numerical_stats': self.normalizer.numerical_stats,
            'categorical_mappings': {
                name: list(mapping.keys())
                for name, mapping in self.normalizer.categorical_mappings.items()
            },
            'cache_size': len(self._feature_cache),
            'cache_ttl_seconds': self._cache_ttl.total_seconds()
        }
    
    def validate_features(
        self,
        normalized_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate that features are in expected ranges
        
        Returns:
            {
                'valid': bool,
                'issues': List[str],
                'feature_ranges': Dict[str, Tuple[float, float]]
            }
        """
        issues = []
        feature_ranges = {}
        
        for name, value in normalized_features.items():
            feature_ranges[name] = (value, value)
            
            # Check for NaN or Inf
            if np.isnan(value) or np.isinf(value):
                issues.append(f"{name} has invalid value: {value}")
            
            # Check if in [0, 1] range (most features should be)
            if '_sin' not in name and '_cos' not in name:
                if value < -0.1 or value > 1.1:
                    issues.append(f"{name} out of expected range: {value}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'feature_ranges': feature_ranges
        }


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def create_test_context() -> Dict[str, Any]:
    """
    Create a test context for development/testing
    """
    return {
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'geo': {
            'country': 'US',
            'region': 'CA',
            'city': 'San Francisco'
        },
        'session': {
            'pages_viewed': 5,
            'time_seconds': 120,
            'scroll_depth': 75.0
        },
        'returning_user': False,
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'summer_sale',
        'referrer': 'https://google.com',
        'timestamp': datetime.utcnow().isoformat()
    }


async def test_feature_engineering():
    """
    Test feature engineering pipeline
    """
    print("Testing Feature Engineering Service...")
    
    # Create service
    service = FeatureEngineeringService(enable_cache=False)
    await service.initialize(auto_fit=True)
    
    # Extract features
    test_ctx = create_test_context()
    features = await service.extract_features(test_ctx)
    
    print(f"\n✅ Extracted {len(features)} features:")
    for name, value in sorted(features.items()):
        print(f"  {name}: {value:.4f}")
    
    # Get vector
    vector = service.get_feature_vector(features)
    print(f"\n✅ Feature vector ({len(vector)} dimensions):")
    print(f"  {vector[:5]}... (showing first 5)")
    
    # Validate
    validation = service.validate_features(features)
    print(f"\n✅ Validation: {'PASS' if validation['valid'] else 'FAIL'}")
    if validation['issues']:
        for issue in validation['issues']:
            print(f"  ⚠️  {issue}")
    
    # Statistics
    stats = await service.get_feature_statistics()
    print(f"\n✅ Statistics:")
    print(f"  N features: {stats['n_features']}")
    print(f"  Fitted: {stats['fitted']}")
    
    print("\n✅ All tests passed!")


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_feature_engineering())
