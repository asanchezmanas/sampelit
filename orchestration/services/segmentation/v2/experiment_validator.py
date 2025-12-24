"""
Experiment Validator
Validates experiments have sufficient samples for statistical power.

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

from .sample_size_calculator import SampleSizeCalculator, SampleSizeResult

logger = logging.getLogger(__name__)


class ExperimentValidator:
    """
    Validates experiment configuration and progress
    
    Checks:
    - Sufficient sample size for desired power
    - Even traffic allocation
    - Minimum runtime
    - Early stopping criteria
    - Sample ratio mismatch (SRM)
    
    Example:
        >>> validator = ExperimentValidator(db_pool)
        >>> 
        >>> validation = await validator.validate_before_launch(
        ...     experiment_id='exp_123',
        ...     baseline_cvr=0.02,
        ...     desired_mde=0.20,
        ...     daily_traffic=5000
        ... )
        >>> 
        >>> if validation['can_launch']:
        ...     print("✅ Experiment ready to launch")
        ... else:
        ...     print(f"❌ Issues: {validation['issues']}")
    """
    
    def __init__(self, db_pool):
        self.db = db_pool
        self.calculator = SampleSizeCalculator()
        self.logger = logging.getLogger(f"{__name__}.ExperimentValidator")
    
    # ========================================================================
    # PRE-LAUNCH VALIDATION
    # ========================================================================
    
    async def validate_before_launch(
        self,
        experiment_id: UUID,
        baseline_cvr: float,
        desired_mde: float = 0.10,
        daily_traffic: int = 1000,
        n_variants: int = 2,
        n_segments: Optional[int] = None,
        max_duration_days: int = 90
    ) -> Dict[str, Any]:
        """
        Validate experiment before launch
        
        Args:
            experiment_id: Experiment UUID
            baseline_cvr: Baseline conversion rate
            desired_mde: Desired minimum detectable effect
            daily_traffic: Expected daily traffic
            n_variants: Number of variants
            n_segments: Number of segments (None = no segmentation)
            max_duration_days: Maximum acceptable duration
            
        Returns:
            {
                'can_launch': bool,
                'issues': List[str],
                'warnings': List[str],
                'sample_size_result': SampleSizeResult,
                'recommendation': str
            }
        """
        self.logger.info(
            f"Validating experiment {experiment_id} before launch"
        )
        
        issues = []
        warnings = []
        
        # ─────────────────────────────────────────────────────────────────
        # Check 1: Sample size calculation
        # ─────────────────────────────────────────────────────────────────
        sample_size_result = self.calculator.calculate_with_traffic(
            baseline_rate=baseline_cvr,
            mde=desired_mde,
            daily_traffic=daily_traffic,
            max_duration_days=max_duration_days,
            n_variants=n_variants,
            n_segments=n_segments
        )
        
        if not sample_size_result.achievable:
            issues.append(
                f"Insufficient traffic: Need {sample_size_result.days_required:.1f} days "
                f"(max: {max_duration_days})"
            )
        
        # ─────────────────────────────────────────────────────────────────
        # Check 2: Baseline CVR reasonable
        # ─────────────────────────────────────────────────────────────────
        if baseline_cvr < 0.001:  # < 0.1%
            warnings.append(
                f"Very low baseline CVR ({baseline_cvr*100:.2f}%) - "
                "experiment may take very long"
            )
        
        if baseline_cvr > 0.50:  # > 50%
            warnings.append(
                f"Very high baseline CVR ({baseline_cvr*100:.2f}%) - "
                "verify this is correct"
            )
        
        # ─────────────────────────────────────────────────────────────────
        # Check 3: MDE reasonable
        # ─────────────────────────────────────────────────────────────────
        if desired_mde < 0.05:  # < 5%
            warnings.append(
                f"Very small MDE ({desired_mde*100:.1f}%) - "
                "will require very large sample"
            )
        
        if desired_mde > 0.50:  # > 50%
            warnings.append(
                f"Very large MDE ({desired_mde*100:.0f}%) - "
                "you may be able to detect smaller effects"
            )
        
        # ─────────────────────────────────────────────────────────────────
        # Check 4: Too many variants/segments
        # ─────────────────────────────────────────────────────────────────
        if n_variants > 5:
            warnings.append(
                f"Many variants ({n_variants}) - "
                "consider reducing for faster results"
            )
        
        if n_segments and n_segments > 7:
            warnings.append(
                f"Many segments ({n_segments}) - "
                "sample size increases with segments"
            )
        
        # ─────────────────────────────────────────────────────────────────
        # Check 5: Minimum daily traffic
        # ─────────────────────────────────────────────────────────────────
        min_daily_traffic = 100 * n_variants
        if n_segments:
            min_daily_traffic *= n_segments
        
        if daily_traffic < min_daily_traffic:
            issues.append(
                f"Daily traffic too low ({daily_traffic}) - "
                f"minimum recommended: {min_daily_traffic}"
            )
        
        # ─────────────────────────────────────────────────────────────────
        # Determine if can launch
        # ─────────────────────────────────────────────────────────────────
        can_launch = len(issues) == 0
        
        # ─────────────────────────────────────────────────────────────────
        # Generate recommendation
        # ─────────────────────────────────────────────────────────────────
        if can_launch:
            recommendation = (
                f"✅ Experiment ready to launch!\n"
                f"\n"
                f"Configuration:\n"
                f"  Variants: {n_variants}\n"
                f"  Segments: {n_segments or 'None'}\n"
                f"  MDE: {desired_mde*100:.0f}%\n"
                f"  Expected duration: {sample_size_result.days_required:.1f} days\n"
                f"  Total samples needed: {sample_size_result.total_required:,}\n"
            )
            
            if warnings:
                recommendation += f"\n⚠️  Warnings:\n"
                for warning in warnings:
                    recommendation += f"  - {warning}\n"
        else:
            recommendation = (
                f"❌ Cannot launch experiment\n"
                f"\n"
                f"Issues:\n"
            )
            for issue in issues:
                recommendation += f"  - {issue}\n"
            
            recommendation += sample_size_result.recommendation
        
        return {
            'can_launch': can_launch,
            'issues': issues,
            'warnings': warnings,
            'sample_size_result': sample_size_result.to_dict(),
            'recommendation': recommendation
        }
    
    # ========================================================================
    # IN-FLIGHT VALIDATION
    # ========================================================================
    
    async def validate_running_experiment(
        self,
        experiment_id: UUID,
        check_srm: bool = True,
        check_power: bool = True
    ) -> Dict[str, Any]:
        """
        Validate running experiment
        
        Checks:
        - Sample Ratio Mismatch (SRM)
        - Sufficient samples collected
        - Early stopping criteria
        
        Args:
            experiment_id: Experiment UUID
            check_srm: Whether to check for SRM
            check_power: Whether to check if powered
            
        Returns:
            {
                'healthy': bool,
                'issues': List[str],
                'warnings': List[str],
                'metrics': Dict
            }
        """
        self.logger.info(f"Validating running experiment {experiment_id}")
        
        issues = []
        warnings = []
        metrics = {}
        
        # ─────────────────────────────────────────────────────────────────
        # Get experiment data
        # ─────────────────────────────────────────────────────────────────
        async with self.db.acquire() as conn:
            # Get variant allocation counts
            variant_stats = await conn.fetch(
                """
                SELECT 
                    variant_id,
                    COUNT(*) as allocations,
                    SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions
                FROM assignments
                WHERE experiment_id = $1
                GROUP BY variant_id
                """,
                experiment_id
            )
        
        if not variant_stats:
            return {
                'healthy': False,
                'issues': ['No data collected yet'],
                'warnings': [],
                'metrics': {}
            }
        
        # ─────────────────────────────────────────────────────────────────
        # Check 1: Sample Ratio Mismatch (SRM)
        # ─────────────────────────────────────────────────────────────────
        if check_srm:
            srm_result = self._check_srm(variant_stats)
            
            if srm_result['has_srm']:
                issues.append(
                    f"Sample Ratio Mismatch detected (p={srm_result['p_value']:.4f})"
                )
                warnings.append(
                    "Traffic allocation is uneven - check for implementation bugs"
                )
            
            metrics['srm'] = srm_result
        
        # ─────────────────────────────────────────────────────────────────
        # Check 2: Sufficient samples
        # ─────────────────────────────────────────────────────────────────
        if check_power:
            # Get baseline CVR (from control)
            control_stats = variant_stats[0]  # Assume first is control
            baseline_cvr = (
                control_stats['conversions'] / control_stats['allocations']
                if control_stats['allocations'] > 0
                else 0.02
            )
            
            # Check if we have enough samples
            total_allocations = sum(v['allocations'] for v in variant_stats)
            
            # Calculate what MDE we can detect with current samples
            avg_per_variant = total_allocations / len(variant_stats)
            
            detectable_mde = self.calculator.calculate_detectable_effect(
                baseline_rate=baseline_cvr,
                available_samples=int(avg_per_variant),
                n_variants=len(variant_stats)
            )
            
            metrics['current_samples'] = {
                'total': total_allocations,
                'per_variant_avg': avg_per_variant,
                'detectable_mde': detectable_mde
            }
            
            if detectable_mde > 0.30:  # Can only detect >30% effects
                warnings.append(
                    f"Underpowered: Can only detect {detectable_mde*100:.0f}% effects "
                    f"with current samples"
                )
        
        # ─────────────────────────────────────────────────────────────────
        # Check 3: Minimum samples per variant
        # ─────────────────────────────────────────────────────────────────
        for variant in variant_stats:
            if variant['allocations'] < 100:
                warnings.append(
                    f"Variant {variant['variant_id']} has only "
                    f"{variant['allocations']} samples (min: 100)"
                )
        
        # ─────────────────────────────────────────────────────────────────
        # Determine health
        # ─────────────────────────────────────────────────────────────────
        healthy = len(issues) == 0
        
        return {
            'healthy': healthy,
            'issues': issues,
            'warnings': warnings,
            'metrics': metrics
        }
    
    def _check_srm(
        self,
        variant_stats: List[Dict]
    ) -> Dict[str, Any]:
        """
        Check for Sample Ratio Mismatch
        
        Uses chi-square test to check if observed allocation
        matches expected allocation (usually 50/50 or 33/33/33).
        
        Args:
            variant_stats: List of {variant_id, allocations, conversions}
            
        Returns:
            {
                'has_srm': bool,
                'p_value': float,
                'expected': List[int],
                'observed': List[int]
            }
        """
        n_variants = len(variant_stats)
        total = sum(v['allocations'] for v in variant_stats)
        
        # Expected: Equal allocation
        expected = [total / n_variants] * n_variants
        
        # Observed
        observed = [v['allocations'] for v in variant_stats]
        
        # Chi-square test
        chi2_stat = sum(
            (obs - exp) ** 2 / exp
            for obs, exp in zip(observed, expected)
        )
        
        # p-value
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(chi2_stat, df=n_variants - 1)
        
        # SRM if p < 0.01 (strict threshold)
        has_srm = p_value < 0.01
        
        return {
            'has_srm': has_srm,
            'p_value': float(p_value),
            'chi2_stat': float(chi2_stat),
            'expected': [int(e) for e in expected],
            'observed': observed
        }
    
    # ========================================================================
    # EARLY STOPPING
    # ========================================================================
    
    async def check_early_stopping(
        self,
        experiment_id: UUID,
        alpha: float = 0.05,
        min_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Check if experiment can be stopped early
        
        Uses sequential testing (alpha spending function)
        to maintain overall Type I error rate.
        
        Args:
            experiment_id: Experiment UUID
            alpha: Overall significance level
            min_samples: Minimum samples before considering stopping
            
        Returns:
            {
                'can_stop': bool,
                'reason': str,
                'winner': Optional[int],
                'confidence': float
            }
        """
        # Get current results
        async with self.db.acquire() as conn:
            variant_stats = await conn.fetch(
                """
                SELECT 
                    variant_id,
                    COUNT(*) as allocations,
                    SUM(CASE WHEN converted THEN 1 ELSE 0 END) as conversions
                FROM assignments
                WHERE experiment_id = $1
                GROUP BY variant_id
                """,
                experiment_id
            )
        
        if not variant_stats or len(variant_stats) < 2:
            return {
                'can_stop': False,
                'reason': 'Insufficient data',
                'winner': None,
                'confidence': 0.0
            }
        
        # Check minimum samples
        if any(v['allocations'] < min_samples for v in variant_stats):
            return {
                'can_stop': False,
                'reason': f'Need at least {min_samples} samples per variant',
                'winner': None,
                'confidence': 0.0
            }
        
        # Simple z-test for now (could use sequential testing)
        control = variant_stats[0]
        p_control = control['conversions'] / control['allocations']
        
        significant_winner = None
        max_lift = 0.0
        
        for variant in variant_stats[1:]:
            p_variant = variant['conversions'] / variant['allocations']
            
            # Z-test
            pooled_p = (
                (control['conversions'] + variant['conversions']) /
                (control['allocations'] + variant['allocations'])
            )
            
            se = np.sqrt(
                pooled_p * (1 - pooled_p) * (
                    1/control['allocations'] + 1/variant['allocations']
                )
            )
            
            z = (p_variant - p_control) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            
            if p_value < alpha:
                lift = (p_variant - p_control) / p_control
                if abs(lift) > abs(max_lift):
                    max_lift = lift
                    significant_winner = variant['variant_id']
        
        if significant_winner:
            return {
                'can_stop': True,
                'reason': f'Significant winner found (lift: {max_lift*100:.1f}%)',
                'winner': significant_winner,
                'confidence': 1 - alpha
            }
        else:
            return {
                'can_stop': False,
                'reason': 'No significant winner yet',
                'winner': None,
                'confidence': 0.0
            }
    
    # ========================================================================
    # COMPREHENSIVE REPORT
    # ========================================================================
    
    async def generate_experiment_report(
        self,
        experiment_id: UUID
    ) -> str:
        """
        Generate comprehensive validation report
        """
        # Pre-launch validation (with estimated params)
        # In-flight validation
        # Early stopping check
        
        in_flight = await self.validate_running_experiment(experiment_id)
        early_stop = await self.check_early_stopping(experiment_id)
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"EXPERIMENT VALIDATION REPORT")
        lines.append(f"Experiment ID: {experiment_id}")
        lines.append("=" * 80)
        lines.append("")
        
        # Health
        health_emoji = "✅" if in_flight['healthy'] else "❌"
        lines.append(f"Health: {health_emoji} {'Healthy' if in_flight['healthy'] else 'Issues Detected'}")
        lines.append("")
        
        # Issues
        if in_flight['issues']:
            lines.append("Issues:")
            for issue in in_flight['issues']:
                lines.append(f"  ❌ {issue}")
            lines.append("")
        
        # Warnings
        if in_flight['warnings']:
            lines.append("Warnings:")
            for warning in in_flight['warnings']:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")
        
        # Metrics
        if 'current_samples' in in_flight['metrics']:
            cs = in_flight['metrics']['current_samples']
            lines.append("Current Samples:")
            lines.append(f"  Total: {cs['total']:,}")
            lines.append(f"  Per variant (avg): {cs['per_variant_avg']:.0f}")
            lines.append(f"  Detectable MDE: {cs['detectable_mde']*100:.1f}%")
            lines.append("")
        
        # Early stopping
        lines.append("Early Stopping Assessment:")
        if early_stop['can_stop']:
            lines.append(f"  ✅ Can stop: {early_stop['reason']}")
            if early_stop['winner']:
                lines.append(f"  Winner: Variant {early_stop['winner']}")
        else:
            lines.append(f"  ⏳ Continue: {early_stop['reason']}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
