# data_access/repositories/variant_segment_repository.py
"""
Variant Segment Repository

Maneja el estado Thompson Sampling separado por segmento.

ARQUITECTURA CORRECTA:
- Variantes son únicas (contenido, diseño)
- Estado Thompson es por (variant_id, segment_key)
- Permite que misma variante tenga diferente performance en diferentes segmentos

Copyright (c) 2024 Samplit Technologies
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

logger = logging.getLogger(__name__)


class VariantSegmentRepository:
    """
    Repository para estado Thompson Sampling por segmento
    
    ✅ Nueva arquitectura correcta:
    - variant_segment_state table
    - Separación de contenido (variant) y performance (segment state)
    """
    
    def __init__(self, db_pool):
        self.db = db_pool
        self.logger = logging.getLogger(f"{__name__}.VariantSegmentRepository")
    
    # ========================================================================
    # INITIALIZATION & COLD START
    # ========================================================================
    
    async def ensure_segment_state(
        self,
        variant_id: str,
        segment_key: str,
        experiment_id: str,
        warm_start: bool = False
    ) -> None:
        """
        Asegura que existe estado para (variant, segment)
        
        Args:
            variant_id: ID de la variante
            segment_key: Clave del segmento (ej: "mobile", "us_traffic")
            experiment_id: ID del experimento
            warm_start: Si True, inicializa con datos globales (mejor que prior vacío)
        
        Warm Start Strategy:
            Si es un nuevo segmento, en vez de empezar con Beta(1, 1),
            podemos usar datos del segmento "global" o "default" como prior.
            Esto acelera convergencia.
        """
        
        async with self.db.acquire() as conn:
            # Check if exists
            exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM variant_segment_state
                    WHERE variant_id = $1 AND segment_key = $2
                )
                """,
                UUID(variant_id),
                segment_key
            )
            
            if exists:
                return
            
            # Determinar prior para nuevo segmento
            if warm_start:
                # Usar datos del segmento "default" o global como prior
                global_state = await conn.fetchrow(
                    """
                    SELECT alpha, beta
                    FROM variant_segment_state
                    WHERE variant_id = $1 AND segment_key = 'default'
                    """,
                    UUID(variant_id)
                )
                
                if global_state:
                    initial_alpha = global_state['alpha']
                    initial_beta = global_state['beta']
                    self.logger.info(
                        f"Warm start for {variant_id}/{segment_key}: "
                        f"α={initial_alpha:.2f}, β={initial_beta:.2f}"
                    )
                else:
                    initial_alpha = 1.0
                    initial_beta = 1.0
            else:
                # Uniform prior (no assumptions)
                initial_alpha = 1.0
                initial_beta = 1.0
            
            # Create state
            await conn.execute(
                """
                INSERT INTO variant_segment_state (
                    variant_id, segment_key, experiment_id,
                    alpha, beta
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (variant_id, segment_key) DO NOTHING
                """,
                UUID(variant_id),
                segment_key,
                UUID(experiment_id),
                initial_alpha,
                initial_beta
            )
            
            self.logger.debug(
                f"Created state for variant {variant_id} in segment {segment_key}"
            )
    
    # ========================================================================
    # THOMPSON SAMPLING STATE RETRIEVAL
    # ========================================================================
    
    async def get_variants_for_segment(
        self,
        experiment_id: str,
        segment_key: str,
        element_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las variantes con su estado Thompson para un segmento
        
        Esta es la query crítica para allocation.
        
        Returns:
            [
                {
                    'id': 'variant_uuid',
                    'name': 'Variant A',
                    'content': {...},
                    '_internal_state': {
                        'success_count': alpha - 1,
                        'failure_count': beta - 1,
                        'samples': total_allocations,
                        'alpha': alpha,
                        'beta': beta
                    }
                },
                ...
            ]
        """
        
        query = """
        SELECT 
            ev.id,
            ev.name,
            ev.content,
            ev.element_id,
            
            -- Thompson Sampling state
            vss.alpha,
            vss.beta,
            vss.total_allocations,
            vss.total_conversions,
            vss.conversion_rate,
            
            -- Metadata
            vss.last_allocation_at,
            vss.confidence_lower,
            vss.confidence_upper
            
        FROM element_variants ev
        LEFT JOIN variant_segment_state vss 
            ON ev.id = vss.variant_id 
            AND vss.segment_key = $2
        WHERE ev.experiment_id = $1
          AND ev.is_active = TRUE
        """
        
        params = [UUID(experiment_id), segment_key]
        
        if element_id:
            query += " AND ev.element_id = $3"
            params.append(UUID(element_id))
        
        query += " ORDER BY ev.variant_order"
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        variants = []
        for row in rows:
            # Si no hay estado (nuevo segmento), usar priors
            alpha = row['alpha'] if row['alpha'] is not None else 1.0
            beta = row['beta'] if row['beta'] is not None else 1.0
            samples = row['total_allocations'] if row['total_allocations'] is not None else 0
            
            variants.append({
                'id': str(row['id']),
                'name': row['name'],
                'content': row['content'],
                'element_id': str(row['element_id']) if row['element_id'] else None,
                '_internal_state': {
                    'success_count': int(alpha),  # Para Thompson Sampling
                    'failure_count': int(beta),
                    'samples': samples,
                    'alpha': float(alpha),
                    'beta': float(beta),
                    'conversion_rate': float(row['conversion_rate']) if row['conversion_rate'] else 0.0
                }
            })
        
        self.logger.debug(
            f"Retrieved {len(variants)} variants for segment {segment_key} "
            f"in experiment {experiment_id}"
        )
        
        return variants
    
    # ========================================================================
    # ALLOCATION & CONVERSION TRACKING
    # ========================================================================
    
    async def increment_allocation(
        self,
        variant_id: str,
        segment_key: str
    ) -> None:
        """
        Incrementa contador de allocations para (variant, segment)
        """
        
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE variant_segment_state
                SET 
                    total_allocations = total_allocations + 1,
                    last_allocation_at = NOW(),
                    updated_at = NOW()
                WHERE variant_id = $1 AND segment_key = $2
                """,
                UUID(variant_id),
                segment_key
            )
    
    async def increment_conversion(
        self,
        variant_id: str,
        segment_key: str
    ) -> None:
        """
        Incrementa conversión y actualiza Thompson Sampling state
        
        Actualiza automáticamente alpha, beta, y conversion_rate
        """
        
        async with self.db.acquire() as conn:
            # Usar función SQL que hace todo atómicamente
            await conn.execute(
                "SELECT increment_variant_segment_conversion($1, $2)",
                UUID(variant_id),
                segment_key
            )
            
            self.logger.debug(
                f"Incremented conversion for variant {variant_id} in segment {segment_key}"
            )
    
    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================
    
    async def get_segment_performance(
        self,
        experiment_id: str,
        segment_key: str
    ) -> Dict[str, Any]:
        """
        Obtiene resumen de performance para un segmento específico
        """
        
        async with self.db.acquire() as conn:
            # Usar vista materializada si existe
            result = await conn.fetchrow(
                """
                SELECT 
                    segment_key,
                    segment_description,
                    variant_count,
                    total_visitors,
                    total_conversions,
                    avg_conversion_rate,
                    best_variant_name,
                    data_quality,
                    last_updated
                FROM segment_performance_summary
                WHERE experiment_id = $1 AND segment_key = $2
                """,
                UUID(experiment_id),
                segment_key
            )
            
            if result:
                return dict(result)
            
            # Fallback: calcular en tiempo real si vista no existe
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT vss.variant_id) as variant_count,
                    SUM(vss.total_allocations) as total_visitors,
                    SUM(vss.total_conversions) as total_conversions,
                    AVG(vss.conversion_rate) as avg_conversion_rate
                FROM variant_segment_state vss
                WHERE vss.experiment_id = $1 AND vss.segment_key = $2
                """,
                UUID(experiment_id),
                segment_key
            )
            
            return dict(stats) if stats else {}
    
    async def get_all_segments(
        self,
        experiment_id: str,
        min_sample_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los segmentos del experimento con sus métricas
        
        Args:
            min_sample_size: Filtrar segmentos con menos de X visitors
        """
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    segment_key,
                    variant_count,
                    total_visitors,
                    total_conversions,
                    avg_conversion_rate,
                    best_variant_name,
                    data_quality
                FROM segment_performance_summary
                WHERE experiment_id = $1
                  AND total_visitors >= $2
                ORDER BY total_visitors DESC
                """,
                UUID(experiment_id),
                min_sample_size
            )
        
        return [dict(row) for row in rows]
    
    async def compare_segments(
        self,
        experiment_id: str,
        variant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Compara performance de una variante en diferentes segmentos
        
        Útil para detectar:
        - Segmentos donde la variante funciona mejor
        - Heterogeneidad de efectos
        - Posible Simpson's Paradox
        """
        
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    vss.segment_key,
                    vss.total_allocations,
                    vss.total_conversions,
                    vss.conversion_rate,
                    vss.alpha,
                    vss.beta,
                    
                    -- Estimated CVR (media de Beta)
                    vss.alpha / (vss.alpha + vss.beta) as estimated_cvr,
                    
                    -- Confidence (más samples = más confianza)
                    CASE 
                        WHEN vss.total_allocations >= 1000 THEN 'high'
                        WHEN vss.total_allocations >= 100 THEN 'medium'
                        ELSE 'low'
                    END as confidence_level
                    
                FROM variant_segment_state vss
                WHERE vss.experiment_id = $1
                  AND vss.variant_id = $2
                ORDER BY vss.total_allocations DESC
                """,
                UUID(experiment_id),
                UUID(variant_id)
            )
        
        return [dict(row) for row in rows]
    
    # ========================================================================
    # STATISTICAL UTILITIES
    # ========================================================================
    
    async def calculate_credible_intervals(
        self,
        variant_id: str,
        segment_key: str,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """
        Calcula intervalos de credibilidad Bayesianos
        
        Usa distribución Beta para calcular credible intervals.
        Esto es mejor que confidence intervals frecuentistas porque:
        - Incorpora prior information
        - Más intuitivo: "95% de probabilidad que el verdadero CVR está en [a, b]"
        """
        
        from scipy import stats
        
        async with self.db.acquire() as conn:
            state = await conn.fetchrow(
                """
                SELECT alpha, beta, conversion_rate
                FROM variant_segment_state
                WHERE variant_id = $1 AND segment_key = $2
                """,
                UUID(variant_id),
                segment_key
            )
        
        if not state:
            return {
                'lower': 0.0,
                'upper': 0.0,
                'point_estimate': 0.0
            }
        
        alpha = float(state['alpha'])
        beta = float(state['beta'])
        
        # Credible interval
        lower_percentile = (1 - confidence) / 2
        upper_percentile = 1 - lower_percentile
        
        lower = stats.beta.ppf(lower_percentile, alpha, beta)
        upper = stats.beta.ppf(upper_percentile, alpha, beta)
        
        # Point estimate (media de Beta)
        point = alpha / (alpha + beta)
        
        # Actualizar en BD
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE variant_segment_state
                SET 
                    confidence_lower = $3,
                    confidence_upper = $4
                WHERE variant_id = $1 AND segment_key = $2
                """,
                UUID(variant_id),
                segment_key,
                lower,
                upper
            )
        
        return {
            'lower': float(lower),
            'upper': float(upper),
            'point_estimate': float(point),
            'confidence_level': confidence
        }
    
    async def detect_heterogeneity(
        self,
        experiment_id: str,
        variant_id: str,
        significance_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detecta si hay heterogeneidad significativa entre segmentos
        
        Usa test estadístico para determinar si la diferencia
        en conversion rates entre segmentos es significativa.
        
        Returns:
            {
                'is_heterogeneous': bool,
                'chi_square_statistic': float,
                'p_value': float,
                'segments_compared': int
            }
        """
        
        # TODO: Implementar test chi-cuadrado o Bayesian hierarchical model
        # Por ahora, una heurística simple
        
        segments_data = await self.compare_segments(experiment_id, variant_id)
        
        if len(segments_data) < 2:
            return {
                'is_heterogeneous': False,
                'reason': 'Insufficient segments for comparison'
            }
        
        cvrs = [s['conversion_rate'] for s in segments_data if s['total_allocations'] >= 100]
        
        if len(cvrs) < 2:
            return {
                'is_heterogeneous': False,
                'reason': 'Insufficient data in segments'
            }
        
        # Coefficient of variation
        import statistics
        mean_cvr = statistics.mean(cvrs)
        std_cvr = statistics.stdev(cvrs)
        
        cv = std_cvr / mean_cvr if mean_cvr > 0 else 0
        
        # Si CV > 0.3, hay alta heterogeneidad
        is_heterogeneous = cv > 0.3
        
        return {
            'is_heterogeneous': is_heterogeneous,
            'coefficient_of_variation': float(cv),
            'mean_cvr': float(mean_cvr),
            'std_cvr': float(std_cvr),
            'segments_analyzed': len(cvrs),
            'recommendation': (
                'Segmentation is valuable - performance varies significantly across segments'
                if is_heterogeneous
                else 'Segments behave similarly - might not need segmentation'
            )
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def migrate_old_data_to_new_architecture(db_pool):
    """
    Migra datos de arquitectura vieja a nueva
    
    Solo necesario si tienes datos existentes en element_variants
    con segment_key embebido.
    """
    
    logger.info("Starting data migration to new segmentation architecture...")
    
    async with db_pool.acquire() as conn:
        # Check si ya se ejecutó la migración
        migrated = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM variant_segment_state LIMIT 1
            )
            """
        )
        
        if migrated:
            logger.info("Data already migrated")
            return
        
        # Ejecutar migración SQL
        await conn.execute(open('migration_segmentation_v2.sql').read())
        
        logger.info("✅ Migration completed successfully")


async def refresh_materialized_views(db_pool):
    """
    Refresca vistas materializadas para analytics
    
    Ejecutar esto periódicamente (cada 5-15 minutos) con un cron job
    """
    
    async with db_pool.acquire() as conn:
        await conn.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY segment_performance_summary"
        )
        
        logger.info("✅ Refreshed segment_performance_summary")
