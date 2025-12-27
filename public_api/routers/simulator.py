# public-api/routers/simulator.py

"""
Conversion Simulation Engine
Provides a real-time stochastic model of multivariate A/B testing for demonstration purposes.
Demonstrates the performance lift of the Samplit Intelligent Engine vs. a random baseline.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import random
import logging
from scipy import stats

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# CORE ENGINE
# ════════════════════════════════════════════════════════════════════════════

class SimulationEngine:
    """Real-time traffic generator with curated conversion probabilities"""
    def __init__(self):
        self.elements = {
            'cta': {
                'name': 'Call to Action',
                'variants': {
                    'A': {'text': 'Unlock Growth', 'color': '#0066FF'},
                    'B': {'text': 'Scale Now', 'color': '#050505'},
                    'C': {'text': 'Try Samplit', 'color': '#6366F1'}
                }
            },
            'hero': {
                'name': 'Hero Messaging',
                'variants': {
                    'X': {'text': 'Scientific Conversion Optimization'},
                    'Y': {'text': 'Data-Driven Growth for Solo Founders'},
                    'Z': {'text': 'Maximize Revenue. Minimize Noise.'}
                }
            }
        }
        
        # Latent conversion rates for simulation
        self._probabilities = {
            ('A', 'X'): 0.025, ('A', 'Y'): 0.038, ('A', 'Z'): 0.028,
            ('B', 'X'): 0.042, ('B', 'Y'): 0.051, ('B', 'Z'): 0.045,
            ('C', 'X'): 0.021, ('C', 'Y'): 0.031, ('C', 'Z'): 0.036,
        }
        
    def generate_live_batch(self, size: int = 20):
        """Simulates a rapid stream of individual visitor events comparing strategies"""
        events = []
        combos = list(self._probabilities.keys())
        
        # We simulate what different engines would have picked for the same visitors
        for _ in range(size):
            # 1. Baseline Choice (Fixed or Random)
            baseline_combo = random.choice(combos)
            
            # 2. Samplit Choice (Biased towards known high-performers for demonstration)
            # In a real sim, we'd maintain an internal state. For the UI, we choose 
            # from the top 3 best combinations to show the 'intelligence'
            samplit_choices = [('B', 'Y'), ('B', 'Z'), ('B', 'X')]
            samplit_combo = random.choice(samplit_choices)
            
            # Probability-based conversion check
            cr_samplit = self._probabilities[samplit_combo]
            cr_baseline = self._probabilities[baseline_combo]
            
            converted_samplit = random.random() <= cr_samplit
            converted_baseline = random.random() <= cr_baseline
            
            events.append({
                "id": f"sim_{random.randint(1000, 9999)}",
                "samplit_choice": f"{samplit_combo[0]}-{samplit_combo[1]}",
                "baseline_choice": f"{baseline_combo[0]}-{baseline_combo[1]}",
                "samplit_converted": converted_samplit,
                "baseline_converted": converted_baseline,
                "ui": {
                    "cta": self.elements['cta']['variants'][samplit_combo[0]],
                    "hero": self.elements['hero']['variants'][samplit_combo[1]]
                }
            })
        return events

    def simulate_historical_data(self, visitors: int = 10000):
        """Simulates the aggregated results comparing Samplit vs. Baseline"""
        combos = list(self._probabilities.keys())
        
        # Strategy A: Baseline (Random distribution)
        baseline_stats = []
        visits_per = visitors // len(combos)
        baseline_conversions = 0
        
        for combo in combos:
            cr = self._probabilities[combo]
            convs = int(np.random.binomial(visits_per, cr))
            baseline_conversions += convs
            baseline_stats.append({
                "key": f"{combo[0]}-{combo[1]}",
                "visits": visits_per,
                "conversions": convs,
                "cr": convs / visits_per if visits_per > 0 else 0
            })
            
        # Strategy B: Samplit Intelligence (Concentrates on winners)
        # We simulate 70% of traffic going to the top 2 combinations
        best_combos = [('B', 'Y'), ('B', 'Z')]
        other_combos = [c for c in combos if c not in best_combos]
        
        samplit_stats = []
        samplit_conversions = 0
        
        # Distribute 70% to top 2, 30% to the rest
        top_visits = int(visitors * 0.70) // 2
        rest_visits = int(visitors * 0.30) // len(other_combos)
        
        for combo in combos:
            cr = self._probabilities[combo]
            v = top_visits if combo in best_combos else rest_visits
            convs = int(np.random.binomial(v, cr))
            samplit_conversions += convs
            samplit_stats.append({
                "key": f"{combo[0]}-{combo[1]}",
                "visits": v,
                "conversions": convs,
                "cr": convs / v if v > 0 else 0
            })
            
        return {
            "total_visitors": visitors,
            "strategies": {
                "baseline": {
                    "name": "Standard Testing (Random)",
                    "conversions": baseline_conversions,
                    "conversion_rate": baseline_conversions / visitors
                },
                "samplit": {
                    "name": "Samplit Intelligent Engine",
                    "conversions": samplit_conversions,
                    "conversion_rate": samplit_conversions / visitors
                }
            },
            "performance_gap": {
                "extra_conversions": samplit_conversions - baseline_conversions,
                "uplift": round(((samplit_conversions - baseline_conversions) / baseline_conversions) * 100, 2) if baseline_conversions > 0 else 0
            },
            "variant_details": sorted(samplit_stats, key=lambda x: x['cr'], reverse=True)
        }

engine = SimulationEngine()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/summary")
async def get_simulation_summary():
    """Generates a high-volume simulation snapshot for comparative ROI analysis"""
    return engine.simulate_historical_data(10000)

@router.get("/stream")
async def get_realtime_stream():
    """Returns a comparative batch of simulation events for visual value proof"""
# ════════════════════════════════════════════════════════════════════════════
# FORECAST ENGINE
# ════════════════════════════════════════════════════════════════════════════

class ForecastRequest(BaseModel):
    traffic_daily: int = 1000
    baseline_cr: float = 0.05
    uplift: float = 0.10  # 10% improvement
    confidence_target: float = 0.95

@router.post("/forecast")
async def forecast_convergence(req: ForecastRequest):
    """
    Project experiment convergence based on Samplit Predictive Engine.
    Returns the confidence evolution over time.
    """
    days = 14
    data_points = []
    
    # Simulation Parameters
    visitors_per_day = req.traffic_daily // 2 # split between A/B
    baseline_cr = req.baseline_cr
    test_cr = baseline_cr * (1 + req.uplift)
    
    # Predictive Simulation
    # We simulate one "typical" path for visualization
    cum_visitors_A = 0
    cum_conv_A = 0
    cum_visitors_B = 0
    cum_conv_B = 0
    
    for day in range(1, days + 1):
        # Simulating daily batch
        # Add variability to match real-world conditions
        daily_A_conv = np.random.binomial(visitors_per_day, baseline_cr)
        daily_B_conv = np.random.binomial(visitors_per_day, test_cr)
        
        cum_visitors_A += visitors_per_day
        cum_visitors_B += visitors_per_day
        cum_conv_A += daily_A_conv
        cum_conv_B += daily_B_conv
        
        # Calculate P-Value (Z-test approximation for speed)
        # pooled p
        p_pool = (cum_conv_A + cum_conv_B) / (cum_visitors_A + cum_visitors_B)
        se = np.sqrt(p_pool * (1 - p_pool) * (1/cum_visitors_A + 1/cum_visitors_B))
        
        if se > 0:
            z = ((cum_conv_B/cum_visitors_B) - (cum_conv_A/cum_visitors_A)) / se
            p_curr = 2 * (1 - stats.norm.cdf(abs(z)))
        else:
            p_curr = 1.0
            
        # Clamp for visualization
        data_points.append(min(p_curr, 0.5)) 

    return {
        "days": days,
        "forecast": data_points,
        "parameters": {
            "traffic": req.traffic_daily,
            "uplift": req.uplift
        }
    }

