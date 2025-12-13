# scripts/run_demo_single_element.py

import asyncio
import pandas as pd
import json
import numpy as np

async def run_single_element_demo():
    """
    Demo single-element CON comparación
    """
    
    print("📂 Loading single-element matrix...")
    
    df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
    matrix = df.values
    
    with open('demo_single_element_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Loaded: {matrix.shape[0]} visitors × {matrix.shape[1]} variants")
    
    # ══════════════════════════════════════
    # TRADICIONAL
    # ══════════════════════════════════════
    print("\n" + "="*80)
    print("📊 TRADITIONAL A/B TEST (20% traffic each)")
    print("="*80)
    
    n_visitors = matrix.shape[0]
    n_variants = matrix.shape[1]
    visitors_per_variant = n_visitors // n_variants
    
    trad_conversions = 0
    
    for var_idx in range(n_variants):
        start = var_idx * visitors_per_variant
        end = start + visitors_per_variant if var_idx < n_variants - 1 else n_visitors
        
        conversions = matrix[start:end, var_idx].sum()
        trad_conversions += conversions
        
        var_id = list(metadata['element']['variants'].keys())[var_idx]
        var_name = metadata['element']['variants'][var_id]['text']
        allocated = end - start
        cr = conversions / allocated
        
        print(f"   {var_name:<20} | {allocated:>5} visits | {conversions:>4} conv | {cr:.2%}")
    
    print(f"\n   Total: {trad_conversions} conversions")
    
    # ══════════════════════════════════════
    # SAMPLIT
    # ══════════════════════════════════════
    print("\n" + "="*80)
    print("🚀 SAMPLIT ADAPTIVE ALGORITHM")
    print("="*80)
    
    # [Mismo código que multi-element pero para 1 elemento]
    samplit_conversions = await simulate_single_element_samplit(matrix, metadata)
    
    # ══════════════════════════════════════
    # COMPARACIÓN
    # ══════════════════════════════════════
    print("\n" + "="*80)
    print("💰 RESULTS")
    print("="*80)
    
    additional = samplit_conversions - trad_conversions
    improvement = (additional / trad_conversions) * 100
    
    print(f"\n   Traditional A/B Test:  {trad_conversions} conversions")
    print(f"   Samplit Adaptive:      {samplit_conversions} conversions")
    print(f"   ")
    print(f"   Gain: +{additional} conversions ({improvement:+.1f}%)")


if __name__ == '__main__':
    asyncio.run(run_single_element_demo())
