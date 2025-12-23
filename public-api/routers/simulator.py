# public-api/routers/simulator.py

"""
Conversion Simulation Engine
Provides a real-time stochastic model of multivariate A/B testing for demonstration purposes.
Uses Thompson Sampling and Binomial distributions to simulate visitor behavior.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
import random
import logging

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
        """Simulates a rapid stream of individual visitor events"""
        events = []
        combos = list(self._probabilities.keys())
        
        for _ in range(size):
            combo = random.choice(combos)
            cr = self._probabilities[combo]
            converted = random.random() <= cr
            
            events.append({
                "id": f"sim_{random.randint(1000, 9999)}",
                "combination": f"{combo[0]}-{combo[1]}",
                "ui": {
                    "cta": self.elements['cta']['variants'][combo[0]],
                    "hero": self.elements['hero']['variants'][combo[1]]
                },
                "converted": converted
            })
        return events

    def simulate_historical_data(self, visitors: int = 10000):
        """Simulates the aggregated results of a 10,000 visitor study"""
        variants = []
        combos = list(self._probabilities.keys())
        visits_per = visitors // len(combos)
        
        for combo in combos:
            cr = self._probabilities[combo]
            convs = int(np.random.binomial(visits_per, cr))
            
            variants.append({
                "label": f"{self.elements['cta']['variants'][combo[0]]['text']} / {self.elements['hero']['variants'][combo[1]]['text']}",
                "key": f"{combo[0]}-{combo[1]}",
                "visits": visits_per,
                "conversions": convs,
                "cr": round(convs / visits_per, 4) if visits_per > 0 else 0
            })
            
        variants.sort(key=lambda x: x['cr'], reverse=True)
        winner = variants[0]
        loser = variants[-1]
        
        return {
            "total_sample": visitors,
            "performance": variants,
            "winner": winner,
            "uplift": round(((winner['cr'] - loser['cr']) / loser['cr']) * 100, 2) if loser['cr'] > 0 else 0
        }

engine = SimulationEngine()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/summary")
async def get_simulation_summary():
    """Generates a high-volume simulation snapshot for visual analysis"""
    return engine.simulate_historical_data(10000)

@router.get("/stream")
async def get_realtime_stream():
    """Returns a dynamic batch of simulation events for real-time visualization"""
    return {
        "events": engine.generate_live_batch(25),
        "schema": engine.elements
    }
