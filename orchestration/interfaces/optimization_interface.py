# orchestration/interfaces/optimization_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

class OptimizationStrategy(Enum):
    """
    Available optimization strategies
    
    Note: Implementation details are proprietary
    """
    STANDARD = "standard"           # Traditional A/B
    ADAPTIVE = "adaptive"           # Adaptive allocation (default)
    FAST_LEARNING = "fast_learning" # Low-traffic optimized
    SEQUENTIAL = "sequential"       # Multi-step (funnels)
    HYBRID = "hybrid"              # Auto-select best method

class IOptimizer(ABC):
    """
    Samplit Optimization Interface
    
    This is the public contract for all optimization engines.
    Actual implementations are proprietary.
    """
    
    @abstractmethod
    async def select(self, 
                    options: List[Dict[str, Any]], 
                    context: Dict[str, Any]) -> str:
        """
        Select the optimal option for given context
        
        Args:
            options: Available choices with performance data
            context: User/session context for personalization
            
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
        """
        pass
    
    @abstractmethod
    def get_insights(self) -> Dict[str, Any]:
        """
        Get non-sensitive performance insights
        """
        pass
