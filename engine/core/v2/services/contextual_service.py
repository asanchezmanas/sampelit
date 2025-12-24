# engine/services/contextual_service.py

"""
Contextual Bandits Service Layer

Manages segment tracking, performance analysis, and integration
with the database.
"""

import asyncpg
from typing import Dict, Any, List, Optional, Tuple
import json
import logging

from engine.core.allocators.contextual import ContextExtractor

logger = logging.getLogger(__name__)


class ContextualService:
    """
    Service for managing contextual bandits functionality
    
    Responsibilities:
    - Track segment creation and usage
    - Store/retrieve segment performance data
    - Analyze segment lift
    - Generate segment insights
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def track_assignment_with_context(
        self,
        assignment_id: str,
        experiment_id: str,
        variant_id: str,
        raw_context: Dict[str, Any]
    ) -> str:
        """
        Track assignment with context information
        
        Args:
            assignment_id: Assignment ID
            experiment_id: Experiment ID
            variant_id: Selected variant ID
            raw_context: Raw context from request
        
        Returns:
            Segment ID
        """
        # Extract and normalize context
        normalized_context = ContextExtractor.extract(raw_context)
        
        # Build segment key (using default features)
        # In production, would get features from experiment config
        context_features = ['source', 'device']
        
        segment_parts = []
        for feature in sorted(context_features):
            value = normalized_context.get(feature, 'unknown')
            segment_parts.append(f"{feature}:{value}")
        
        segment_key = '|'.join(segment_parts)
        
        # Get or create segment
        async with self.db.acquire() as conn:
            segment_id = await conn.fetchval(
                "SELECT get_or_create_segment($1, $2, $3)",
                experiment_id,
                segment_key,
                json.dumps(normalized_context)
            )
            
            # Update assignment with context
            await conn.execute("""
                UPDATE assignments
                SET context_data = $1,
                    segment_id = $2
                WHERE id = $3
            """, json.dumps(normalized_context), segment_id, assignment_id)
        
        logger.info(
            f"Tracked assignment {assignment_id} "
            f"for segment {segment_key} (id: {segment_id})"
        )
        
        return str(segment_id)
    
    async def update_segment_performance(
        self,
        variant_id: str,
        segment_id: str,
        converted: bool
    ):
        """
        Update segment performance after conversion/visit
        
        Args:
            variant_id: Variant ID
            segment_id: Segment ID
            converted: Whether user converted
        """
        reward = 1.0 if converted else 0.0
        
        async with self.db.acquire() as conn:
            # Update segment stats
            await conn.execute(
                "SELECT update_segment_stats($1, $2)",
                segment_id,
                converted
            )
            
            # Update variant-segment performance
            await conn.execute(
                "SELECT update_variant_segment_performance($1, $2, $3)",
                variant_id,
                segment_id,
                reward
            )
        
        logger.debug(
            f"Updated segment performance: "
            f"variant={variant_id}, segment={segment_id}, converted={converted}"
        )
    
    async def get_segment_states(
        self,
        experiment_id: str,
        variant_ids: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get all segment states for variants
        
        Returns:
            Dict mapping variant_id -> segment_key -> state
            
        Example:
            {
                'variant_a': {
                    'source:instagram|device:mobile': {
                        'alpha': 20.0,
                        'beta': 80.0,
                        'samples': 100
                    },
                    ...
                },
                ...
            }
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    vsp.variant_id,
                    cs.segment_key,
                    vsp.alpha,
                    vsp.beta,
                    vsp.samples,
                    vsp.conversion_rate
                FROM variant_segment_performance vsp
                JOIN context_segments cs ON cs.id = vsp.segment_id
                WHERE cs.experiment_id = $1
                AND vsp.variant_id = ANY($2)
            """, experiment_id, variant_ids)
        
        # Build nested dict
        result = {vid: {} for vid in variant_ids}
        
        for row in rows:
            variant_id = str(row['variant_id'])
            segment_key = row['segment_key']
            
            result[variant_id][segment_key] = {
                'alpha': row['alpha'],
                'beta': row['beta'],
                'samples': row['samples'],
                'conversion_rate': row['conversion_rate']
            }
        
        return result
    
    async def get_top_segments(
        self,
        experiment_id: str,
        limit: int = 10,
        min_samples: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get top performing segments for experiment
        
        Args:
            experiment_id: Experiment ID
            limit: Max segments to return
            min_samples: Minimum samples required
        
        Returns:
            List of segment dicts with performance data
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    segment_key,
                    context_features,
                    total_visits,
                    total_conversions,
                    overall_conversion_rate,
                    best_variant
                FROM v_segment_performance
                WHERE experiment_id = $1
                AND total_visits >= $2
                ORDER BY overall_conversion_rate DESC
                LIMIT $3
            """, experiment_id, min_samples, limit)
        
        return [
            {
                'segment_key': row['segment_key'],
                'context': row['context_features'],
                'visits': row['total_visits'],
                'conversions': row['total_conversions'],
                'conversion_rate': row['overall_conversion_rate'],
                'best_variant': row['best_variant']
            }
            for row in rows
        ]
    
    async def get_segment_lift_analysis(
        self,
        experiment_id: str,
        min_samples: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze which segments perform significantly different from global
        
        Returns:
            List of segments with lift data
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    segment_key,
                    context_features,
                    variant_name,
                    segment_cr,
                    segment_samples,
                    global_cr,
                    lift_percent,
                    segment_traffic
                FROM v_segment_lift
                WHERE segment_samples >= $1
                ORDER BY ABS(lift_percent) DESC NULLS LAST
                LIMIT 20
            """, min_samples)
        
        # Filter to experiment (view doesn't have experiment_id filter)
        # In production, would join with context_segments table
        
        return [
            {
                'segment_key': row['segment_key'],
                'context': row['context_features'],
                'variant': row['variant_name'],
                'segment_cr': row['segment_cr'],
                'global_cr': row['global_cr'],
                'lift_percent': row['lift_percent'],
                'traffic': row['segment_traffic'],
                'samples': row['segment_samples']
            }
            for row in rows
        ]
    
    async def get_segment_insights(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        Generate actionable insights about segments
        
        Returns:
            Dict with insights and recommendations
        """
        # Get top segments
        top_segments = await self.get_top_segments(experiment_id, limit=5)
        
        # Get lift analysis
        lift_data = await self.get_segment_lift_analysis(experiment_id)
        
        # Identify high-performing segments
        high_performers = [
            s for s in lift_data 
            if s['lift_percent'] and s['lift_percent'] > 20
        ]
        
        # Identify underperformers
        underperformers = [
            s for s in lift_data 
            if s['lift_percent'] and s['lift_percent'] < -20
        ]
        
        # Get total traffic distribution
        async with self.db.acquire() as conn:
            traffic_dist = await conn.fetch("""
                SELECT 
                    segment_key,
                    total_visits,
                    total_visits::FLOAT / SUM(total_visits) OVER () * 100 as traffic_percent
                FROM context_segments
                WHERE experiment_id = $1
                ORDER BY total_visits DESC
                LIMIT 10
            """, experiment_id)
        
        return {
            'summary': {
                'total_segments': len(top_segments),
                'high_performers': len(high_performers),
                'underperformers': len(underperformers)
            },
            'top_segments': top_segments,
            'high_performing_segments': high_performers[:5],
            'underperforming_segments': underperformers[:5],
            'traffic_distribution': [
                {
                    'segment': row['segment_key'],
                    'visits': row['total_visits'],
                    'percent': row['traffic_percent']
                }
                for row in traffic_dist
            ],
            'recommendations': self._generate_recommendations(
                high_performers,
                underperformers
            )
        }
    
    def _generate_recommendations(
        self,
        high_performers: List[Dict],
        underperformers: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if high_performers:
            top = high_performers[0]
            recommendations.append(
                f"🎯 Focus on {top['segment_key']}: "
                f"{top['lift_percent']:.0f}% lift with variant '{top['variant']}'"
            )
        
        if underperformers:
            bottom = underperformers[0]
            recommendations.append(
                f"⚠️ Segment {bottom['segment_key']} underperforming: "
                f"{abs(bottom['lift_percent']):.0f}% worse than average"
            )
        
        if len(high_performers) >= 3:
            recommendations.append(
                f"💡 Consider creating separate experiments for top {len(high_performers)} segments"
            )
        
        return recommendations
    
    async def refresh_analytics(self):
        """Refresh materialized view for analytics"""
        async with self.db.acquire() as conn:
            await conn.execute("SELECT refresh_segment_analytics()")
        
        logger.info("Refreshed segment analytics materialized view")
