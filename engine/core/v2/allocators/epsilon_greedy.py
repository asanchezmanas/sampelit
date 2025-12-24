# engine/core/v2/allocators/epsilon_greedy.py

"""
Epsilon-Greedy Allocator

Simple exploration-exploitation algorithm:
- With probability ε: EXPLORE (random)
- With probability 1-ε: EXPLOIT (best known)

Use cases:
- Benchmarking against Thompson Sampling
- Simple experiments where interpretability matters
- Comparing to academic baselines

References:
- Sutton & Barto (2018). Reinforcement Learning: An Introduction
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from .._base import BaseAllocator

logger = logging.getLogger(__name__)


class EpsilonGreedyAllocator(BaseAllocator):
    """
    Epsilon-Greedy strategy
    
    Balances exploration and exploitation with a simple rule:
    - ε% of the time: explore (random selection)
    - (1-ε)% of the time: exploit (choose best)
    
    Config:
        epsilon: Exploration rate (0.0 - 1.0)
            - 0.0 = pure exploitation
            - 1.0 = pure exploration
            - 0.1 = recommended (10% exploration)
        
        decay: Decay rate for epsilon (optional)
            - 1.0 = no decay (default)
            - 0.99 = slow decay
            - 0.95 = fast decay
        
        min_epsilon: Minimum epsilon value
            - Prevents epsilon from decaying to 0
            - Recommended: 0.01 (1% exploration always)
        
        min_samples: Minimum samples before exploiting
            - Ensures each variant gets tried
            - Default: 10
    
    Example:
        >>> allocator = EpsilonGreedyAllocator({
        ...     'epsilon': 0.1,
        ...     'decay': 0.99,
        ...     'min_epsilon': 0.01
        ... })
        >>> selected = allocator.select(variants, context)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        
        self.epsilon = self.config.get('epsilon', 0.1)
        self.decay = self.config.get('decay', 1.0)
        self.min_epsilon = self.config.get('min_epsilon', 0.01)
        self.min_samples_per_variant = self.config.get('min_samples', 10)
        
        # Validate
        if not 0.0 <= self.epsilon <= 1.0:
            raise ValueError(f"epsilon must be in [0, 1], got {self.epsilon}")
        if not 0.0 <= self.decay <= 1.0:
            raise ValueError(f"decay must be in [0, 1], got {self.decay}")
        
        logger.info(
            f"Initialized EpsilonGreedy: ε={self.epsilon}, "
            f"decay={self.decay}, min_ε={self.min_epsilon}"
        )
    
    async def select(
        self, 
        options: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> str:
        """
        Select variant using epsilon-greedy
        
        Args:
            options: List of variants with _internal_state
            context: User context (not used in epsilon-greedy)
        
        Returns:
            Selected variant ID
        """
        if not options:
            raise ValueError("No options provided")
        
        self._increment_selection_counter()
        
        # Calculate current epsilon (with decay)
        current_epsilon = self._get_current_epsilon()
        
        # Check if we have minimum samples for all variants
        needs_exploration = self._needs_minimum_samples(options)
        
        if needs_exploration:
            # Force exploration until all variants have min samples
            selected_id = self._explore_undersampled(options)
            logger.debug(f"Min samples phase: selected {selected_id}")
        elif random.random() < current_epsilon:
            # EXPLORE: random selection
            selected_id = self._explore(options)
            logger.debug(f"Explore (ε={current_epsilon:.3f}): {selected_id}")
        else:
            # EXPLOIT: choose best
            selected_id = self._exploit(options)
            logger.debug(f"Exploit: {selected_id}")
        
        return selected_id
    
    async def update(
        self, 
        option_id: str, 
        reward: float, 
        context: Dict[str, Any]
    ) -> None:
        """
        Update handled by repository layer
        
        Epsilon-greedy doesn't maintain internal state beyond
        what's in the database.
        """
        self._increment_update_counter()
    
    def _get_current_epsilon(self) -> float:
        """
        Calculate current epsilon with decay
        
        Formula: ε_t = max(min_ε, ε_0 * decay^t)
        """
        decayed_epsilon = self.epsilon * (self.decay ** self._total_selections)
        return max(self.min_epsilon, decayed_epsilon)
    
    def _needs_minimum_samples(self, options: List[Dict]) -> bool:
        """Check if any variant lacks minimum samples"""
        for option in options:
            state = option.get('_internal_state', {})
            samples = state.get('samples', 0)
            if samples < self.min_samples_per_variant:
                return True
        return False
    
    def _explore_undersampled(self, options: List[Dict]) -> str:
        """
        Select undersampled variant (forced exploration)
        
        Prioritizes variants with fewest samples
        """
        # Find variants below threshold
        undersampled = []
        for option in options:
            state = option.get('_internal_state', {})
            samples = state.get('samples', 0)
            if samples < self.min_samples_per_variant:
                undersampled.append((option['id'], samples))
        
        if not undersampled:
            # Fallback to random
            return random.choice([opt['id'] for opt in options])
        
        # Select variant with fewest samples
        min_samples = min(s for _, s in undersampled)
        candidates = [opt_id for opt_id, s in undersampled if s == min_samples]
        
        return random.choice(candidates)
    
    def _explore(self, options: List[Dict]) -> str:
        """
        Exploration: random selection
        
        Pure uniform random selection across all variants.
        """
        return random.choice([opt['id'] for opt in options])
    
    def _exploit(self, options: List[Dict]) -> str:
        """
        Exploitation: choose variant with highest observed conversion rate
        
        If no data available, defaults to first variant.
        """
        best_id = None
        best_rate = -1.0
        
        for option in options:
            state = option.get('_internal_state', {})
            samples = state.get('samples', 0)
            success_count = state.get('success_count', 1)  # Includes prior
            
            if samples > 0:
                # Observed conversion rate (remove prior)
                rate = (success_count - 1) / samples
            else:
                # No data: assume 50%
                rate = 0.5
            
            if rate > best_rate:
                best_rate = rate
                best_id = option['id']
        
        # Fallback to first option if none found
        return best_id if best_id else options[0]['id']
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Override to add epsilon-specific metrics"""
        base_metrics = super().get_performance_metrics()
        
        base_metrics.update({
            'current_epsilon': self._get_current_epsilon(),
            'base_epsilon': self.epsilon,
            'decay_rate': self.decay,
            'min_epsilon': self.min_epsilon,
        })
        
        return base_metrics
    
    def _get_algorithm_type(self) -> str:
        """Override to specify algorithm type"""
        return 'epsilon_greedy'


# Convenience alias
EpsilonGreedy = EpsilonGreedyAllocator
