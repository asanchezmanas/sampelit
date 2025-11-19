# public-api/routers/simulator.py

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from io import StringIO

router = APIRouter()

class SimulatorConfig(BaseModel):
    """Config del simulador"""
    total_visitors: int = Field(default=10000, ge=100, le=100000)
    variants: List[Dict[str, float]] = Field(
        ...,
        description="Lista de variantes con conversion_rate"
    )
    daily_visitors: int = Field(default=1000, ge=10, le=10000)
    confidence_threshold: float = Field(default=0.95, ge=0.80, le=0.99)

class SimulationResult(BaseModel):
    """Resultado de la simulación"""
    total_visitors: int
    days_run: int
    winner_detected_at_day: Optional[int]
    winner_variant: Optional[str]
    
    # Por variante
    variants_data: List[Dict]
    
    # Beneficio calculado
    benefit_analysis: Dict[str, float]
    
    # Timeline
    daily_stats: List[Dict]

@router.post("/simulate", response_model=SimulationResult)
async def run_simulation(config: SimulatorConfig):
    """
    Simular experimento con Thompson Sampling
    
    Endpoint PÚBLICO - no requiere auth
    """
    
    # Validar variantes
    if len(config.variants) < 2:
        raise HTTPException(400, "Necesitas al menos 2 variantes")
    
    if len(config.variants) > 10:
        raise HTTPException(400, "Máximo 10 variantes")
    
    # Validar conversion rates
    for v in config.variants:
        if not (0 <= v['conversion_rate'] <= 1):
            raise HTTPException(400, "Conversion rate debe estar entre 0 y 1")
    
    # Inicializar Thompson Sampling
    variants_state = {
        v['name']: {
            'successes': 1,  # Prior
            'failures': 1,
            'allocations': 0,
            'conversions': 0,
            'true_cr': v['conversion_rate']  # Para simular
        }
        for v in config.variants
    }
    
    # Simular día por día
    daily_stats = []
    winner_detected_at = None
    winner_variant = None
    
    days = config.total_visitors // config.daily_visitors
    
    for day in range(1, days + 1):
        # Stats del día
        day_allocations = {v: 0 for v in variants_state.keys()}
        day_conversions = {v: 0 for v in variants_state.keys()}
        
        # Procesar visitantes del día
        for _ in range(config.daily_visitors):
            # Thompson Sampling: sample from Beta
            samples = {
                name: np.random.beta(
                    state['successes'], 
                    state['failures']
                )
                for name, state in variants_state.items()
            }
            
            # Seleccionar mejor sample
            selected = max(samples, key=samples.get)
            
            # Simular conversión (basado en true_cr)
            converted = np.random.random() < variants_state[selected]['true_cr']
            
            # Update state
            variants_state[selected]['allocations'] += 1
            day_allocations[selected] += 1
            
            if converted:
                variants_state[selected]['conversions'] += 1
                variants_state[selected]['successes'] += 1
                day_conversions[selected] += 1
            else:
                variants_state[selected]['failures'] += 1
        
        # Calcular probabilidad de ser mejor (Monte Carlo)
        if day >= 3:  # Mínimo 3 días
            prob_best = calculate_probability_best(variants_state)
            best_variant = max(prob_best, key=prob_best.get)
            
            if prob_best[best_variant] >= config.confidence_threshold:
                if winner_detected_at is None:
                    winner_detected_at = day
                    winner_variant = best_variant
        
        # Guardar stats del día
        daily_stats.append({
            'day': day,
            'allocations': day_allocations.copy(),
            'conversions': day_conversions.copy(),
            'cumulative_allocations': {
                name: state['allocations'] 
                for name, state in variants_state.items()
            },
            'cumulative_conversions': {
                name: state['conversions'] 
                for name, state in variants_state.items()
            }
        })
    
    # Calcular beneficio
    # Asumiendo que sin optimización = split uniforme
    uniform_conversions = sum(
        (config.total_visitors / len(config.variants)) * v['conversion_rate']
        for v in config.variants
    )
    
    optimized_conversions = sum(
        state['conversions'] 
        for state in variants_state.values()
    )
    
    benefit = optimized_conversions - uniform_conversions
    
    # Formatear resultado
    return SimulationResult(
        total_visitors=config.total_visitors,
        days_run=days,
        winner_detected_at_day=winner_detected_at,
        winner_variant=winner_variant,
        variants_data=[
            {
                'name': name,
                'allocations': state['allocations'],
                'conversions': state['conversions'],
                'observed_cr': state['conversions'] / max(state['allocations'], 1),
                'true_cr': state['true_cr'],
                'final_probability': calculate_probability_best(variants_state)[name]
            }
            for name, state in variants_state.items()
        ],
        benefit_analysis={
            'uniform_split_conversions': round(uniform_conversions, 2),
            'optimized_conversions': optimized_conversions,
            'additional_conversions': round(benefit, 2),
            'improvement_percentage': round((benefit / uniform_conversions) * 100, 2) if uniform_conversions > 0 else 0
        },
        daily_stats=daily_stats
    )

def calculate_probability_best(variants_state: Dict, samples: int = 10000) -> Dict[str, float]:
    """Calcular probabilidad de ser mejor (Monte Carlo)"""
    
    # Sample from Beta distribution
    variant_samples = {
        name: np.random.beta(
            state['successes'], 
            state['failures'], 
            samples
        )
        for name, state in variants_state.items()
    }
    
    # Count how often each is best
    prob_best = {}
    for name in variants_state.keys():
        is_best_count = sum(
            variant_samples[name][i] == max(
                variant_samples[v][i] for v in variants_state.keys()
            )
            for i in range(samples)
        )
        prob_best[name] = is_best_count / samples
    
    return prob_best

@router.post("/simulate-csv")
async def simulate_from_csv(
    file: UploadFile = File(...),
    total_visitors: int = 10000,
    daily_visitors: int = 1000
):
    """
    Simular desde CSV
    
    CSV format:
    variant_name,conversion_rate
    Control,0.05
    Variant A,0.07
    Variant B,0.06
    """
    
    # Leer CSV
    contents = await file.read()
    df = pd.read_csv(StringIO(contents.decode('utf-8')))
    
    # Validar formato
    if 'variant_name' not in df.columns or 'conversion_rate' not in df.columns:
        raise HTTPException(
            400, 
            "CSV debe tener columnas: variant_name, conversion_rate"
        )
    
    # Convertir a formato de config
    variants = [
        {
            'name': row['variant_name'],
            'conversion_rate': float(row['conversion_rate'])
        }
        for _, row in df.iterrows()
    ]
    
    # Ejecutar simulación
    config = SimulatorConfig(
        total_visitors=total_visitors,
        variants=variants,
        daily_visitors=daily_visitors
    )
    
    return await run_simulation(config)
