# engine/services/warm_start_service.py

"""
Warm-Start Service

Helper functions to create warm-start allocators from historical experiments.
"""

import asyncpg
from typing import Dict, Any, List, Optional
import logging

from engine.core.allocators.warm_start import WarmStartAllocator, AdaptiveWarmStartAllocator

logger = logging.getLogger(__name__)


class WarmStartService:
    """
    Service for creating and managing warm-start allocators
    
    Provides methods to:
    - Extract historical data from past experiments
    - Create warm-start allocators
    - Manage experiment templates
    - Track warm-start performance
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def create_from_experiment(
        self,
        source_experiment_id: str,
        confidence: float = 0.5,
        min_samples: int = 100
    ) -> WarmStartAllocator:
        """
        Create warm-start allocator from previous experiment
        
        Args:
            source_experiment_id: ID of experiment to learn from
            confidence: How much to trust historical data (0.0-1.0)
            min_samples: Minimum samples required to use variant data
        
        Returns:
            WarmStartAllocator with informed priors
        
        Example:
            >>> allocator = await service.create_from_experiment(
            ...     source_experiment_id='exp_previous',
            ...     confidence=0.5
            ... )
        """
        # Fetch historical performance data
        historical_data = await self._extract_historical_data(
            source_experiment_id,
            min_samples
        )
        
        if not historical_data:
            logger.warning(
                f"No usable historical data from {source_experiment_id}, "
                f"using cold-start"
            )
            return WarmStartAllocator({'confidence': 0.0})
        
        # Create allocator
        allocator = WarmStartAllocator({
            'historical_priors': historical_data,
            'confidence': confidence,
            'min_historical_samples': min_samples
        })
        
        logger.info(
            f"Created warm-start allocator from {source_experiment_id}: "
            f"{len(historical_data)} variants with historical data"
        )
        
        return allocator
    
    async def _extract_historical_data(
        self,
        experiment_id: str,
        min_samples: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract historical performance data from experiment
        
        Returns:
            Dict mapping variant IDs/names to performance data
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    ev.id,
                    ev.name,
                    COUNT(a.id) as visits,
                    COUNT(c.id) as conversions,
                    CASE 
                        WHEN COUNT(a.id) > 0 
                        THEN COUNT(c.id)::FLOAT / COUNT(a.id)
                        ELSE 0.0
                    END as conversion_rate
                FROM element_variants ev
                LEFT JOIN assignments a ON a.variant_id = ev.id
                LEFT JOIN conversions c ON c.assignment_id = a.id
                WHERE ev.experiment_id = $1
                GROUP BY ev.id, ev.name
                HAVING COUNT(a.id) >= $2
            """, experiment_id, min_samples)
        
        historical_data = {}
        
        for row in rows:
            # Use both ID and name as keys for flexible matching
            variant_key = row['name']  # Use name for cross-experiment matching
            
            historical_data[variant_key] = {
                'id': str(row['id']),
                'name': row['name'],
                'conversions': row['conversions'],
                'visits': row['visits'],
                'conversion_rate': row['conversion_rate']
            }
        
        return historical_data
    
    async def create_template(
        self,
        user_id: str,
        name: str,
        source_experiment_ids: List[str],
        category: Optional[str] = None,
        description: Optional[str] = None,
        confidence: float = 0.5
    ) -> str:
        """
        Create reusable template from one or more experiments
        
        Templates allow quick warm-start setup for common experiment types.
        
        Args:
            user_id: User creating template
            name: Template name (e.g., "CTA Test Standard")
            source_experiment_ids: Experiments to aggregate data from
            category: Category (e.g., 'cta_test', 'headline_test')
            description: Optional description
            confidence: Default confidence for this template
        
        Returns:
            Template ID
        
        Example:
            >>> template_id = await service.create_template(
            ...     user_id='user_123',
            ...     name='CTA Test Standard',
            ...     source_experiment_ids=['exp_1', 'exp_2', 'exp_3'],
            ...     category='cta_test',
            ...     confidence=0.5
            ... )
        """
        # Aggregate historical data from all source experiments
        aggregated_data = await self._aggregate_experiments(source_experiment_ids)
        
        # Store template
        async with self.db.acquire() as conn:
            template_id = await conn.fetchval("""
                INSERT INTO experiment_templates (
                    user_id,
                    name,
                    description,
                    category,
                    historical_data,
                    source_experiment_ids
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """,
                user_id,
                name,
                description,
                category,
                aggregated_data,  # JSONB
                source_experiment_ids
            )
        
        logger.info(f"Created template {template_id}: {name}")
        
        return str(template_id)
    
    async def _aggregate_experiments(
        self,
        experiment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate historical data from multiple experiments
        
        Combines data from variants with similar names/characteristics.
        """
        # Fetch data from all experiments
        all_data = []
        
        for exp_id in experiment_ids:
            data = await self._extract_historical_data(exp_id, min_samples=50)
            all_data.append(data)
        
        # Aggregate by variant name
        aggregated = {}
        
        for exp_data in all_data:
            for variant_name, variant_data in exp_data.items():
                if variant_name not in aggregated:
                    aggregated[variant_name] = {
                        'total_conversions': 0,
                        'total_visits': 0,
                        'experiments_count': 0
                    }
                
                aggregated[variant_name]['total_conversions'] += variant_data['conversions']
                aggregated[variant_name]['total_visits'] += variant_data['visits']
                aggregated[variant_name]['experiments_count'] += 1
        
        # Calculate aggregated stats
        variants_data = []
        
        for variant_name, stats in aggregated.items():
            variants_data.append({
                'name': variant_name,
                'conversions': stats['total_conversions'],
                'visits': stats['total_visits'],
                'conversion_rate': stats['total_conversions'] / stats['total_visits'],
                'experiments_count': stats['experiments_count']
            })
        
        return {
            'variants': variants_data,
            'total_experiments': len(experiment_ids)
        }
    
    async def create_from_template(
        self,
        template_id: str,
        confidence_override: Optional[float] = None
    ) -> WarmStartAllocator:
        """
        Create warm-start allocator from template
        
        Args:
            template_id: Template ID
            confidence_override: Override template's default confidence
        
        Returns:
            WarmStartAllocator configured from template
        """
        # Fetch template
        async with self.db.acquire() as conn:
            template = await conn.fetchrow("""
                SELECT 
                    historical_data,
                    name
                FROM experiment_templates
                WHERE id = $1
            """, template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Extract variant data
        template_data = template['historical_data']
        
        historical_priors = {}
        for variant_data in template_data['variants']:
            historical_priors[variant_data['name']] = {
                'conversions': variant_data['conversions'],
                'visits': variant_data['visits']
            }
        
        # Determine confidence
        confidence = confidence_override if confidence_override is not None else 0.5
        
        # Create allocator
        allocator = WarmStartAllocator({
            'historical_priors': historical_priors,
            'confidence': confidence
        })
        
        # Update template usage count
        async with self.db.acquire() as conn:
            await conn.execute("""
                UPDATE experiment_templates
                SET times_used = times_used + 1
                WHERE id = $1
            """, template_id)
        
        logger.info(f"Created allocator from template: {template['name']}")
        
        return allocator
    
    async def track_warm_start_performance(
        self,
        experiment_id: str,
        parent_experiment_id: Optional[str] = None,
        template_id: Optional[str] = None,
        confidence: float = 0.5
    ):
        """
        Track warm-start lineage for performance analysis
        
        Records parent-child relationship between experiments
        for later analysis of warm-start effectiveness.
        """
        async with self.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO experiment_lineage (
                    experiment_id,
                    parent_experiment_id,
                    template_id,
                    warm_start_enabled,
                    warm_start_confidence
                ) VALUES ($1, $2, $3, $4, $5)
            """,
                experiment_id,
                parent_experiment_id,
                template_id,
                True,
                confidence
            )
        
        logger.info(
            f"Tracked warm-start lineage: {experiment_id} "
            f"(parent: {parent_experiment_id}, template: {template_id})"
        )
    
    async def get_warm_start_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics on warm-start usage and performance
        
        Returns:
            Dict with usage stats, performance improvements, etc.
        """
        async with self.db.acquire() as conn:
            # Count warm-start vs cold-start
            counts = await conn.fetchrow("""
                SELECT 
                    COUNT(*) FILTER (WHERE warm_start_enabled) as warm_start_count,
                    COUNT(*) FILTER (WHERE NOT warm_start_enabled) as cold_start_count
                FROM experiment_lineage
            """)
            
            # Average improvement
            avg_improvement = await conn.fetchval("""
                SELECT AVG(improvement_vs_cold_start)
                FROM experiment_lineage
                WHERE improvement_vs_cold_start IS NOT NULL
                AND warm_start_enabled = true
            """)
        
        return {
            'warm_start_experiments': counts['warm_start_count'],
            'cold_start_experiments': counts['cold_start_count'],
            'avg_improvement_percent': avg_improvement or 0.0,
        }
