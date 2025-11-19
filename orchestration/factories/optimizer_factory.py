# orchestration/factories/optimizer_factory.py

"""
Optimizer Factory

Creates optimization engines without exposing implementation details.
This is the public-facing API for creating optimizers.
"""

from typing import Optional, Dict, Any
from orchestration.interfaces.optimization_interface import IOptimizer, OptimizationStrategy
from engine.core import _get_allocator

class OptimizerFactory:
    """
    Factory for creating optimization engines
    
    Implementation details are abstracted and proprietary.
    Clients don't know if it's Thompson, Epsilon, UCB, etc.
    """
    
    _instances: Dict[str, IOptimizer] = {}  # Singleton per strategy
    
    @classmethod
    def create(cls, 
               strategy: OptimizationStrategy,
               config: Optional[Dict[str, Any]] = None) -> IOptimizer:
        """
        Create optimizer instance
        
        This factory abstracts the actual implementation.
        Clients don't know which algorithm is being used.
        
        Args:
            strategy: Optimization strategy to use
            config: Optional configuration dict
            
        Returns:
            IOptimizer instance
        """
        
        # Use singleton per strategy to maintain state
        cache_key = f"{strategy.value}_{hash(str(sorted((config or {}).items())))}"
        
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Get allocator from private engine (ofuscado)
        optimizer = _get_allocator(
            strategy_code=strategy.value,
            config=config or {}
        )
        
        cls._instances[cache_key] = optimizer
        return optimizer
    
    @classmethod
    def create_for_experiment_type(cls, 
                                   experiment_type: str,
                                   traffic_level: str = 'normal',
                                   config: Optional[Dict[str, Any]] = None) -> IOptimizer:
        """
        Auto-select best strategy based on experiment characteristics
        
        This is where the magic happens - we decide:
        - Thompson for normal traffic
        - Epsilon for low traffic  
        - Sequential for funnels
        
        But the client never knows which we chose.
        
        Args:
            experiment_type: 'standard', 'funnel', 'email', 'push'
            traffic_level: 'low', 'normal', 'high'
            config: Optional configuration
            
        Returns:
            IOptimizer instance
        """
        
        # Funnel optimization
        if experiment_type == "funnel":
            return cls.create(OptimizationStrategy.SEQUENTIAL, config)
        
        # Low traffic optimization
        if traffic_level == "low":
            return cls.create(OptimizationStrategy.FAST_LEARNING, config)
        
        # Default: adaptive (Thompson Sampling internally)
        return cls.create(OptimizationStrategy.ADAPTIVE, config)
    
    @classmethod
    def clear_cache(cls):
        """Clear singleton cache (for testing)"""
        cls._instances.clear()
