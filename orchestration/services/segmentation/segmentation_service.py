"""
Segmentation Service
Handles segment key lookup, manual rules, and segment performance tracking.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncpg
import logging

logger = logging.getLogger(__name__)

class SegmentationService:
    """
    Logic for mapping context features to specific segment keys.
    Supports both manual rules and automatic clusters.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def get_segment_key(
        self, 
        experiment_id: UUID, 
        normalized_context: Dict[str, Any]
    ) -> str:
        """
        Determines the segment key based on context and experiment config.
        """
        # 1. Check for predicted cluster (Auto mode)
        cluster = normalized_context.get("_predicted_cluster")
        if cluster is not None:
            return f"cluster_{cluster}"
            
        # 2. Check for manual segment rules
        # In a real system, we'd fetch rules from experiment_segmentation_config
        # For now, we'll use a simple attribute-based lookup if configured
        
        async with self.db.acquire() as conn:
            config = await conn.fetchrow(
                "SELECT segment_by FROM experiment_segmentation_config WHERE experiment_id = $1",
                experiment_id
            )
            
        if config and config['segment_by']:
            parts = []
            for attr in config['segment_by']:
                val = self._get_nested(normalized_context, attr)
                if val:
                    parts.append(f"{attr}_{val}")
            
            if parts:
                return "_".join(parts)
                
        return "default"

    def _get_nested(self, data: Dict, path: str) -> Any:
        """Helper to get nested dictionary values."""
        keys = path.split('.')
        rv = data
        for key in keys:
            if isinstance(rv, dict):
                rv = rv.get(key)
            else:
                return None
        return rv

    async def ensure_segment_exists(
        self, 
        experiment_id: UUID, 
        segment_key: str, 
        metadata: Optional[Dict] = None
    ) -> None:
        """Registers a segment if it's the first time we see it."""
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO segments (experiment_id, segment_key, metadata, created_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (experiment_id, segment_key) DO NOTHING
                """,
                experiment_id, segment_key, metadata or {}
            )

    async def update_segment_performance(
        self, 
        experiment_id: UUID, 
        segment_key: str
    ) -> None:
        """Updates aggregate performance metrics for a segment."""
        # This would typically be a background task or a trigger in the DB
        # For now, we implement the logic here
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                WITH stats AS (
                    SELECT 
                        SUM(total_allocations) as allocs,
                        SUM(total_conversions) as convs
                    FROM element_variants
                    WHERE experiment_id = $1 AND segment_key = $2
                )
                UPDATE segments
                SET 
                    total_visitors = stats.allocs,
                    total_conversions = stats.convs,
                    conversion_rate = CASE 
                        WHEN stats.allocs > 0 THEN stats.convs::decimal / stats.allocs 
                        ELSE 0 
                    END,
                    updated_at = NOW()
                FROM stats
                WHERE segments.experiment_id = $1 AND segments.segment_key = $2
                """,
                experiment_id, segment_key
            )
