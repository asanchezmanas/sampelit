# public-api/routers/simulator.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
import random
import asyncio

router = APIRouter()

# ══════════════════════════════════════
# SIMULATION LOGIC (Ported from scripts)
# ══════════════════════════════════════

class SimulationEngine:
    """
    Real-time version of MultiElementDemoGenerator
    """
    def __init__(self):
        self.elements = {
            'cta_button': {
                'name': 'CTA Button',
                'variants': {
                    'A': {'text': 'Sign Up', 'color': '#0066FF'},
                    'B': {'text': 'Get Started', 'color': '#00C853'},
                    'C': {'text': 'Try Free', 'color': '#FF6B35'}
                }
            },
            'hero_copy': {
                'name': 'Hero Copy',
                'variants': {
                    'X': {'text': 'Grow Your Business Fast'},
                    'Y': {'text': '10x Your Conversions Today'},
                    'Z': {'text': 'Join 10,000+ Companies'}
                }
            }
        }
        
        # True Conversion Rates (Hidden from user initially)
        self.probabilities = {
            ('A', 'X'): 0.025, ('A', 'Y'): 0.032, ('A', 'Z'): 0.028,
            ('B', 'X'): 0.038, ('B', 'Y'): 0.045, ('B', 'Z'): 0.041,
            ('C', 'X'): 0.021, ('C', 'Y'): 0.029, ('C', 'Z'): 0.036,
        }
        
    def generate_batch(self, batch_size=50):
        """Generate a batch of simulated traffic events"""
        events = []
        
        combinations = list(self.probabilities.keys())
        
        for _ in range(batch_size):
            # For the demo visualizer, we want to show distribution.
            combo = random.choice(combinations)
            cr = self.probabilities[combo]
            converted = random.random() <= cr
            
            events.append({
                "combination": f"{combo[0]}-{combo[1]}", # e.g. A-X
                "elements": {
                    "cta": self.elements['cta_button']['variants'][combo[0]],
                    "copy": self.elements['hero_copy']['variants'][combo[1]]
                },
                "converted": converted
            })
            
        return events

    def run_full_simulation(self, n_visitors=10000):
        """Run a full simulation of N visitors and return stats"""
        stats = {}
        combinations = list(self.probabilities.keys())
        
        total_conversions = 0
        
        for combo in combinations:
            stats[combo] = {"visits": 0, "conversions": 0}
            
        # Simulate N visitors
        # We assume uniform traffic distribution for the A/B test phase
        visits_per_variant = n_visitors // len(combinations)
        
        for combo in combinations:
            cr = self.probabilities[combo]
            # Binomial distribution for speed
            convs = np.random.binomial(visits_per_variant, cr)
            
            stats[combo]["visits"] = visits_per_variant
            stats[combo]["conversions"] = int(convs)
            total_conversions += int(convs)
            
        # Format for API
        results = []
        for combo, data in stats.items():
            results.append({
                "name": f"{self.elements['cta_button']['variants'][combo[0]]['text']} + {self.elements['hero_copy']['variants'][combo[1]]['text']}",
                "combination": f"{combo[0]}-{combo[1]}",
                "visits": data["visits"],
                "conversions": data["conversions"],
                "cr": data["conversions"] / data["visits"] if data["visits"] > 0 else 0
            })
            
        # Sort by CR desc
        results.sort(key=lambda x: x['cr'], reverse=True)
        
        winner = results[0]
        loser = results[-1]
        improvement = (winner['cr'] - loser['cr']) / loser['cr'] if loser['cr'] > 0 else 0
        
        return {
            "total_visitors": n_visitors,
            "total_conversions": total_conversions,
            "variants": results,
            "winner": winner,
            "improvement": improvement
        }

engine = SimulationEngine()

@router.get("/summary")
async def simulate_summary():
    """Returns the result of a 10,000 visitor simulation"""
    return engine.run_full_simulation(10000)

@router.get("/stream")
async def simulate_stream():
    """
    Returns a batch of simulated events.
    Frontend calls this repeatedly to 'animate' the chart.
    """
    return {
        "batch": engine.generate_batch(batch_size=20),
        "metadata": {
            "elements": engine.elements
        }
    }
