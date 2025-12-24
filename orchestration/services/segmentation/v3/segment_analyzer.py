"""
Segment Analyzer

Analyzes segment performance and generates actionable insights.

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from uuid import UUID
from scipy import stats

logger = logging.getLogger(__name__)


class SegmentAnalyzer:
    """
    Analyzes segment performance and generates insights
    
    Capabilities:
    - Identify high/low performing segments
    - Calculate lift vs global baseline
    - Statistical significance testing
    - Generate actionable recommendations
    - Detect anomalies
    
    Example:
        >>> analyzer = SegmentAnalyzer(db_pool)
        >>> 
        >>> insights = await analyzer.analyze_experiment(experiment_id)
        >>> 
        >>> print(insights['summary'])
        >>> for segment in insights['high_performers']:
        ...     print(f"{segment['segment_key']}: +{segment['lift_percent']:.0f}% lift")
    """
    
    def __init__(self, db_pool):
        self.db = db_pool
        self.logger = logging.getLogger(f"{__name__}.SegmentAnalyzer")
    
    # ========================================================================
    # MAIN ANALYSIS
    # ========================================================================
    
    async def analyze_experiment(
        self,
        experiment_id: UUID,
        min_samples: int = 50
    ) -> Dict[str, Any]:
        """
        Comprehensive experiment analysis
        
        Args:
            experiment_id: Experiment UUID
            min_samples: Minimum samples for reliable analysis
        
        Returns:
            Dict with insights:
            {
                'summary': {...},
                'top_segments': [...],
                'high_performers': [...],
                'underperformers': [...],
                'statistical_tests': [...],
                'recommendations': [...]
            }
        """
        self.logger.info(f"Analyzing experiment {experiment_id}")
        
        # ─────────────────────────────────────────────────────────────
        # Fetch data
        # ─────────────────────────────────────────────────────────────
        segment_data = await self._fetch_segment_data(experiment_id, min_samples)
        
        if not segment_data:
            return {
                'summary': {'message': 'No segments with sufficient data'},
                'top_segments': [],
                'high_performers': [],
                'underperformers': [],
                'statistical_tests': [],
                'recommendations': []
            }
        
        # ─────────────────────────────────────────────────────────────
        # Calculate global baseline
        # ─────────────────────────────────────────────────────────────
        global_baseline = await self._calculate_global_baseline(experiment_id)
        
        # ─────────────────────────────────────────────────────────────
        # Calculate lifts
        # ─────────────────────────────────────────────────────────────
        lifts = self._calculate_lifts(segment_data, global_baseline)
        
        # ─────────────────────────────────────────────────────────────
        # Statistical significance tests
        # ─────────────────────────────────────────────────────────────
        stat_tests = self._run_statistical_tests(
            segment_data,
            global_baseline
        )
        
        # ─────────────────────────────────────────────────────────────
        # Identify high/low performers
        # ─────────────────────────────────────────────────────────────
        high_performers = [
            lift for lift in lifts
            if lift['lift_percent'] > 20 and lift['is_significant']
        ]
        high_performers.sort(key=lambda x: x['lift_percent'], reverse=True)
        
        underperformers = [
            lift for lift in lifts
            if lift['lift_percent'] < -20 and lift['is_significant']
        ]
        underperformers.sort(key=lambda x: x['lift_percent'])
        
        # ─────────────────────────────────────────────────────────────
        # Generate recommendations
        # ─────────────────────────────────────────────────────────────
        recommendations = self._generate_recommendations(
            high_performers,
            underperformers,
            segment_data
        )
        
        # ─────────────────────────────────────────────────────────────
        # Summary stats
        # ─────────────────────────────────────────────────────────────
        summary = {
            'total_segments': len(segment_data),
            'significant_segments': sum(1 for t in stat_tests if t['is_significant']),
            'high_performers': len(high_performers),
            'underperformers': len(underperformers),
            'global_conversion_rate': global_baseline['conversion_rate'],
            'best_segment': high_performers[0] if high_performers else None,
            'worst_segment': underperformers[0] if underperformers else None
        }
        
        return {
            'summary': summary,
            'top_segments': segment_data[:10],  # Top 10 by traffic
            'high_performers': high_performers[:5],
            'underperformers': underperformers[:5],
            'statistical_tests': stat_tests,
            'recommendations': recommendations
        }
    
    # ========================================================================
    # DATA FETCHING
    # ========================================================================
    
    async def _fetch_segment_data(
        self,
        experiment_id: UUID,
        min_samples: int
    ) -> List[Dict[str, Any]]:
        """Fetch segment performance data"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    cs.segment_key,
                    cs.context_features,
                    cs.total_visits,
                    cs.total_conversions,
                    CASE 
                        WHEN cs.total_visits > 0
                        THEN cs.total_conversions::FLOAT / cs.total_visits
                        ELSE 0.0
                    END as conversion_rate
                FROM context_segments cs
                WHERE cs.experiment_id = $1
                  AND cs.total_visits >= $2
                ORDER BY cs.total_visits DESC
            """, experiment_id, min_samples)
        
        return [
            {
                'segment_key': row['segment_key'],
                'context': row['context_features'],
                'visits': row['total_visits'],
                'conversions': row['total_conversions'],
                'conversion_rate': row['conversion_rate']
            }
            for row in rows
        ]
    
    async def _calculate_global_baseline(
        self,
        experiment_id: UUID
    ) -> Dict[str, Any]:
        """Calculate global baseline metrics"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    SUM(total_visitors) as total_visits,
                    SUM(total_conversions) as total_conversions
                FROM element_variants
                WHERE experiment_id = $1
                  AND status = 'active'
            """, experiment_id)
        
        total_visits = row['total_visits'] or 0
        total_conversions = row['total_conversions'] or 0
        
        conversion_rate = (
            total_conversions / total_visits 
            if total_visits > 0 
            else 0.0
        )
        
        return {
            'visits': total_visits,
            'conversions': total_conversions,
            'conversion_rate': conversion_rate
        }
    
    # ========================================================================
    # LIFT CALCULATION
    # ========================================================================
    
    def _calculate_lifts(
        self,
        segment_data: List[Dict[str, Any]],
        global_baseline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calculate lift for each segment vs global baseline
        
        Lift = (segment_rate - baseline_rate) / baseline_rate * 100
        """
        lifts = []
        baseline_rate = global_baseline['conversion_rate']
        
        for segment in segment_data:
            segment_rate = segment['conversion_rate']
            
            # Calculate lift
            if baseline_rate > 0:
                lift_percent = (
                    (segment_rate - baseline_rate) / baseline_rate * 100
                )
            else:
                lift_percent = 0.0
            
            # Statistical significance (Z-test for proportions)
            is_significant, p_value = self._test_significance(
                segment['conversions'],
                segment['visits'],
                global_baseline['conversions'],
                global_baseline['visits']
            )
            
            lifts.append({
                'segment_key': segment['segment_key'],
                'context': segment['context'],
                'segment_rate': segment_rate,
                'baseline_rate': baseline_rate,
                'lift_percent': lift_percent,
                'absolute_lift': segment_rate - baseline_rate,
                'visits': segment['visits'],
                'conversions': segment['conversions'],
                'is_significant': is_significant,
                'p_value': p_value
            })
        
        # Sort by absolute lift
        lifts.sort(key=lambda x: abs(x['lift_percent']), reverse=True)
        
        return lifts
    
    def _test_significance(
        self,
        segment_conversions: int,
        segment_visits: int,
        global_conversions: int,
        global_visits: int,
        alpha: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Test if segment performance is significantly different from global
        
        Uses Z-test for proportions.
        
        Returns:
            (is_significant, p_value)
        """
        if segment_visits == 0 or global_visits == 0:
            return False, 1.0
        
        # Proportions
        p1 = segment_conversions / segment_visits
        p2 = global_conversions / global_visits
        
        # Pooled proportion
        p_pooled = (segment_conversions + global_conversions) / (segment_visits + global_visits)
        
        # Standard error
        se = np.sqrt(
            p_pooled * (1 - p_pooled) * (1/segment_visits + 1/global_visits)
        )
        
        if se == 0:
            return False, 1.0
        
        # Z-statistic
        z = (p1 - p2) / se
        
        # Two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        is_significant = p_value < alpha
        
        return is_significant, float(p_value)
    
    # ========================================================================
    # STATISTICAL TESTS
    # ========================================================================
    
    def _run_statistical_tests(
        self,
        segment_data: List[Dict[str, Any]],
        global_baseline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run statistical tests for each segment
        """
        tests = []
        
        for segment in segment_data:
            is_sig, p_value = self._test_significance(
                segment['conversions'],
                segment['visits'],
                global_baseline['conversions'],
                global_baseline['visits']
            )
            
            # Effect size (Cohen's h for proportions)
            effect_size = self._calculate_effect_size(
                segment['conversion_rate'],
                global_baseline['conversion_rate']
            )
            
            tests.append({
                'segment_key': segment['segment_key'],
                'is_significant': is_sig,
                'p_value': p_value,
                'effect_size': effect_size,
                'effect_interpretation': self._interpret_effect_size(effect_size)
            })
        
        return tests
    
    def _calculate_effect_size(
        self,
        p1: float,
        p2: float
    ) -> float:
        """
        Calculate Cohen's h (effect size for proportions)
        
        h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
        
        Interpretation:
        - 0.2: small
        - 0.5: medium
        - 0.8: large
        """
        phi1 = 2 * np.arcsin(np.sqrt(p1))
        phi2 = 2 * np.arcsin(np.sqrt(p2))
        
        h = phi1 - phi2
        
        return float(abs(h))
    
    def _interpret_effect_size(self, h: float) -> str:
        """Interpret Cohen's h"""
        if h < 0.2:
            return 'negligible'
        elif h < 0.5:
            return 'small'
        elif h < 0.8:
            return 'medium'
        else:
            return 'large'
    
    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================
    
    def _generate_recommendations(
        self,
        high_performers: List[Dict],
        underperformers: List[Dict],
        segment_data: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # High performers
        if high_performers:
            top = high_performers[0]
            recommendations.append(
                f"🎯 Focus marketing on {top['segment_key']}: "
                f"+{top['lift_percent']:.0f}% lift "
                f"(p={top['p_value']:.4f})"
            )
            
            if len(high_performers) >= 3:
                recommendations.append(
                    f"💡 Top 3 segments account for significant performance - "
                    f"consider dedicated campaigns"
                )
        
        # Underperformers
        if underperformers:
            bottom = underperformers[0]
            recommendations.append(
                f"⚠️ Segment {bottom['segment_key']} underperforming: "
                f"{bottom['lift_percent']:.0f}% worse "
                f"(p={bottom['p_value']:.4f})"
            )
            
            recommendations.append(
                f"🔧 Consider A/B testing different variants for underperforming segments"
            )
        
        # Traffic distribution
        total_traffic = sum(s['visits'] for s in segment_data)
        top_3_traffic = sum(s['visits'] for s in segment_data[:3])
        top_3_percent = (top_3_traffic / total_traffic * 100) if total_traffic > 0 else 0
        
        if top_3_percent > 70:
            recommendations.append(
                f"📊 Top 3 segments represent {top_3_percent:.0f}% of traffic - "
                f"focus optimization efforts here"
            )
        
        # Segment diversity
        if len(segment_data) > 20:
            recommendations.append(
                f"🌳 High segment diversity ({len(segment_data)} segments) - "
                f"consider hierarchical clustering for better organization"
            )
        elif len(segment_data) < 5:
            recommendations.append(
                f"📍 Low segment diversity ({len(segment_data)} segments) - "
                f"consider adding more context features"
            )
        
        return recommendations
    
    # ========================================================================
    # ADVANCED ANALYTICS
    # ========================================================================
    
    async def find_similar_segments(
        self,
        experiment_id: UUID,
        reference_segment_key: str,
        n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find segments with similar performance to reference
        
        Useful for identifying patterns across segments.
        """
        # Fetch all segments
        segment_data = await self._fetch_segment_data(experiment_id, min_samples=50)
        
        # Find reference
        reference = next(
            (s for s in segment_data if s['segment_key'] == reference_segment_key),
            None
        )
        
        if not reference:
            return []
        
        # Calculate similarity (based on conversion rate)
        similarities = []
        ref_rate = reference['conversion_rate']
        
        for segment in segment_data:
            if segment['segment_key'] == reference_segment_key:
                continue
            
            # Similarity = 1 - abs(rate1 - rate2)
            similarity = 1.0 - abs(segment['conversion_rate'] - ref_rate)
            
            similarities.append({
                'segment_key': segment['segment_key'],
                'context': segment['context'],
                'conversion_rate': segment['conversion_rate'],
                'similarity': similarity,
                'rate_diff': segment['conversion_rate'] - ref_rate
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:n]
    
    async def detect_anomalies(
        self,
        experiment_id: UUID,
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous segments (outliers)
        
        Uses Z-score to identify segments with unusual performance.
        
        Args:
            experiment_id: Experiment UUID
            threshold: Z-score threshold (default: 3.0 = 99.7% confidence)
        
        Returns:
            List of anomalous segments
        """
        segment_data = await self._fetch_segment_data(experiment_id, min_samples=50)
        
        if len(segment_data) < 3:
            return []
        
        # Calculate mean and std of conversion rates
        rates = [s['conversion_rate'] for s in segment_data]
        mean_rate = np.mean(rates)
        std_rate = np.std(rates)
        
        if std_rate == 0:
            return []
        
        # Find anomalies
        anomalies = []
        
        for segment in segment_data:
            z_score = abs((segment['conversion_rate'] - mean_rate) / std_rate)
            
            if z_score > threshold:
                anomalies.append({
                    'segment_key': segment['segment_key'],
                    'context': segment['context'],
                    'conversion_rate': segment['conversion_rate'],
                    'z_score': float(z_score),
                    'deviation': segment['conversion_rate'] - mean_rate,
                    'is_positive': segment['conversion_rate'] > mean_rate
                })
        
        # Sort by z-score
        anomalies.sort(key=lambda x: x['z_score'], reverse=True)
        
        return anomalies
