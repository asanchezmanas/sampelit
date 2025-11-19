# public-api/routers/analytics.py

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from data_access.database import get_database, DatabaseManager
from public_api.routers.auth import get_current_user

router = APIRouter()

# ============================================
# RESPONSE MODELS
# ============================================

class VariantAnalytics(BaseModel):
    """Analytics for a single variant"""
    variant_id: str
    variant_name: str
    allocations: int
    conversions: int
    conversion_rate: float
    confidence_score: float
    probability_best: Optional[float] = None
    credible_interval_lower: Optional[float] = None
    credible_interval_upper: Optional[float] = None

class ExperimentAnalytics(BaseModel):
    """Comprehensive experiment analytics"""
    experiment_id: str
    experiment_name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    
    # Summary
    total_users: int
    total_conversions: int
    overall_conversion_rate: float
    
    # Variant analytics
    variants: List[VariantAnalytics]
    
    # Bayesian analysis
    recommended_winner: Optional[str] = None
    winner_confidence: Optional[float] = None
    confidence_threshold_met: bool = False
    continue_testing: bool = True
    
    # Recommendations
    recommendations: List[str] = []

class TimeseriesDataPoint(BaseModel):
    """Single data point in timeseries"""
    timestamp: datetime
    allocations: int
    conversions: int
    conversion_rate: float

class TimeseriesResponse(BaseModel):
    """Timeseries analytics response"""
    experiment_id: str
    variant_id: Optional[str]
    data_points: List[TimeseriesDataPoint]

# ============================================
# ENDPOINTS
# ============================================

@router.get("/{experiment_id}", response_model=ExperimentAnalytics)
async def get_experiment_analytics(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get comprehensive analytics for experiment
    
    Includes:
    - Variant performance metrics
    - Bayesian statistical analysis
    - Recommendations
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp_row = await conn.fetchrow(
                """
                SELECT id, name, status, created_at, started_at, user_id
                FROM experiments
                WHERE id = $1
                """,
                experiment_id
            )
        
        if not exp_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        if str(exp_row['user_id']) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get variant analytics
        async with db.pool.acquire() as conn:
            variant_rows = await conn.fetch(
                """
                SELECT 
                    v.id,
                    v.name,
                    v.total_allocations,
                    v.total_conversions,
                    v.observed_conversion_rate,
                    CASE 
                        WHEN v.total_allocations >= 30 THEN 0.8
                        WHEN v.total_allocations >= 10 THEN 0.5
                        ELSE 0.2
                    END as confidence_score
                FROM variants v
                WHERE v.experiment_id = $1 AND v.is_active = true
                ORDER BY v.created_at
                """,
                experiment_id
            )
        
        variants = [dict(row) for row in variant_rows]
        
        # Calculate totals
        total_users = sum(v['total_allocations'] for v in variants)
        total_conversions = sum(v['total_conversions'] for v in variants)
        overall_cr = total_conversions / total_users if total_users > 0 else 0
        
        # Bayesian analysis
        bayesian_analysis = await _perform_bayesian_analysis(variants)
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            variants,
            bayesian_analysis,
            total_users
        )
        
        # Build response
        variant_analytics = [
            VariantAnalytics(
                variant_id=str(v['id']),
                variant_name=v['name'],
                allocations=v['total_allocations'],
                conversions=v['total_conversions'],
                conversion_rate=float(v['observed_conversion_rate']),
                confidence_score=float(v['confidence_score']),
                probability_best=bayesian_analysis['prob_best'].get(str(v['id'])),
                credible_interval_lower=bayesian_analysis['credible_intervals'].get(
                    str(v['id']), {}
                ).get('lower'),
                credible_interval_upper=bayesian_analysis['credible_intervals'].get(
                    str(v['id']), {}
                ).get('upper')
            )
            for v in variants
        ]
        
        return ExperimentAnalytics(
            experiment_id=str(exp_row['id']),
            experiment_name=exp_row['name'],
            status=exp_row['status'],
            created_at=exp_row['created_at'],
            started_at=exp_row['started_at'],
            total_users=total_users,
            total_conversions=total_conversions,
            overall_conversion_rate=overall_cr,
            variants=variant_analytics,
            recommended_winner=bayesian_analysis.get('best_variant'),
            winner_confidence=bayesian_analysis.get('best_confidence'),
            confidence_threshold_met=bayesian_analysis.get('threshold_met', False),
            continue_testing=not bayesian_analysis.get('threshold_met', False),
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics failed: {str(e)}"
        )

@router.get("/{experiment_id}/timeseries", response_model=TimeseriesResponse)
async def get_timeseries_analytics(
    experiment_id: str,
    variant_id: Optional[str] = Query(None, description="Filter by variant"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data"),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get timeseries analytics
    
    Returns hourly aggregated data for the last N hours.
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM experiments WHERE id = $1 AND user_id = $2)",
                experiment_id, user_id
            )
        
        if not exp_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or access denied"
            )
        
        # Get timeseries data
        async with db.pool.acquire() as conn:
            if variant_id:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE_TRUNC('hour', allocated_at) as hour,
                        COUNT(*) as allocations,
                        COUNT(converted_at) as conversions,
                        CASE 
                            WHEN COUNT(*) > 0 
                            THEN COUNT(converted_at)::FLOAT / COUNT(*)::FLOAT
                            ELSE 0
                        END as conversion_rate
                    FROM allocations
                    WHERE 
                        experiment_id = $1 
                        AND variant_id = $2
                        AND allocated_at >= NOW() - INTERVAL '1 hour' * $3
                    GROUP BY DATE_TRUNC('hour', allocated_at)
                    ORDER BY hour ASC
                    """,
                    experiment_id, variant_id, hours
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE_TRUNC('hour', allocated_at) as hour,
                        COUNT(*) as allocations,
                        COUNT(converted_at) as conversions,
                        CASE 
                            WHEN COUNT(*) > 0 
                            THEN COUNT(converted_at)::FLOAT / COUNT(*)::FLOAT
                            ELSE 0
                        END as conversion_rate
                    FROM allocations
                    WHERE 
                        experiment_id = $1
                        AND allocated_at >= NOW() - INTERVAL '1 hour' * $2
                    GROUP BY DATE_TRUNC('hour', allocated_at)
                    ORDER BY hour ASC
                    """,
                    experiment_id, hours
                )
        
        data_points = [
            TimeseriesDataPoint(
                timestamp=row['hour'],
                allocations=row['allocations'],
                conversions=row['conversions'],
                conversion_rate=float(row['conversion_rate'])
            )
            for row in rows
        ]
        
        return TimeseriesResponse(
            experiment_id=experiment_id,
            variant_id=variant_id,
            data_points=data_points
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeseries analytics failed: {str(e)}"
        )

@router.get("/{experiment_id}/variants/{variant_id}/details")
async def get_variant_details(
    experiment_id: str,
    variant_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get detailed analytics for specific variant
    
    Includes recent allocations and conversion patterns.
    """
    
    try:
        # Verify ownership
        async with db.pool.acquire() as conn:
            exp_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM experiments WHERE id = $1 AND user_id = $2)",
                experiment_id, user_id
            )
        
        if not exp_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or access denied"
            )
        
        # Get variant data
        async with db.pool.acquire() as conn:
            variant = await conn.fetchrow(
                """
                SELECT 
                    id, name, description, content,
                    total_allocations, total_conversions,
                    observed_conversion_rate, created_at
                FROM variants
                WHERE id = $1 AND experiment_id = $2
                """,
                variant_id, experiment_id
            )
        
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found"
            )
        
        # Get recent allocations
        async with db.pool.acquire() as conn:
            recent_allocations = await conn.fetch(
                """
                SELECT 
                    allocated_at, converted_at, conversion_value
                FROM allocations
                WHERE variant_id = $1
                ORDER BY allocated_at DESC
                LIMIT 50
                """,
                variant_id
            )
        
        return {
            "variant": dict(variant),
            "recent_activity": [dict(row) for row in recent_allocations]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Variant details failed: {str(e)}"
        )

# ============================================
# HELPER FUNCTIONS
# ============================================

async def _perform_bayesian_analysis(variants: List[Dict]) -> Dict[str, Any]:
    """
    Perform Bayesian analysis on variants
    
    Uses Thompson Sampling statistics to calculate:
    - Probability each variant is best
    - Credible intervals
    - Statistical significance
    """
    
    import numpy as np
    from scipy import stats
    
    if len(variants) < 2:
        return {
            'prob_best': {},
            'credible_intervals': {},
            'best_variant': None,
            'best_confidence': 0,
            'threshold_met': False
        }
    
    # Calculate probability each is best (Monte Carlo)
    samples = 10000
    variant_samples = {}
    
    for variant in variants:
        # Beta distribution parameters
        alpha = variant['total_conversions'] + 1
        beta = variant['total_allocations'] - variant['total_conversions'] + 1
        
        variant_samples[str(variant['id'])] = np.random.beta(alpha, beta, samples)
    
    # Count how often each is best
    prob_best = {}
    for var_id in variant_samples:
        is_best_count = sum(
            variant_samples[var_id][i] == max(
                variant_samples[vid][i] for vid in variant_samples
            )
            for i in range(samples)
        )
        prob_best[var_id] = is_best_count / samples
    
    # Calculate credible intervals
    credible_intervals = {}
    for variant in variants:
        alpha = variant['total_conversions'] + 1
        beta = variant['total_allocations'] - variant['total_conversions'] + 1
        
        credible_intervals[str(variant['id'])] = {
            'lower': float(stats.beta.ppf(0.025, alpha, beta)),
            'upper': float(stats.beta.ppf(0.975, alpha, beta)),
            'expected': float(alpha / (alpha + beta))
        }
    
    # Determine winner
    best_variant_id = max(prob_best, key=prob_best.get)
    best_confidence = prob_best[best_variant_id]
    threshold_met = best_confidence >= 0.95
    
    return {
        'prob_best': prob_best,
        'credible_intervals': credible_intervals,
        'best_variant': best_variant_id if threshold_met else None,
        'best_confidence': best_confidence,
        'threshold_met': threshold_met
    }

def _generate_recommendations(
    variants: List[Dict],
    bayesian: Dict[str, Any],
    total_users: int
) -> List[str]:
    """Generate actionable recommendations"""
    
    recommendations = []
    
    # Check sample size
    if total_users < 100:
        recommendations.append(
            f"⏳ Need more data: {total_users}/100 users minimum for reliable results"
        )
    
    # Check for winner
    if bayesian.get('threshold_met'):
        best_name = next(
            v['name'] for v in variants 
            if str(v['id']) == bayesian['best_variant']
        )
        recommendations.append(
            f"🏆 Clear winner: {best_name} ({bayesian['best_confidence']:.1%} confidence)"
        )
        recommendations.append("Consider stopping the test and implementing the winner")
    else:
        recommendations.append(
            "📊 Continue testing - no clear winner yet"
        )
    
    # Check for underperformers
    if bayesian.get('prob_best'):
        poor_performers = [
            v for v in variants 
            if bayesian['prob_best'].get(str(v['id']), 0) < 0.05
        ]
        if poor_performers and total_users > 100:
            recommendations.append(
                f"💡 Consider pausing {len(poor_performers)} clearly underperforming variant(s)"
            )
    
    return recommendations
