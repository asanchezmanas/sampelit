# engine/core/_base.py

"""
Base Allocator Class

All optimization strategies inherit from this base.
Implementation details are proprietary.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

class BaseAllocator(ABC):
    """
    Base class for all allocation strategies
    
    This is the foundation for all optimization algorithms.
    Actual implementations (Thompson Sampling, Epsilon-Greedy, etc.)
    are in separate modules with obfuscated names.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Common configuration
        self.learning_rate = config.get('learning_rate', 0.1)
        self.min_samples = config.get('min_samples', 30)
        self.created_at = datetime.now(timezone.utc)
    
    @abstractmethod
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
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
    async def update(self, 
                    option_id: str, 
                    reward: float,
                    context: Dict[str, Any]) -> None:
        """
        Update algorithm with observed reward
        
        Args:
            option_id: ID of the selected option
            reward: Observed reward (0.0 to 1.0)
            context: Additional context
        """
        pass
    
    def get_insights(self) -> Dict[str, Any]:
        """
        Get non-sensitive insights
        
        Returns public-safe metrics without revealing algorithm details
        """
        return {
            'strategy': self.__class__.__name__,
            'created_at': self.created_at.isoformat(),
            'config': {
                k: v for k, v in self.config.items() 
                if k not in ['algorithm_type', 'internal_params']
            }
        }
    
    def _log_decision(self, **kwargs):
        """Sanitized logging - no algorithm details"""
        safe_kwargs = {
            k: v for k, v in kwargs.items()
            if k not in ['alpha', 'beta', 'epsilon', 'thompson', 'scores']
        }
        self.logger.info("Decision made", extra=safe_kwargs)
