"""
Sample Size Calculator
Statistical sample size calculation for A/B tests with segmentation.

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from scipy import stats
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """Type of statistical test"""
    PROPORTION = "proportion"  # Binary outcome (conversion)
    MEAN = "mean"              # Continuous outcome (revenue, time)


@dataclass
class SampleSizeResult:
    """
    Result of sample size calculation
    
    Attributes:
        per_variant: Samples needed per variant
        total_required: Total samples needed (all variants)
        per_segment_per_variant: Samples per variant per segment (if segmented)
        total_per_segment: Total per segment (if segmented)
        days_required: Days needed given daily traffic
        power: Statistical power (1 - β)
        alpha: Significance level (α)
        baseline_rate: Baseline conversion rate
        mde: Minimum detectable effect
        achievable: Whether experiment is achievable
        recommendation: Human-readable recommendation
    """
    per_variant: int
    total_required: int
    per_segment_per_variant: Optional[Dict[str, int]] = None
    total_per_segment: Optional[Dict[str, int]] = None
    days_required: Optional[float] = None
    power: float = 0.80
    alpha: float = 0.05
    baseline_rate: float = 0.0
    mde: float = 0.0
    achievable: bool = True
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'per_variant': self.per_variant,
            'total_required': self.total_required,
            'per_segment_per_variant': self.per_segment_per_variant,
            'total_per_segment': self.total_per_segment,
            'days_required': self.days_required,
            'power': self.power,
            'alpha': self.alpha,
            'baseline_rate': self.baseline_rate,
            'mde': self.mde,
            'achievable': self.achievable,
            'recommendation': self.recommendation
        }


class SampleSizeCalculator:
    """
    Professional sample size calculator for A/B testing
    
    Uses proper statistical formulas:
    - Power analysis (not magic numbers)
    - Bonferroni correction for multiple comparisons
    - Adjustments for segmentation
    - Traffic-based feasibility checks
    
    Example:
        >>> calculator = SampleSizeCalculator()
        >>> 
        >>> result = calculator.calculate_for_proportion(
        ...     baseline_rate=0.02,        # 2% CVR
        ...     mde=0.20,                  # Detect 20% lift
        ...     power=0.80,                # 80% power
        ...     alpha=0.05,                # 5% significance
        ...     n_variants=3,              # 3 variants
        ...     n_segments=5               # 5 segments
        ... )
        >>> 
        >>> print(f"Need {result.per_variant} per variant")
        >>> print(f"Total: {result.total_required}")
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SampleSizeCalculator")
    
    # ========================================================================
    # MAIN CALCULATIONS
    # ========================================================================
    
    def calculate_for_proportion(
        self,
        baseline_rate: float,
        mde: float,
        power: float = 0.80,
        alpha: float = 0.05,
        n_variants: int = 2,
        n_segments: Optional[int] = None,
        two_tailed: bool = True
    ) -> SampleSizeResult:
        """
        Calculate sample size for proportion test (e.g., conversion rate)
        
        Formula:
            n = 2 * (Z_α/2 + Z_β)² * p(1-p) / (MDE)²
        
        Where:
            - Z_α/2: Z-score for significance level (e.g., 1.96 for α=0.05)
            - Z_β: Z-score for power (e.g., 0.84 for power=0.80)
            - p: Baseline conversion rate
            - MDE: Minimum detectable effect (absolute)
        
        Args:
            baseline_rate: Baseline conversion rate (0-1)
            mde: Minimum detectable effect (relative, e.g., 0.20 = 20% lift)
            power: Statistical power (1 - β), typically 0.80
            alpha: Significance level (α), typically 0.05
            n_variants: Number of variants (including control)
            n_segments: Number of segments (None = no segmentation)
            two_tailed: Whether to use two-tailed test
            
        Returns:
            SampleSizeResult with calculated sizes
        """
        # ─────────────────────────────────────────────────────────────────
        # Input validation
        # ─────────────────────────────────────────────────────────────────
        if not 0 < baseline_rate < 1:
            raise ValueError(f"baseline_rate must be in (0, 1), got {baseline_rate}")
        
        if not 0 < mde < 1:
            raise ValueError(f"mde must be in (0, 1), got {mde}")
        
        if not 0 < power < 1:
            raise ValueError(f"power must be in (0, 1), got {power}")
        
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        
        # ─────────────────────────────────────────────────────────────────
        # Bonferroni correction for multiple comparisons
        # ─────────────────────────────────────────────────────────────────
        # When testing k variants against control, we do k-1 comparisons
        # Bonferroni: α_adjusted = α / n_comparisons
        n_comparisons = n_variants - 1
        
        if n_segments:
            # With segmentation, we also compare across segments
            # Total comparisons = (variants - 1) * segments
            n_comparisons = (n_variants - 1) * n_segments
        
        alpha_adjusted = alpha / n_comparisons
        
        self.logger.info(
            f"Bonferroni correction: α={alpha:.4f} → α_adj={alpha_adjusted:.4f} "
            f"({n_comparisons} comparisons)"
        )
        
        # ─────────────────────────────────────────────────────────────────
        # Calculate Z-scores
        # ─────────────────────────────────────────────────────────────────
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha_adjusted / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha_adjusted)
        
        z_beta = stats.norm.ppf(power)
        
        # ─────────────────────────────────────────────────────────────────
        # Calculate absolute effect size
        # ─────────────────────────────────────────────────────────────────
        # MDE is relative (e.g., 20% lift)
        # Absolute effect = baseline_rate * mde
        absolute_effect = baseline_rate * mde
        
        # ─────────────────────────────────────────────────────────────────
        # Sample size formula for proportions
        # ─────────────────────────────────────────────────────────────────
        # Pooled variance under H0 (equal proportions)
        p_pooled = baseline_rate
        variance = p_pooled * (1 - p_pooled)
        
        # Sample size per variant
        n_per_variant = (
            2 * (z_alpha + z_beta) ** 2 * variance / 
            (absolute_effect ** 2)
        )
        
        n_per_variant = int(np.ceil(n_per_variant))
        
        # ─────────────────────────────────────────────────────────────────
        # Total samples
        # ─────────────────────────────────────────────────────────────────
        total_required = n_per_variant * n_variants
        
        # ─────────────────────────────────────────────────────────────────
        # Segmentation adjustments
        # ─────────────────────────────────────────────────────────────────
        per_segment_per_variant = None
        total_per_segment = None
        
        if n_segments:
            # Each segment needs its own samples
            # Assume equal distribution across segments for now
            per_segment_per_variant = {
                f"segment_{i}": n_per_variant
                for i in range(n_segments)
            }
            
            total_per_segment = {
                f"segment_{i}": n_per_variant * n_variants
                for i in range(n_segments)
            }
            
            # Total across all segments
            total_required = n_per_variant * n_variants * n_segments
        
        # ─────────────────────────────────────────────────────────────────
        # Build result
        # ─────────────────────────────────────────────────────────────────
        result = SampleSizeResult(
            per_variant=n_per_variant,
            total_required=total_required,
            per_segment_per_variant=per_segment_per_variant,
            total_per_segment=total_per_segment,
            power=power,
            alpha=alpha,
            baseline_rate=baseline_rate,
            mde=mde,
            achievable=True  # Will be updated if traffic provided
        )
        
        self.logger.info(
            f"Calculated sample size: {n_per_variant} per variant, "
            f"{total_required} total"
        )
        
        return result
    
    def calculate_for_mean(
        self,
        baseline_mean: float,
        baseline_std: float,
        mde: float,
        power: float = 0.80,
        alpha: float = 0.05,
        n_variants: int = 2,
        n_segments: Optional[int] = None,
        two_tailed: bool = True
    ) -> SampleSizeResult:
        """
        Calculate sample size for mean test (e.g., revenue, time on site)
        
        Formula:
            n = 2 * (Z_α/2 + Z_β)² * σ² / (MDE)²
        
        Args:
            baseline_mean: Baseline mean value
            baseline_std: Baseline standard deviation
            mde: Minimum detectable effect (relative)
            power: Statistical power
            alpha: Significance level
            n_variants: Number of variants
            n_segments: Number of segments
            two_tailed: Whether to use two-tailed test
            
        Returns:
            SampleSizeResult
        """
        # Bonferroni correction
        n_comparisons = n_variants - 1
        if n_segments:
            n_comparisons = (n_variants - 1) * n_segments
        
        alpha_adjusted = alpha / n_comparisons
        
        # Z-scores
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha_adjusted / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha_adjusted)
        
        z_beta = stats.norm.ppf(power)
        
        # Absolute effect
        absolute_effect = baseline_mean * mde
        
        # Sample size formula for means
        n_per_variant = (
            2 * (z_alpha + z_beta) ** 2 * baseline_std ** 2 / 
            (absolute_effect ** 2)
        )
        
        n_per_variant = int(np.ceil(n_per_variant))
        
        # Total
        total_required = n_per_variant * n_variants
        
        if n_segments:
            total_required = n_per_variant * n_variants * n_segments
        
        return SampleSizeResult(
            per_variant=n_per_variant,
            total_required=total_required,
            power=power,
            alpha=alpha,
            baseline_rate=baseline_mean,
            mde=mde,
            achievable=True
        )
    
    # ========================================================================
    # TRAFFIC-BASED FEASIBILITY
    # ========================================================================
    
    def calculate_with_traffic(
        self,
        baseline_rate: float,
        mde: float,
        daily_traffic: int,
        max_duration_days: int = 90,
        power: float = 0.80,
        alpha: float = 0.05,
        n_variants: int = 2,
        n_segments: Optional[int] = None
    ) -> SampleSizeResult:
        """
        Calculate sample size and check if achievable given traffic
        
        Args:
            baseline_rate: Baseline conversion rate
            mde: Minimum detectable effect
            daily_traffic: Daily traffic volume
            max_duration_days: Maximum acceptable test duration
            power: Statistical power
            alpha: Significance level
            n_variants: Number of variants
            n_segments: Number of segments
            
        Returns:
            SampleSizeResult with achievability assessment
        """
        # Calculate required sample size
        result = self.calculate_for_proportion(
            baseline_rate=baseline_rate,
            mde=mde,
            power=power,
            alpha=alpha,
            n_variants=n_variants,
            n_segments=n_segments
        )
        
        # Calculate days needed
        days_required = result.total_required / daily_traffic
        result.days_required = days_required
        
        # Check achievability
        if days_required > max_duration_days:
            result.achievable = False
            result.recommendation = (
                f"❌ Not achievable: Would require {days_required:.1f} days "
                f"(max: {max_duration_days} days).\n"
                f"\n"
                f"Options:\n"
                f"  1. Increase traffic\n"
                f"  2. Increase MDE (currently {mde*100:.0f}% - try {self._suggest_higher_mde(mde)*100:.0f}%)\n"
                f"  3. Reduce variants (currently {n_variants})\n"
                f"  4. Use manual segmentation instead of auto-clustering\n"
            )
        else:
            result.achievable = True
            result.recommendation = (
                f"✅ Achievable: {days_required:.1f} days needed "
                f"(within {max_duration_days} days limit).\n"
                f"\n"
                f"Per variant: {result.per_variant:,} samples\n"
                f"Total: {result.total_required:,} samples\n"
            )
        
        return result
    
    def _suggest_higher_mde(self, current_mde: float) -> float:
        """Suggest higher MDE that might be achievable"""
        # Increase by 50%
        suggested = current_mde * 1.5
        # Round to nice number
        return round(suggested, 2)
    
    # ========================================================================
    # REVERSE CALCULATION (WHAT MDE CAN WE DETECT?)
    # ========================================================================
    
    def calculate_detectable_effect(
        self,
        baseline_rate: float,
        available_samples: int,
        power: float = 0.80,
        alpha: float = 0.05,
        n_variants: int = 2,
        n_segments: Optional[int] = None
    ) -> float:
        """
        Reverse calculation: Given samples, what effect can we detect?
        
        This is useful for determining if an experiment is underpowered.
        
        Args:
            baseline_rate: Baseline conversion rate
            available_samples: Available samples per variant
            power: Statistical power
            alpha: Significance level
            n_variants: Number of variants
            n_segments: Number of segments
            
        Returns:
            Minimum detectable effect (relative)
        """
        # Bonferroni correction
        n_comparisons = n_variants - 1
        if n_segments:
            n_comparisons = (n_variants - 1) * n_segments
        
        alpha_adjusted = alpha / n_comparisons
        
        # Z-scores
        z_alpha = stats.norm.ppf(1 - alpha_adjusted / 2)
        z_beta = stats.norm.ppf(power)
        
        # Rearrange formula to solve for MDE
        # n = 2 * (Z_α + Z_β)² * p(1-p) / (MDE_abs)²
        # MDE_abs = sqrt(2 * (Z_α + Z_β)² * p(1-p) / n)
        
        p = baseline_rate
        variance = p * (1 - p)
        
        absolute_effect = np.sqrt(
            2 * (z_alpha + z_beta) ** 2 * variance / available_samples
        )
        
        # Convert to relative effect
        relative_effect = absolute_effect / baseline_rate
        
        return float(relative_effect)
    
    # ========================================================================
    # PRACTICAL RECOMMENDATIONS
    # ========================================================================
    
    def recommend_configuration(
        self,
        daily_traffic: int,
        baseline_rate: float,
        desired_mde: float = 0.10,
        max_duration_days: int = 30,
        use_segmentation: bool = False
    ) -> Dict[str, Any]:
        """
        Recommend experiment configuration based on constraints
        
        This is the high-level function to use for practical recommendations.
        
        Args:
            daily_traffic: Daily traffic volume
            baseline_rate: Baseline conversion rate
            desired_mde: Desired minimum detectable effect (default 10%)
            max_duration_days: Maximum test duration
            use_segmentation: Whether to use segmentation
            
        Returns:
            Dictionary with recommendations:
            {
                'recommendation': str,
                'n_variants': int,
                'n_segments': int | None,
                'achievable_mde': float,
                'days_required': float,
                'power': float
            }
        """
        recommendations = []
        
        # ─────────────────────────────────────────────────────────────────
        # Test different configurations
        # ─────────────────────────────────────────────────────────────────
        
        configs_to_test = [
            # (n_variants, n_segments, label)
            (2, None, "Simple A/B (2 variants, no segmentation)"),
            (3, None, "A/B/C (3 variants, no segmentation)"),
            (2, 3, "A/B with 3 segments"),
            (3, 3, "A/B/C with 3 segments"),
            (2, 5, "A/B with 5 segments"),
        ]
        
        if not use_segmentation:
            configs_to_test = configs_to_test[:2]  # Only non-segmented
        
        for n_variants, n_segments, label in configs_to_test:
            result = self.calculate_with_traffic(
                baseline_rate=baseline_rate,
                mde=desired_mde,
                daily_traffic=daily_traffic,
                max_duration_days=max_duration_days,
                n_variants=n_variants,
                n_segments=n_segments
            )
            
            recommendations.append({
                'label': label,
                'n_variants': n_variants,
                'n_segments': n_segments,
                'achievable': result.achievable,
                'days_required': result.days_required,
                'total_samples': result.total_required
            })
        
        # ─────────────────────────────────────────────────────────────────
        # Select best configuration
        # ─────────────────────────────────────────────────────────────────
        
        # Filter achievable configs
        achievable_configs = [r for r in recommendations if r['achievable']]
        
        if achievable_configs:
            # Pick most complex achievable config (more segments/variants = better)
            best = max(
                achievable_configs,
                key=lambda x: (
                    x['n_segments'] or 0,
                    x['n_variants']
                )
            )
            
            recommendation = (
                f"✅ Recommended: {best['label']}\n"
                f"   Duration: {best['days_required']:.1f} days\n"
                f"   Total samples: {best['total_samples']:,}\n"
                f"\n"
                f"This configuration allows you to detect a {desired_mde*100:.0f}% effect "
                f"with 80% power."
            )
            
            return {
                'recommendation': recommendation,
                'n_variants': best['n_variants'],
                'n_segments': best['n_segments'],
                'achievable_mde': desired_mde,
                'days_required': best['days_required'],
                'power': 0.80,
                'all_options': recommendations
            }
        
        else:
            # No config achievable - calculate what MDE is achievable
            # Use simplest config (2 variants, no segments)
            available_samples_per_variant = (
                daily_traffic * max_duration_days / 2
            )
            
            achievable_mde = self.calculate_detectable_effect(
                baseline_rate=baseline_rate,
                available_samples=int(available_samples_per_variant),
                n_variants=2,
                n_segments=None
            )
            
            recommendation = (
                f"⚠️  Cannot achieve {desired_mde*100:.0f}% MDE in {max_duration_days} days.\n"
                f"\n"
                f"With your traffic ({daily_traffic:,}/day), you can detect:\n"
                f"  Minimum effect: {achievable_mde*100:.0f}%\n"
                f"\n"
                f"Options:\n"
                f"  1. Accept higher MDE ({achievable_mde*100:.0f}%)\n"
                f"  2. Run test longer (>{max_duration_days} days)\n"
                f"  3. Increase traffic\n"
                f"  4. Focus on high-impact changes only\n"
            )
            
            return {
                'recommendation': recommendation,
                'n_variants': 2,
                'n_segments': None,
                'achievable_mde': achievable_mde,
                'days_required': None,
                'power': 0.80,
                'all_options': recommendations
            }


# ============================================================================
# UTILITIES
# ============================================================================

def format_sample_size_report(result: SampleSizeResult) -> str:
    """
    Generate human-readable report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("SAMPLE SIZE CALCULATION REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    # Parameters
    lines.append("Parameters:")
    lines.append(f"  Baseline Rate:  {result.baseline_rate*100:.2f}%")
    lines.append(f"  MDE (relative): {result.mde*100:.0f}%")
    lines.append(f"  MDE (absolute): {result.baseline_rate*result.mde*100:.2f}pp")
    lines.append(f"  Power:          {result.power*100:.0f}%")
    lines.append(f"  Alpha:          {result.alpha*100:.2f}%")
    lines.append("")
    
    # Results
    lines.append("Required Samples:")
    lines.append(f"  Per variant:    {result.per_variant:,}")
    lines.append(f"  Total:          {result.total_required:,}")
    
    if result.days_required:
        lines.append(f"  Days needed:    {result.days_required:.1f}")
    
    lines.append("")
    
    # Segmentation details
    if result.per_segment_per_variant:
        lines.append("Per Segment Breakdown:")
        for seg, samples in result.per_segment_per_variant.items():
            total = result.total_per_segment[seg]
            lines.append(f"  {seg}: {samples:,} per variant ({total:,} total)")
        lines.append("")
    
    # Recommendation
    if result.recommendation:
        lines.append("Recommendation:")
        for line in result.recommendation.split('\n'):
            lines.append(f"  {line}")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)
