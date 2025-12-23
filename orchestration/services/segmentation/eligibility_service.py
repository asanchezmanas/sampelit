"""
Eligibility Service for Segmentation
Analyzes traffic patterns to recommend segmentation strategies.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncpg
import logging

logger = logging.getLogger(__name__)

class EligibilityService:
    """
    Determines if an experiment has enough traffic for reliable segmentation.
    Thresholds:
    - Manual: > 1,000 visitors/day
    - Auto (K-means): > 10,000 visitors/day
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def analyze_eligibility(self, experiment_id: UUID) -> Dict[str, Any]:
        """
        Analyzes traffic and returns recommendations.
        """
        async with self.db.acquire() as conn:
            # Get visitors in last 7 days
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_visitors,
                    COUNT(*) / 7.0 as daily_avg
                FROM assignments
                WHERE experiment_id = $1 
                  AND assigned_at > NOW() - INTERVAL '7 days'
                """,
                experiment_id
            )
            
            # Get current configuration
            config = await conn.fetchrow(
                "SELECT mode FROM experiment_segmentation_config WHERE experiment_id = $1",
                experiment_id
            )
            
        total = stats['total_visitors'] if stats else 0
        daily = stats['daily_avg'] if stats else 0
        current_mode = config['mode'] if config else 'disabled'
        
        status = "ineligible"
        recommendation = "Continue collecting data until daily traffic reaches 1,000 visitors."
        
        if daily >= 10000:
            status = "eligible_auto"
            recommendation = "Traffic is high enough for Automatic Clustering (K-means)."
        elif daily >= 1000:
            status = "eligible_manual"
            recommendation = "Traffic is sufficient for Manual Segmentation by Source/Device."
            
        return {
            "experiment_id": str(experiment_id),
            "daily_avg": daily,
            "total_sample": total,
            "status": status,
            "current_mode": current_mode,
            "recommendation": recommendation
        }

    async def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """Finds all experiments that could benefit from segmentation."""
        # Simple implementation: list active experiments and analyze them
        async with self.db.acquire() as conn:
            experiments = await conn.fetch(
                "SELECT id, name FROM experiments WHERE status = 'running'"
            )
            
        results = []
        for exp in experiments:
            analysis = await self.analyze_eligibility(exp['id'])
            if analysis['status'] != "ineligible":
                results.append({
                    "name": exp['name'],
                    **analysis
                })
        return results
