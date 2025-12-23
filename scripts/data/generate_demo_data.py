# scripts/generate_demo_data.py

import numpy as np
import pandas as pd
import json
from datetime import datetime
from itertools import product

class MultiElementDemoGenerator:
    """
    Genera matriz de conversiones para experimento MULTI-ELEMENTO
    
    2 elementos × 3 variantes = 9 combinaciones
    Thompson Sampling aprende la MEJOR combinación
    """
    
    def __init__(self):
        self.n_visitors = 10000
        
        # ══════════════════════════════════════
        # ELEMENTOS Y VARIANTES
        # ══════════════════════════════════════
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
        
        # ══════════════════════════════════════
        # CONVERSION RATES POR COMBINACIÓN
        # ══════════════════════════════════════
        # Algunas combinaciones funcionan mejor que otras
        # Puede haber efectos de interacción
        
        self.combination_conversion_rates = {
            ('A', 'X'): 0.025,  # Sign Up + Grow Business = 2.5%
            ('A', 'Y'): 0.032,  # Sign Up + 10x = 3.2%
            ('A', 'Z'): 0.028,  # Sign Up + Join = 2.8%
            
            ('B', 'X'): 0.038,  # Get Started + Grow = 3.8%
            ('B', 'Y'): 0.045,  # Get Started + 10x = 4.5% ← WINNER!
            ('B', 'Z'): 0.041,  # Get Started + Join = 4.1%
            
            ('C', 'X'): 0.021,  # Try Free + Grow = 2.1%
            ('C', 'Y'): 0.029,  # Try Free + 10x = 2.9%
            ('C', 'Z'): 0.036,  # Try Free + Join = 3.6%
        }
        
        # Lista ordenada de combinaciones
        self.combinations = sorted(self.combination_conversion_rates.keys())
    
    def generate_conversion_matrix(self):
        """
        Genera matriz de conversiones
        
        Returns:
            numpy array (10000 × 9) 
            Columnas = combinaciones [(A,X), (A,Y), ..., (C,Z)]
        """
        print("🎲 Generating MULTI-ELEMENT conversion matrix...")
        print(f"   Visitors: {self.n_visitors}")
        print(f"   Elements: {len(self.elements)}")
        print(f"   Combinations: {len(self.combinations)}")
        
        # Crear matriz vacía
        n_combinations = len(self.combinations)
        matrix = np.zeros((self.n_visitors, n_combinations), dtype=int)
        
        # Para cada combinación (columna)
        for col_idx, combination in enumerate(self.combinations):
            cr = self.combination_conversion_rates[combination]
            
            # Para cada visitante (fila)
            for row_idx in range(self.n_visitors):
                # ¿Convertiría con esta combinación?
                if np.random.rand() <= cr:
                    matrix[row_idx, col_idx] = 1
            
            conversions = matrix[:, col_idx].sum()
            actual_cr = conversions / self.n_visitors
            
            cta, copy = combination
            combo_name = f"CTA-{cta} + Copy-{copy}"
            print(f"   {combo_name:<25} | Target: {cr:.1%} | Actual: {actual_cr:.1%} | Total: {conversions}")
        
        return matrix
    
    def get_combination_name(self, combination):
        """Nombre legible de combinación"""
        cta_var, copy_var = combination
        cta_text = self.elements['cta_button']['variants'][cta_var]['text']
        copy_text = self.elements['hero_copy']['variants'][copy_var]['text']
        return f"{cta_text} + {copy_text}"
    
    def matrix_to_dataframe(self, matrix):
        """Convertir matriz a DataFrame"""
        # Nombres de columnas = combinaciones
        column_names = [
            f"CTA-{cta}_Copy-{copy}"
            for cta, copy in self.combinations
        ]
        
        df = pd.DataFrame(matrix, columns=column_names)
        df.index.name = 'visitor_id'
        return df
    
    def save_matrix(self, matrix, filename='demo_multielement_matrix.csv'):
        """Guardar matriz como CSV"""
        df = self.matrix_to_dataframe(matrix)
        df.to_csv(filename)
        print(f"\n💾 Conversion matrix saved: {filename}")
        print(f"   Size: {matrix.shape[0]} visitors × {matrix.shape[1]} combinations")
        return filename
    
    def export_metadata(self, matrix):
        """Exportar metadata"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'n_visitors': self.n_visitors,
            'n_elements': len(self.elements),
            'n_combinations': len(self.combinations),
            'elements': {
                elem_id: {
                    'name': elem_data['name'],
                    'variants': {
                        var_id: var_data
                        for var_id, var_data in elem_data['variants'].items()
                    }
                }
                for elem_id, elem_data in self.elements.items()
            },
            'combinations': [
                {
                    'cta': cta,
                    'copy': copy,
                    'name': self.get_combination_name((cta, copy)),
                    'true_cr': self.combination_conversion_rates[(cta, copy)],
                    'actual_conversions': int(matrix[:, idx].sum())
                }
                for idx, (cta, copy) in enumerate(self.combinations)
            ],
            'winner': {
                'combination': ('B', 'Y'),
                'name': self.get_combination_name(('B', 'Y')),
                'true_cr': self.combination_conversion_rates[('B', 'Y')]
            }
        }
        
        with open('demo_multielement_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Metadata saved: demo_multielement_metadata.json")
        return metadata
    
    def print_summary(self, matrix):
        """Imprimir resumen"""
        print("\n" + "="*80)
        print("📊 MULTI-ELEMENT EXPERIMENT SUMMARY")
        print("="*80)
        
        print("\n🎯 Elements:")
        for elem_id, elem_data in self.elements.items():
            print(f"\n   {elem_data['name']}:")
            for var_id, var_data in elem_data['variants'].items():
                print(f"      Variant {var_id}: {var_data}")
        
        print("\n🔀 Combinations (sorted by CR):")
        sorted_combos = sorted(
            self.combinations,
            key=lambda c: self.combination_conversion_rates[c],
            reverse=True
        )
        
        for rank, combo in enumerate(sorted_combos, 1):
            cr = self.combination_conversion_rates[combo]
            name = self.get_combination_name(combo)
            col_idx = self.combinations.index(combo)
            actual = matrix[:, col_idx].sum()
            
            marker = "🏆" if rank == 1 else "  "
            print(f"   {marker} #{rank}. {name:<40} | CR: {cr:.1%} | Would convert: {actual}")
        
        print("\n" + "="*80)


def generate_multielement_dataset():
    """Generar dataset multi-elemento"""
    generator = MultiElementDemoGenerator()
    
    # 1. Generar matriz
    matrix = generator.generate_conversion_matrix()
    
    # 2. Guardar CSV
    csv_file = generator.save_matrix(matrix)
    
    # 3. Guardar metadata
    metadata = generator.export_metadata(matrix)
    
    # 4. Imprimir resumen
    generator.print_summary(matrix)
    
    print("\n✅ Multi-element dataset generation complete!")
    print(f"\n📊 Files generated:")
    print(f"   - {csv_file}")
    print(f"   - demo_multielement_metadata.json")
    print(f"\n🔍 Thompson Sampling will learn the BEST COMBINATION")
    
    return matrix, metadata


if __name__ == '__main__':
    matrix, metadata = generate_multielement_dataset()
