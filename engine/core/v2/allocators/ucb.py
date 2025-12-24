# engine/core/allocators/ucb.py

"""
UCB (Upper Confidence Bound) Allocator

Deterministic exploration-exploitation algorithm based on
confidence intervals.

Formula: UCB_i = μ̂_i + c * sqrt(ln(N) / n_i)

Where:
  μ̂_i = empirical mean reward for arm i
  N = total samples across all arms
  n_i = samples for arm i
  c = exploration constant (tunable hyperparameter)

Advantages:
✅ Deterministic (reproducible)
✅ Strong theoretical guarantees (regret bounds)
✅ Intuitive (optimism in the face of uncertainty)
✅ No probability distributions needed

Disadvantages:
⚠️ Requires tuning 'c' parameter
⚠️ Can be overly optimistic early on
⚠️ Doesn't model full uncertainty (Thompson does)

Use cases:
- When reproducibility is critical
- Benchmarking against probabilistic methods
- Academic comparisons
- When you want explainable decisions

References:
- Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). 
  "Finite-time Analysis of the Multiarmed Bandit Problem"
- Lattimore & Szepesvári (2020). "Bandit Algorithms"
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from .._base import BaseAllocator

logger = logging.getLogger(__name__)


class UCBAllocator(BaseAllocator):
    """
    Upper Confidence Bound (UCB1) allocator
    
    Selects the variant with highest upper confidence bound:
    UCB_i = mean_i + c * sqrt(ln(total_samples) / samples_i)
    
    Config:
        c: Exploration constant (default: 2.0)
           Recommended values:
           - 1.0 = conservative (less exploration)
           - 2.0 = balanced (recommended, √2 from theory)
           - 3.0 = aggressive (more exploration)
           
        min_samples: Minimum samples before using UCB (default: 30)
           Below this threshold, uses round-robin exploration
           
        optimistic_init: Initial value for variants with no data
           - True: assume high performance (optimism)
           - False: assume 0.5 (neutral)
    
    Example:
        >>> allocator = UCBAllocator({
        ...     'c': 2.0,
        ...     'min_samples': 30,
        ...     'optimistic_init': True
        ... })
        >>> selected = allocator.select(variants, context)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        
        self.c = self.config.get('c', 2.0)
        self.min_samples_per_variant = self.config.get('min_samples', 30)
        self.optimistic_init = self.config.get('optimistic_init', True)
        
        # Validate
        if self.c <= 0:
            raise ValueError(f"c must be positive, got {self.c}")
        
        # Track selections for round-robin phase
        self._round_robin_counter = 0
        
        logger.info(
            f"Initialized UCB: c={self.c}, "
            f"min_samples={self.min_samples_per_variant}, "
            f"optimistic={self.optimistic_init}"
        )
    
    async def select(
        self, 
        options: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> str:
        """
        Select variant using UCB formula
        
        Args:
            options: List of variants with _internal_state
            context: User context (not used in UCB)
        
        Returns:
            Selected variant ID
        """
        if not options:
            raise ValueError("No options provided")
        
        self._increment_selection_counter()
        
        # Calculate total samples across all variants
        total_samples = sum(
            opt.get('_internal_state', {}).get('samples', 0)
            for opt in options
        )
        
        # Phase 1: Round-robin until all variants have min_samples
        if self._needs_minimum_samples(options):
            selected_id = self._round_robin_select(options)
            logger.debug(
                f"Round-robin phase: {selected_id} "
                f"(total_samples={total_samples})"
            )
            return selected_id
        
        # Phase 2: UCB selection
        ucb_scores = self._calculate_ucb_scores(options, total_samples)
        
        # Select variant with highest UCB score
        selected_id = max(ucb_scores, key=ucb_scores.get)
        
        logger.debug(
            f"UCB selection: {selected_id} "
            f"(score={ucb_scores[selected_id]:.4f}, N={total_samples})"
        )
        
        # Log all scores for debugging
        if logger.isEnabledFor(logging.DEBUG):
            for opt_id, score in ucb_scores.items():
                logger.debug(f"  {opt_id}: UCB={score:.4f}")
        
        return selected_id
    
    async def update(
        self, 
        option_id: str, 
        reward: float, 
        context: Dict[str, Any]
    ) -> None:
        """
        Update handled by repository layer
        
        UCB uses empirical means from database state.
        """
        self._increment_update_counter()
    
    def _needs_minimum_samples(self, options: List[Dict]) -> bool:
        """Check if any variant lacks minimum samples"""
        for option in options:
            state = option.get('_internal_state', {})
            samples = state.get('samples', 0)
            if samples < self.min_samples_per_variant:
                return True
        return False
    
    def _round_robin_select(self, options: List[Dict]) -> str:
        """
        Round-robin selection for initial exploration
        
        Cycles through variants in order, prioritizing those
        with fewest samples.
        """
        # Find variant with fewest samples
        min_samples = float('inf')
        candidates = []
        
        for option in options:
            state = option.get('_internal_state', {})
            samples = state.get('samples', 0)
            
            if samples < min_samples:
                min_samples = samples
                candidates = [option['id']]
            elif samples == min_samples:
                candidates.append(option['id'])
        
        # If multiple candidates, use round-robin counter
        selected_idx = self._round_robin_counter % len(candidates)
        self._round_robin_counter += 1
        
        return candidates[selected_idx]
    
    def _calculate_ucb_scores(
        self, 
        options: List[Dict], 
        total_samples: int
    ) -> Dict[str, float]:
        """
        Calculate UCB score for each variant
        
        UCB_i = μ̂_i + c * sqrt(ln(N) / n_i)
        
        Args:
            options: List of variants
            total_samples: Total samples across all variants
        
        Returns:
            Dict mapping variant ID to UCB score
        """
        ucb_scores = {}
        
        for option in options:
            opt_id = option['id']
            state = option.get('_internal_state', {})
            
            samples = state.get('samples', 0)
            success_count = state.get('success_count', 1)  # Includes prior
            
            if samples == 0:
                # No data: use optimistic initialization
                if self.optimistic_init:
                    ucb_scores[opt_id] = float('inf')  # Force exploration
                else:
                    ucb_scores[opt_id] = 0.5  # Neutral assumption
                continue
            
            # Empirical mean (remove prior)
            empirical_mean = (success_count - 1) / samples
            
            # Confidence bonus (exploration term)
            confidence_bonus = self.c * math.sqrt(
                math.log(total_samples + 1) / samples
            )
            
            # UCB score
            ucb = empirical_mean + confidence_bonus
            
            ucb_scores[opt_id] = ucb
            
            logger.debug(
                f"{opt_id}: μ̂={empirical_mean:.3f}, "
                f"bonus={confidence_bonus:.3f}, "
                f"UCB={ucb:.3f}, n={samples}"
            )
        
        return ucb_scores
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Override to add UCB-specific metrics"""
        base_metrics = super().get_performance_metrics()
        
        base_metrics.update({
            'exploration_constant': self.c,
            'min_samples_per_variant': self.min_samples_per_variant,
            'optimistic_init': self.optimistic_init,
            'round_robin_count': self._round_robin_counter,
        })
        
        return base_metrics
    
    def _get_algorithm_type(self) -> str:
        """Override to specify algorithm type"""
        return 'ucb'


# Convenience alias
UCB = UCBAllocator


class UCB1Tuned(UCBAllocator):
    """
    UCB1-Tuned variant (uses variance in bonus term)
    
    More sophisticated than UCB1, considers variance of rewards.
    
    Formula: UCB_i = μ̂_i + sqrt(ln(N) / n_i * min(1/4, V_i(n_i)))
    
    Where V_i(n_i) is the empirical variance plus a bias term.
    
    Better performance in practice, but more complex.
    """
    
    def _calculate_ucb_scores(
        self, 
        options: List[Dict], 
        total_samples: int
    ) -> Dict[str, float]:
        """
        Calculate UCB1-Tuned scores using variance
        
        More adaptive to variance in rewards.
        """
        ucb_scores = {}
        
        for option in options:
            opt_id = option['id']
            state = option.get('_internal_state', {})
            
            samples = state.get('samples', 0)
            
            if samples == 0:
                ucb_scores[opt_id] = float('inf') if self.optimistic_init else 0.5
                continue
            
            success_count = state.get('success_count', 1)
            empirical_mean = (success_count - 1) / samples
            
            # Calculate empirical variance
            # Approximation: Var(Bernoulli(p)) = p(1-p)
            empirical_variance = empirical_mean * (1 - empirical_mean)
            
            # Variance term with bias correction
            variance_term = empirical_variance + math.sqrt(
                2 * math.log(total_samples + 1) / samples
            )
            
            # Cap variance at 1/4 (maximum for Bernoulli)
            variance_term = min(0.25, variance_term)
            
            # UCB1-Tuned formula
            confidence_bonus = math.sqrt(
                math.log(total_samples + 1) / samples * variance_term
            )
            
            ucb = empirical_mean + confidence_bonus
            
            ucb_scores[opt_id] = ucb
            
            logger.debug(
                f"{opt_id}: μ̂={empirical_mean:.3f}, "
                f"σ²={variance_term:.3f}, "
                f"UCB-Tuned={ucb:.3f}"
            )
        
        return ucb_scores
    
    def _get_algorithm_type(self) -> str:
        return 'ucb1_tuned'
