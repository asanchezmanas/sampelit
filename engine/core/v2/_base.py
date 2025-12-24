# engine/core/_base.py

"""
Base Allocator Class

CHANGELOG:
- 2024-12: Added performance metrics and algorithm metadata
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging


class BaseAllocator(ABC):
    """
    Base class for all allocation strategies
    
    New in v1.1:
    - get_performance_metrics() for monitoring
    - get_algorithm_info() for metadata
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Common configuration
        self.learning_rate = config.get('learning_rate', 0.1)
        self.min_samples = config.get('min_samples', 30)
        self.created_at = datetime.now(timezone.utc)
        
        # Performance tracking
        self._total_selections = 0
        self._total_updates = 0
    
    @abstractmethod
    async def select(
        self, 
        options: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> str:
        """
        Select optimal option
        
        Args:
            options: Available choices with performance data
            context: User/session context
            
        Returns:
            Selected option ID
        """
        pass
    
    @abstractmethod
    async def update(
        self, 
        option_id: str, 
        reward: float,
        context: Dict[str, Any]
    ) -> None:
        """
        Update algorithm with observed reward
        
        Args:
            option_id: ID of the selected option
            reward: Observed reward (0.0 to 1.0)
            context: Additional context
        """
        pass
    
    # ============================================
    # NEW: Performance Monitoring
    # ============================================
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring
        
        Override in subclasses to add algorithm-specific metrics.
        
        Returns:
            Dict with metrics (always safe to expose)
        """
        return {
            'total_selections': self._total_selections,
            'total_updates': self._total_updates,
            'uptime_seconds': (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            'selections_per_second': self._get_throughput(),
        }
    
    def _get_throughput(self) -> float:
        """Calculate throughput (selections/second)"""
        uptime = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        if uptime == 0:
            return 0.0
        return self._total_selections / uptime
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        Get algorithm metadata
        
        Returns:
            Dict with algorithm information (safe for public API)
        """
        return {
            'name': self.__class__.__name__,
            'type': self._get_algorithm_type(),
            'version': '1.1.0',
            'created_at': self.created_at.isoformat(),
            'config': self._get_safe_config(),
        }
    
    def _get_algorithm_type(self) -> str:
        """
        Get algorithm type category
        
        Override in subclasses for accurate categorization
        """
        return 'multi_armed_bandit'
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """
        Get sanitized config (no sensitive data)
        
        Filters out internal parameters that shouldn't be exposed
        """
        unsafe_keys = {'algorithm_type', 'internal_params', 'api_key', 'secret'}
        return {
            k: v for k, v in self.config.items() 
            if k not in unsafe_keys
        }
    
    # ============================================
    # NEW: Health Check
    # ============================================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if allocator is healthy
        
        Returns:
            Dict with health status
        """
        metrics = self.get_performance_metrics()
        
        is_healthy = True
        warnings = []
        
        # Check if allocator is being used
        if metrics['total_selections'] == 0:
            warnings.append('No selections made yet')
        
        # Check throughput (should be > 0 if active)
        if metrics['selections_per_second'] == 0 and metrics['total_selections'] > 0:
            warnings.append('Zero throughput - possible stall')
        
        return {
            'healthy': is_healthy,
            'warnings': warnings,
            'metrics': metrics,
        }
    
    # ============================================
    # Internal Helpers
    # ============================================
    
    def _log_decision(self, **kwargs):
        """Sanitized logging - no algorithm details"""
        safe_kwargs = {
            k: v for k, v in kwargs.items()
            if k not in ['alpha', 'beta', 'epsilon', 'thompson', 'scores', 'ucb']
        }
        self.logger.info("Decision made", extra=safe_kwargs)
    
    def _increment_selection_counter(self):
        """Track selection (call in subclasses)"""
        self._total_selections += 1
    
    def _increment_update_counter(self):
        """Track update (call in subclasses)"""
        self._total_updates += 1
