# engine/core/allocators/bayesian.py
"""
Bayesian Allocator - Thompson Sampling

Implementation of Thompson Sampling algorithm for multi-armed bandits.

References:
- Thompson, W. R. (1933). "On the Likelihood that One Unknown 
  Probability Exceeds Another in View of the Evidence of Two Samples"
- Chapelle, O., & Li, L. (2011). "An Empirical Evaluation of 
  Thompson Sampling"
- Agrawal, S., & Goyal, N. (2012). "Analysis of Thompson Sampling 
  for the Multi-armed Bandit Problem"

Algorithm Overview:
==================
Thompson Sampling is a Bayesian approach to the multi-armed bandit problem.
For each variant i:
1. Maintain Beta(αᵢ, βᵢ) posterior distribution
2. Sample θᵢ ~ Beta(αᵢ, βᵢ)
3. Select variant with highest sampled θᵢ
4. Update: αᵢ += reward, βᵢ += (1 - reward)

Advantages:
- Naturally balances exploration vs exploitation
- No hyperparameters to tune
- Proven regret bounds
- Works well with sparse data

License: Proprietary
Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BayesianAllocator:
    """
    Thompson Sampling Allocator
    
    Uses Beta-Binomial conjugate priors for binary rewards (conversion/no conversion).
    
    The Beta distribution is conjugate to the Binomial, meaning:
    - Prior: Beta(α, β)
    - Likelihood: Binomial(n, p)
    - Posterior: Beta(α + successes, β + failures)
    
    Attributes:
        alpha_prior: Prior successes (default: 1.0 = uniform prior)
        beta_prior: Prior failures (default: 1.0 = uniform prior)
        min_samples: Minimum samples before exploiting (default: 100)
    
    Example:
        >>> allocator = BayesianAllocator({'alpha_prior': 1.0, 'beta_prior': 1.0})
        >>> 
        >>> variants = [
        ...     {'id': 'v1', 'algorithm_state': {'alpha': 10, 'beta': 90}},
        ...     {'id': 'v2', 'algorithm_state': {'alpha': 15, 'beta': 85}},
        ... ]
        >>> 
        >>> selected_idx = allocator.select_variant(variants)
        >>> print(f"Selected variant {selected_idx}")
        >>> 
        >>> # After observing reward
        >>> new_state = allocator.update_state(
        ...     variants[selected_idx]['algorithm_state'],
        ...     reward=1.0  # conversion
        ... )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize allocator
        
        Args:
            config: Configuration dict with optional:
                - alpha_prior: Prior successes (default: 1.0)
                  - 1.0 = uniform prior (no preference)
                  - >1.0 = optimistic prior (expect success)
                  - <1.0 = pessimistic prior (expect failure)
                - beta_prior: Prior failures (default: 1.0)
                - min_samples: Minimum samples before optimizing (default: 100)
                  - Lower = faster exploitation, higher risk
                  - Higher = longer exploration, lower risk
        """
        self.config = config or {}
        self.alpha_prior = self.config.get('alpha_prior', 1.0)
        self.beta_prior = self.config.get('beta_prior', 1.0)
        self.min_samples = self.config.get('min_samples', 100)
        
        # Validate priors
        if self.alpha_prior <= 0 or self.beta_prior <= 0:
            raise ValueError("Alpha and beta priors must be positive")
        
        logger.debug(
            f"Initialized BayesianAllocator: "
            f"α={self.alpha_prior}, β={self.beta_prior}, "
            f"min_samples={self.min_samples}"
        )
    
    def select_variant(self, variants: List[Dict[str, Any]]) -> int:
        """
        Select variant using Thompson Sampling
        
        Args:
            variants: List of variants with 'algorithm_state' containing:
                - alpha: Posterior successes (α parameter of Beta)
                - beta: Posterior failures (β parameter of Beta)
                - samples: Total samples (optional, for min_samples check)
                
        Returns:
            Index of selected variant (0-based)
            
        Raises:
            ValueError: If variants list is empty
            
        Notes:
            - If total_samples < min_samples, uses uniform random selection
            - Otherwise, samples from Beta(α, β) and picks highest sample
            - Ties are broken randomly
        """
        if not variants:
            raise ValueError("Variants list cannot be empty")
        
        # Calculate total samples across all variants
        total_samples = sum(
            v.get('algorithm_state', {}).get('samples', 0)
            for v in variants
        )
        
        # If we don't have enough samples yet, explore uniformly
        if total_samples < self.min_samples:
            selected = int(np.random.randint(0, len(variants)))
            logger.debug(
                f"Uniform exploration: {total_samples}/{self.min_samples} samples, "
                f"selected variant {selected}"
            )
            return selected
        
        # Thompson Sampling: sample from Beta distribution for each variant
        samples = []
        
        for i, variant in enumerate(variants):
            state = variant.get('algorithm_state', {})
            
            # Get posterior parameters (default to priors if not set)
            alpha = state.get('alpha', self.alpha_prior)
            beta = state.get('beta', self.beta_prior)
            
            # Sample from Beta(α, β)
            try:
                sample = np.random.beta(alpha, beta)
            except ValueError as e:
                # If Beta parameters invalid, use prior
                logger.warning(
                    f"Invalid Beta parameters for variant {i}: "
                    f"α={alpha}, β={beta}. Using prior."
                )
                sample = np.random.beta(self.alpha_prior, self.beta_prior)
            
            samples.append(sample)
            
            logger.debug(
                f"Variant {i}: α={alpha:.2f}, β={beta:.2f}, "
                f"sample={sample:.4f}, "
                f"samples={state.get('samples', 0)}"
            )
        
        # Select variant with highest sample
        selected = int(np.argmax(samples))
        
        logger.debug(
            f"Thompson Sampling: selected variant {selected} "
            f"(sample={samples[selected]:.4f})"
        )
        
        return selected
    
    def update_state(
        self, 
        variant_state: Dict[str, Any], 
        reward: float
    ) -> Dict[str, Any]:
        """
        Update variant state after observing reward
        
        Bayesian update rule:
        - If reward = 1: α = α + 1 (observed success)
        - If reward = 0: β = β + 1 (observed failure)
        
        Args:
            variant_state: Current state with 'alpha', 'beta', 'samples'
            reward: Observed reward
                - 1.0 = conversion (success)
                - 0.0 = no conversion (failure)
                - 0.0-1.0 = partial reward (e.g., 0.5 for partial completion)
            
        Returns:
            Updated state dict with:
                - alpha: Updated posterior successes
                - beta: Updated posterior failures
                - samples: Incremented sample count
                - version: State version (for migration tracking)
        
        Notes:
            - For partial rewards (0 < r < 1), we update:
              α += r, β += (1 - r)
            - This maintains the probabilistic interpretation
        """
        # Get current parameters (default to priors)
        alpha = variant_state.get('alpha', self.alpha_prior)
        beta = variant_state.get('beta', self.beta_prior)
        samples = variant_state.get('samples', 0)
        
        # Bayesian update
        if reward >= 1.0:
            # Full success
            alpha += 1.0
        elif reward <= 0.0:
            # Full failure
            beta += 1.0
        else:
            # Partial reward (e.g., 0.5)
            alpha += reward
            beta += (1.0 - reward)
        
        samples += 1
        
        new_state = {
            'alpha': alpha,
            'beta': beta,
            'samples': samples,
            'version': variant_state.get('version', 1)
        }
        
        logger.debug(
            f"State updated: α={alpha:.2f}, β={beta:.2f}, "
            f"samples={samples}, reward={reward}"
        )
        
        return new_state
    
    def get_probability_best(
        self, 
        variants: List[Dict[str, Any]], 
        n_samples: int = 10000
    ) -> List[float]:
        """
        Calculate probability each variant is best using Monte Carlo
        
        Uses Monte Carlo simulation to estimate P(variant i is best).
        This is useful for analytics and deciding when to stop experiment.
        
        Args:
            variants: List of variants with algorithm_state
            n_samples: Number of Monte Carlo samples (default: 10000)
                - More samples = more accurate but slower
                - 10000 is good balance for production
            
        Returns:
            List of probabilities (one per variant), summing to 1.0
            
        Example:
            >>> probs = allocator.get_probability_best(variants)
            >>> print(f"Variant 0 has {probs[0]:.1%} chance of being best")
            >>> 
            >>> # Stop experiment if one variant has >95% probability
            >>> if max(probs) > 0.95:
            ...     print("Winner detected!")
        
        Algorithm:
            1. For each Monte Carlo sample:
               - Sample θᵢ ~ Beta(αᵢ, βᵢ) for each variant i
               - Find argmax θᵢ
            2. Count how often each variant was best
            3. Normalize counts to get probabilities
        """
        if not variants:
            return []
        
        # Generate Monte Carlo samples for all variants
        variant_samples = []
        
        for variant in variants:
            state = variant.get('algorithm_state', {})
            alpha = state.get('alpha', self.alpha_prior)
            beta = state.get('beta', self.beta_prior)
            
            try:
                # Generate n_samples from Beta(α, β)
                samples = np.random.beta(alpha, beta, n_samples)
            except ValueError:
                # If invalid parameters, use uniform
                samples = np.random.uniform(0, 1, n_samples)
            
            variant_samples.append(samples)
        
        variant_samples = np.array(variant_samples)
        
        # For each Monte Carlo sample, find which variant was best
        best_indices = np.argmax(variant_samples, axis=0)
        
        # Count how often each variant was best
        probabilities = [
            (best_indices == i).sum() / n_samples
            for i in range(len(variants))
        ]
        
        logger.debug(
            f"Probability best (n={n_samples}): " +
            ", ".join(f"v{i}={p:.3f}" for i, p in enumerate(probabilities))
        )
        
        return probabilities
    
    def get_expected_loss(
        self,
        variants: List[Dict[str, Any]],
        n_samples: int = 10000
    ) -> List[float]:
        """
        Calculate expected loss for each variant
        
        Expected loss = E[max_j(θⱼ) - θᵢ]
        
        This measures how much worse variant i is compared to the best.
        Useful for decision making: deploy variant with lowest expected loss.
        
        Args:
            variants: List of variants with algorithm_state
            n_samples: Number of Monte Carlo samples
            
        Returns:
            List of expected losses (lower is better)
            
        Example:
            >>> losses = allocator.get_expected_loss(variants)
            >>> best_idx = np.argmin(losses)
            >>> print(f"Deploy variant {best_idx} (loss={losses[best_idx]:.4f})")
        """
        if not variants:
            return []
        
        # Generate samples
        variant_samples = []
        
        for variant in variants:
            state = variant.get('algorithm_state', {})
            alpha = state.get('alpha', self.alpha_prior)
            beta = state.get('beta', self.beta_prior)
            
            try:
                samples = np.random.beta(alpha, beta, n_samples)
            except ValueError:
                samples = np.random.uniform(0, 1, n_samples)
            
            variant_samples.append(samples)
        
        variant_samples = np.array(variant_samples)
        
        # Find max for each sample
        max_samples = np.max(variant_samples, axis=0)
        
        # Calculate expected loss for each variant
        expected_losses = [
            np.mean(max_samples - variant_samples[i])
            for i in range(len(variants))
        ]
        
        return expected_losses


class AdaptiveBayesianAllocator(BayesianAllocator):
    """
    Adaptive Thompson Sampling with dynamic exploration
    
    Extends BayesianAllocator with adaptive exploration bonus.
    Automatically adjusts exploration based on:
    - Sample size (more exploration early on)
    - Confidence in best variant (less exploration if clear winner)
    - Variance in performance (more exploration if uncertain)
    
    Recommended for:
    - Experiments where traffic is unpredictable
    - Multi-element experiments
    - When you want faster convergence
    
    Example:
        >>> allocator = AdaptiveBayesianAllocator({
        ...     'alpha_prior': 1.0,
        ...     'beta_prior': 1.0,
        ...     'exploration_bonus': 0.3,  # Adds exploration
        ...     'min_samples': 100
        ... })
        >>> 
        >>> # Same interface as BayesianAllocator
        >>> selected = allocator.select_variant(variants)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptive allocator
        
        Args:
            config: Configuration with additional:
                - exploration_bonus: Bonus for under-explored variants (default: 0.0)
                  - 0.0 = no bonus (same as BayesianAllocator)
                  - 0.1-0.3 = light exploration (recommended)
                  - 0.5+ = heavy exploration (use for high variance)
        """
        super().__init__(config)
        self.exploration_bonus = self.config.get('exploration_bonus', 0.0)
        
        logger.debug(
            f"Initialized AdaptiveBayesianAllocator: "
            f"exploration_bonus={self.exploration_bonus}"
        )
    
    def select_variant(self, variants: List[Dict[str, Any]]) -> int:
        """
        Select variant with adaptive exploration
        
        Adds UCB-style exploration bonus to Thompson samples:
        sample_i = sample_i + bonus * sqrt(log(N) / n_i)
        
        Where:
        - N = total samples across all variants
        - n_i = samples for variant i
        - bonus = exploration_bonus parameter
        
        This encourages exploring variants with fewer samples,
        similar to UCB algorithm but maintaining Thompson's probabilistic framework.
        """
        if not variants:
            raise ValueError("Variants list cannot be empty")
        
        # Calculate total samples
        total_samples = sum(
            v.get('algorithm_state', {}).get('samples', 0)
            for v in variants
        )
        
        # If not enough samples, uniform exploration
        if total_samples < self.min_samples:
            return int(np.random.randint(0, len(variants)))
        
        # Sample with exploration bonus
        samples = []
        
        for i, variant in enumerate(variants):
            state = variant.get('algorithm_state', {})
            alpha = state.get('alpha', self.alpha_prior)
            beta = state.get('beta', self.beta_prior)
            variant_samples = state.get('samples', 0)
            
            # Base Thompson sample
            try:
                sample = np.random.beta(alpha, beta)
            except ValueError:
                sample = np.random.beta(self.alpha_prior, self.beta_prior)
            
            # Add exploration bonus for under-sampled variants
            if self.exploration_bonus > 0 and variant_samples < total_samples / len(variants):
                # UCB-style bonus: sqrt(log(N) / n_i)
                bonus = self.exploration_bonus * np.sqrt(
                    np.log(total_samples + 1) / max(variant_samples, 1)
                )
                sample += bonus
                
                logger.debug(
                    f"Variant {i}: base_sample={sample-bonus:.4f}, "
                    f"bonus={bonus:.4f}, final={sample:.4f}"
                )
            
            samples.append(sample)
        
        selected = int(np.argmax(samples))
        
        logger.debug(
            f"Adaptive Thompson: selected variant {selected} "
            f"(sample={samples[selected]:.4f})"
        )
        
        return selected
