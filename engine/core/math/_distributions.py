# engine/core/math/_distributions.py

"""
Statistical Distribution Sampling

Proprietary implementations of sampling algorithms
used by Samplit's optimization engine.

⚠️ CONFIDENTIAL - Implementation details are trade secrets
"""

from typing import Dict, Any, List
import numpy as np

def sample_posterior(success_count: int,
                    failure_count: int,
                    exploration_bonus: float = 0.0) -> float:
    """
    Sample from posterior distribution
    
    This function samples from Samplit's proprietary
    posterior distribution model.
    
    Args:
        success_count: Number of positive outcomes
        failure_count: Number of negative outcomes
        exploration_bonus: Additional exploration term
    
    Returns:
        Sampled performance score
    
    Implementation: [CONFIDENTIAL]
    """
    
    # Esto es Adaptive Choice Strategy (Beta distribution)
    # pero nunca lo nombramos explícitamente
    
    # Prior + observed data
    alpha = success_count + 1.0
    beta = failure_count + 1.0
    
    # Sample from Beta distribution
    sampled_value = np.random.beta(alpha, beta)
    
    # Add exploration bonus if provided
    adjusted_value = sampled_value + exploration_bonus
    
    return float(adjusted_value)

def calculate_confidence_bounds(success_count: int,
                                failure_count: int,
                                confidence_level: float = 0.95) -> Dict[str, float]:
    """
    Calculate confidence bounds for performance estimate
    
    Uses Samplit's proprietary interval estimation method.
    
    Implementation: [CONFIDENTIAL - BAYESIAN CREDIBLE INTERVALS]
    """
    
    from scipy import stats
    
    alpha = success_count + 1.0
    beta = failure_count + 1.0
    
    # Calculate credible interval (Bayesian confidence interval)
    lower_percentile = (1 - confidence_level) / 2
    upper_percentile = 1 - lower_percentile
    
    lower_bound = stats.beta.ppf(lower_percentile, alpha, beta)
    upper_bound = stats.beta.ppf(upper_percentile, alpha, beta)
    
    expected_value = alpha / (alpha + beta)
    
    return {
        'expected': float(expected_value),
        'lower': float(lower_bound),
        'upper': float(upper_bound),
        'confidence': confidence_level
    }

def calculate_probability_best(options_data: List[Dict[str, int]],
                              samples: int = 10000) -> Dict[str, float]:
    """
    Calculate probability each option is the best
    
    Uses Monte Carlo simulation with Samplit's proprietary
    sampling methodology.
    
    Implementation: [CONFIDENTIAL - MONTE CARLO BAYESIAN]
    """
    
    # Generate samples for each option
    option_samples = {}
    
    for i, opt_data in enumerate(options_data):
        alpha = opt_data['successes'] + 1.0
        beta = opt_data['failures'] + 1.0
        
        # Sample from posterior
        option_samples[i] = np.random.beta(alpha, beta, samples)
    
    # Count how often each is best
    prob_best = {}
    
    for i in range(len(options_data)):
        is_best_count = 0
        
        for sample_idx in range(samples):
            # Check if this option is best in this sample
            is_best = True
            current_sample = option_samples[i][sample_idx]
            
            for j in range(len(options_data)):
                if i != j and option_samples[j][sample_idx] > current_sample:
                    is_best = False
                    break
            
            if is_best:
                is_best_count += 1
        
        prob_best[i] = is_best_count / samples
    
    return prob_best

# Export only what's needed
__all__ = [
    'sample_posterior',
    'calculate_confidence_bounds',
    'calculate_probability_best'
]
