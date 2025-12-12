# scripts/generate_demo_single_element.py

import numpy as np
import pandas as pd
import json
from datetime import datetime

class SingleElementDemoGenerator:
    """
    Genera matriz de conversiones para UN ELEMENTO con múltiples variantes
    
    Caso más común: testear diferentes versiones del CTA
    Por ejemplo: 5 variantes de botón
    """
    
    def __init__(self):
        self.n_visitors = 10000
        
        # ══════════════════════════════════════
        # UN ELEMENTO: CTA Button
        # ══════════════════════════════════════
        self.element = {
            'id': 'cta_button',
            'name': 'Main CTA Button',
            'selector': '#hero-cta',
            'type': 'button'
        }
        
        # ══════════════════════════════════════
        # MÚLTIPLES VARIANTES
        # ══════════════════════════════════════
        self.variants = {
            'A': {
                'name': 'Sign Up Free',
                'text': 'Sign Up Free',
                'color': '#0066FF',
                'size': 'large'
            },
            'B': {
                'name': 'Get Started',
                'text': 'Get Started',
                'color': '#00C853',
                'size': 'large'
            },
            'C': {
                'name': 'Try It Now',
                'text': 'Try It Now',
                'color': '#FF6B35',
                'size': 'large'
            },
            'D': {
                'name': 'Start Free Trial',
                'text': 'Start Free Trial',
                'color': '#9C27B0',
                'size': 'medium'
            },
            'E': {
                'name': 'Join Now',
                'text': 'Join Now',
                'color': '#FF5722',
                'size': 'large'
            }
        }
        
        # ══════════════════════════════════════
        # CONVERSION RATES POR VARIANTE
        # ══════════════════════════════════════
        # Realistas para SaaS landing page
        self.variant_conversion_rates = {
            'A': 0.028,  # 2.8% - Control (baseline típico)
            'B': 0.042,  # 4.2% - Get Started funciona bien
            'C': 0.035,  # 3.5% - Try It Now (urgencia moderada)
            'D': 0.048,  # 4.8% - Start Free Trial ← WINNER!
            'E': 0.031   # 3.1% - Join Now (ok)
        }
        
        self.variant_ids = sorted(self.variants.keys())
    
    def generate_conversion_matrix(self):
        """
        Genera matriz de conversiones
        
        Returns:
            numpy array (10000 × 5)
            Columnas = variantes [A, B, C, D, E]
        """
        print("🎲 Generating SINGLE-ELEMENT conversion matrix...")
        print(f"   Visitors: {self.n_visitors}")
        print(f"   Element: {self.element['name']}")
        print(f"   Variants: {len(self.variants)}")
        
        # Crear matriz vacía
        n_variants = len(self.variant_ids)
        matrix = np.zeros((self.n_visitors, n_variants), dtype=int)
        
        print(f"\n{'Variant':<25} | {'Target CR':<10} | {'Actual CR':<10} | {'Conversions'}")
        print("-" * 75)
        
        # Para cada variante (columna)
        for col_idx, variant_id in enumerate(self.variant_ids):
            variant = self.variants[variant_id]
            cr = self.variant_conversion_rates[variant_id]
            
            # Para cada visitante (fila)
            for row_idx in range(self.n_visitors):
                # ¿Convertiría con esta variante?
                if np.random.rand() <= cr:
                    matrix[row_idx, col_idx] = 1
            
            conversions = matrix[:, col_idx].sum()
            actual_cr = conversions / self.n_visitors
            
            print(f"{variant['name']:<25} | {cr:>9.1%} | {actual_cr:>9.1%} | {conversions:>11}")
        
        return matrix
    
    def matrix_to_dataframe(self, matrix):
        """Convertir matriz a DataFrame"""
        # Nombres de columnas = nombres de variantes
        column_names = [
            f"Variant_{variant_id}_{self.variants[variant_id]['name'].replace(' ', '_')}"
            for variant_id in self.variant_ids
        ]
        
        df = pd.DataFrame(matrix, columns=column_names)
        df.index.name = 'visitor_id'
        return df
    
    def save_matrix(self, matrix, filename='demo_single_element_matrix.csv'):
        """Guardar matriz como CSV"""
        df = self.matrix_to_dataframe(matrix)
        df.to_csv(filename)
        print(f"\n💾 Conversion matrix saved: {filename}")
        print(f"   Size: {matrix.shape[0]} visitors × {matrix.shape[1]} variants")
        return filename
    
    def export_metadata(self, matrix):
        """Exportar metadata"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'experiment_type': 'single_element',
            'n_visitors': self.n_visitors,
            'element': self.element,
            'variants': [
                {
                    'id': variant_id,
                    'name': variant_data['name'],
                    'content': variant_data,
                    'true_cr': self.variant_conversion_rates[variant_id],
                    'actual_conversions': int(matrix[:, idx].sum()),
                    'actual_cr': float(matrix[:, idx].sum() / self.n_visitors)
                }
                for idx, (variant_id, variant_data) in enumerate(
                    sorted(self.variants.items())
                )
            ],
            'winner': {
                'id': 'D',
                'name': self.variants['D']['name'],
                'true_cr': self.variant_conversion_rates['D']
            },
            'total_possible_conversions': int(matrix.sum())
        }
        
        with open('demo_single_element_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Metadata saved: demo_single_element_metadata.json")
        return metadata
    
    def print_summary(self, matrix):
        """Imprimir resumen"""
        print("\n" + "="*80)
        print("📊 SINGLE-ELEMENT EXPERIMENT SUMMARY")
        print("="*80)
        
        print(f"\n🎯 Element: {self.element['name']}")
        print(f"   Selector: {self.element['selector']}")
        print(f"   Type: {self.element['type']}")
        
        print("\n📋 Variants (sorted by CR):")
        sorted_variants = sorted(
            self.variant_ids,
            key=lambda v: self.variant_conversion_rates[v],
            reverse=True
        )
        
        for rank, variant_id in enumerate(sorted_variants, 1):
            variant = self.variants[variant_id]
            cr = self.variant_conversion_rates[variant_id]
            col_idx = self.variant_ids.index(variant_id)
            conversions = matrix[:, col_idx].sum()
            
            marker = "🏆" if rank == 1 else "  "
            print(f"   {marker} #{rank}. {variant['name']:<25} | "
                  f"CR: {cr:.1%} | Would convert: {conversions:>4}/{self.n_visitors}")
        
        # Calcular beneficio vs split uniforme
        uniform_per_variant = self.n_visitors / len(self.variants)
        uniform_conversions = sum(
            uniform_per_variant * self.variant_conversion_rates[v]
            for v in self.variant_ids
        )
        
        # Mejor caso: todo el tráfico al winner
        best_cr = max(self.variant_conversion_rates.values())
        best_case_conversions = self.n_visitors * best_cr
        
        print(f"\n💰 Potential Impact:")
        print(f"   Uniform split (A/B test): {uniform_conversions:.0f} conversions")
        print(f"   All to winner (optimal): {best_case_conversions:.0f} conversions")
        print(f"   Potential gain: +{best_case_conversions - uniform_conversions:.0f} conversions")
        print(f"   Thompson Sampling will approach optimal automatically!")
        
        print("\n" + "="*80)


def generate_single_element_dataset():
    """Generar dataset de un elemento"""
    generator = SingleElementDemoGenerator()
    
    # 1. Generar matriz
    matrix = generator.generate_conversion_matrix()
    
    # 2. Guardar CSV
    csv_file = generator.save_matrix(matrix)
    
    # 3. Guardar metadata
    metadata = generator.export_metadata(matrix)
    
    # 4. Imprimir resumen
    generator.print_summary(matrix)
    
    print("\n✅ Single-element dataset generation complete!")
    print(f"\n📊 Files generated:")
    print(f"   - {csv_file}")
    print(f"   - demo_single_element_metadata.json")
    print(f"\n🔍 Thompson Sampling will learn the BEST VARIANT")
    
    return matrix, metadata


if __name__ == '__main__':
    matrix, metadata = generate_single_element_dataset()
