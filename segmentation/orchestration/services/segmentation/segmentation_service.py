# orchestration/services/segmentation/segmentation_service.py

"""
Segmentation Service - Main Orchestrator

Handles:
- Manual segmentation (user-defined segments)
- Auto-clustering
- Segment creation and management
"""

from typing import Dict, Any, List, Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

class SegmentationService:
    """
    Main service for segmentation operations
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def get_segment_key(
        self,
        experiment_id: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Determine segment key for user based on experiment config
        
        Returns:
            - 'default' if segmentation disabled
            - 'source:instagram' for manual segmentation
            - 'cluster_2' for auto-clustering
        
        This is the main entry point called during allocation
        """
        
        # Get segmentation config
        async with self.db.acquire() as conn:
            config = await conn.fetchrow(
                "SELECT * FROM experiment_segmentation_config WHERE experiment_id = $1",
                experiment_id
            )
        
        if not config or config['mode'] == 'disabled':
            return 'default'
        
        # Manual segmentation
        if config['mode'] == 'manual':
            segment_by = config.get('segment_by', [])
            if not segment_by:
                return 'default'
            
            return self._build_manual_segment_key(context, segment_by)
        
        # Auto-clustering
        elif config['mode'] == 'auto':
            # This will be filled by clustering_service.predict_cluster()
            # For now, return a placeholder
            cluster_key = context.get('_predicted_cluster')
            if cluster_key:
                return cluster_key
            
            # Fallback if prediction failed
            return 'default'
        
        return 'default'
    
    def _build_manual_segment_key(
        self,
        context: Dict[str, Any],
        segment_by: List[str]
    ) -> str:
        """
        Build segment key from context fields
        
        Examples:
        - segment_by=['source'] → 'source:instagram'
        - segment_by=['source', 'device'] → 'source:instagram|device:mobile'
        """
        
        parts = []
        for field in segment_by:
            value = context.get(field, 'unknown')
            parts.append(f"{field}:{value}")
        
        return "|".join(parts)
    
    async def ensure_segment_exists(
        self,
        experiment_id: str,
        segment_key: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Ensure segment record exists
        
        Creates segment if first time seeing it
        """
        
        if segment_key == 'default':
            return
        
        async with self.db.acquire() as conn:
            # Check if exists
            exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM experiment_segments
                    WHERE experiment_id = $1 AND segment_key = $2
                )
                """,
                experiment_id, segment_key
            )
            
            if not exists:
                # Extract characteristics from segment_key
                characteristics = self._parse_segment_key(segment_key, context)
                
                # Generate display name
                display_name = self._generate_segment_display_name(segment_key)
                
                # Create segment
                await conn.execute(
                    """
                    INSERT INTO experiment_segments (
                        experiment_id, segment_key, segment_type,
                        display_name, characteristics
                    ) VALUES ($1, $2, 'manual', $3, $4)
                    ON CONFLICT (experiment_id, segment_key) DO NOTHING
                    """,
                    experiment_id,
                    segment_key,
                    display_name,
                    characteristics
                )
                
                logger.info(f"Created new segment: {segment_key} for experiment {experiment_id}")
    
    def _parse_segment_key(
        self, 
        segment_key: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse segment_key back into characteristics
        
        'source:instagram|device:mobile' → {'source': 'instagram', 'device': 'mobile'}
        """
        
        if segment_key.startswith('cluster_'):
            return {'cluster': segment_key}
        
        characteristics = {}
        parts = segment_key.split('|')
        
        for part in parts:
            if ':' in part:
                field, value = part.split(':', 1)
                characteristics[field] = value
        
        return characteristics
    
    def _generate_segment_display_name(self, segment_key: str) -> str:
        """
        Generate human-readable name from segment key
        
        Examples:
        - 'source:instagram' → 'Instagram Traffic'
        - 'source:google|device:mobile' → 'Google Mobile Users'
        - 'cluster_2' → 'Cluster 2'
        """
        
        if segment_key.startswith('cluster_'):
            cluster_num = segment_key.replace('cluster_', '')
            return f'Cluster {cluster_num}'
        
        parts = segment_key.split('|')
        descriptors = []
        
        for part in parts:
            if ':' in part:
                field, value = part.split(':', 1)
                
                if field == 'source':
                    descriptors.append(value.title())
                elif field == 'device':
                    descriptors.append(value.title())
                elif field == 'geo':
                    descriptors.append(value.upper())
        
        if descriptors:
            if len(descriptors) == 1:
                return f"{descriptors[0]} Traffic"
            else:
                return " ".join(descriptors) + " Users"
        
        return segment_key.title()
    
    async def get_segment_stats(
        self, 
        experiment_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get performance stats for all segments
        
        Returns list of segments with allocations, conversions, CR
        """
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    es.segment_key,
                    es.segment_type,
                    es.display_name,
                    es.characteristics,
                    COUNT(DISTINCT a.id) as allocations,
                    COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL) as conversions,
                    CASE 
                        WHEN COUNT(DISTINCT a.id) > 0
                        THEN COUNT(DISTINCT a.id) FILTER (WHERE a.converted_at IS NOT NULL)::FLOAT / 
                             COUNT(DISTINCT a.id)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM experiment_segments es
                LEFT JOIN assignments a ON 
                    es.experiment_id = a.experiment_id 
                    AND es.segment_key = a.segment_key
                WHERE es.experiment_id = $1
                GROUP BY es.segment_key, es.segment_type, es.display_name, es.characteristics
                ORDER BY allocations DESC
                """,
                experiment_id
            )
        
        return [
            {
                'segment_key': row['segment_key'],
                'segment_type': row['segment_type'],
                'display_name': row['display_name'],
                'characteristics': row['characteristics'],
                'allocations': row['allocations'],
                'conversions': row['conversions'],
                'conversion_rate': float(row['conversion_rate'])
            }
            for row in rows
        ]
    
    async def update_segment_performance(
        self, 
        experiment_id: str, 
        segment_key: str
    ) -> None:
        """
        Update cached performance metrics for segment
        
        Called periodically or after significant events
        """
        
        async with self.db.acquire() as conn:
            # Calculate from assignments
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as allocations,
                    COUNT(*) FILTER (WHERE converted_at IS NOT NULL) as conversions,
                    CASE 
                        WHEN COUNT(*) > 0
                        THEN COUNT(*) FILTER (WHERE converted_at IS NOT NULL)::FLOAT / COUNT(*)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM assignments
                WHERE experiment_id = $1 AND segment_key = $2
                """,
                experiment_id, segment_key
            )
            
            # Update segment record
            await conn.execute(
                """
                UPDATE experiment_segments
                SET 
                    total_allocations = $3,
                    total_conversions = $4,
                    conversion_rate = $5,
                    updated_at = NOW()
                WHERE experiment_id = $1 AND segment_key = $2
                """,
                experiment_id,
                segment_key,
                stats['allocations'],
                stats['conversions'],
                stats['conversion_rate']
            )
    
    async def get_best_performing_segment(
        self, 
        experiment_id: str,
        min_samples: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Get best performing segment
        
        Useful for recommendations
        """
        
        segments = await self.get_segment_stats(experiment_id)
        
        # Filter by minimum samples
        qualified = [s for s in segments if s['allocations'] >= min_samples]
        
        if not qualified:
            return None
        
        # Return highest CR
        return max(qualified, key=lambda s: s['conversion_rate'])
    
    async def compare_segments(
        self, 
        experiment_id: str,
        segment_key_a: str,
        segment_key_b: str
    ) -> Dict[str, Any]:
        """
        Statistical comparison between two segments
        
        Returns lift, significance, etc.
        """
        
        async with self.db.acquire() as conn:
            stats_a = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as n,
                    COUNT(*) FILTER (WHERE converted_at IS NOT NULL) as conversions
                FROM assignments
                WHERE experiment_id = $1 AND segment_key = $2
                """,
                experiment_id, segment_key_a
            )
            
            stats_b = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as n,
                    COUNT(*) FILTER (WHERE converted_at IS NOT NULL) as conversions
                FROM assignments
                WHERE experiment_id = $1 AND segment_key = $2
                """,
                experiment_id, segment_key_b
            )
        
        # Calculate conversion rates
        cr_a = stats_a['conversions'] / stats_a['n'] if stats_a['n'] > 0 else 0
        cr_b = stats_b['conversions'] / stats_b['n'] if stats_b['n'] > 0 else 0
        
        # Calculate lift
        if cr_a > 0:
            lift = ((cr_b - cr_a) / cr_a) * 100
        else:
            lift = 0
        
        # Simple z-test for significance
        from scipy import stats as scipy_stats
        import numpy as np
        
        if stats_a['n'] > 30 and stats_b['n'] > 30:
            # Z-test for proportions
            pooled_cr = (stats_a['conversions'] + stats_b['conversions']) / (stats_a['n'] + stats_b['n'])
            
            se = np.sqrt(pooled_cr * (1 - pooled_cr) * (1/stats_a['n'] + 1/stats_b['n']))
            
            if se > 0:
                z_score = (cr_a - cr_b) / se
                p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z_score)))
            else:
                p_value = 1.0
            
            significant = p_value < 0.05
        else:
            p_value = None
            significant = False
        
        return {
            'segment_a': segment_key_a,
            'segment_b': segment_key_b,
            'cr_a': cr_a,
            'cr_b': cr_b,
            'lift': lift,
            'p_value': p_value,
            'significant': significant,
            'winner': segment_key_b if lift > 0 and significant else segment_key_a
        }
