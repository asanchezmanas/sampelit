# scripts/generate_demo_single_element.py

import numpy as np
import pandas as pd
import json
from datetime import datetime

class SingleElementDemoGenerator:
    """
    Demo de 1 ELEMENTO con 5 VARIANTES
    
    Ejemplo: Testing CTA button text
    """
    
    def __init__(self):
        self.n_visitors = 10000
        
        # 1 elemento, 5 variantes
        self.element = {
            'name': 'CTA Button',
            'variants': {
                'A': {'text': 'Sign Up Now', 'color': '#0066FF'},
                'B': {'text': 'Get Started Free', 'color': '#00C853'},
                'C': {'text': 'Try It Free', 'color': '#FF6B35'},
                'D': {'text': 'Start Your Trial', 'color': '#9C27B0'},
                'E': {'text': 'Join Today', 'color': '#FF5722'}
            }
        }
        
        # Conversion rates realistas
        self.conversion_rates = {
            'A': 0.028,  # 2.8%
            'B': 0.042,  # 4.2% ← WINNER
            'C': 0.035,  # 3.5%
            'D': 0.031,  # 3.1%
            'E': 0.024   # 2.4%
        }
    
    def generate_conversion_matrix(self):
        """
        Genera matriz (10000 × 5)
        """
        print("🎲 Generating SINGLE-ELEMENT conversion matrix...")
        print(f"   Element: {self.element['name']}")
        print(f"   Variants: {len(self.element['variants'])}")
        print(f"   Visitors: {self.n_visitors}")
        
        n_variants = len(self.element['variants'])
        matrix = np.zeros((self.n_visitors, n_variants), dtype=int)
        
        for col_idx, (var_id, var_data) in enumerate(self.element['variants'].items()):
            cr = self.conversion_rates[var_id]
            
            for row_idx in range(self.n_visitors):
                if np.random.rand() <= cr:
                    matrix[row_idx, col_idx] = 1
            
            conversions = matrix[:, col_idx].sum()
            actual_cr = conversions / self.n_visitors
            
            print(f"\n   Variant {var_id}: {var_data['text']}")
            print(f"      Target CR: {cr:.1%} | Actual: {actual_cr:.1%} | Conversions: {conversions}")
        
        return matrix
    
    def save_matrix(self, matrix):
        """Guardar CSV"""
        variant_names = list(self.element['variants'].keys())
        df = pd.DataFrame(matrix, columns=variant_names)
        df.index.name = 'visitor_id'
        df.to_csv('demo_single_element_matrix.csv')
        
        print(f"\n💾 Matrix saved: demo_single_element_matrix.csv")
        return 'demo_single_element_matrix.csv'
    
    def export_metadata(self, matrix):
        """Metadata"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'n_visitors': self.n_visitors,
            'element': self.element,
            'conversion_rates': self.conversion_rates,
            'actual_conversions': {
                var_id: int(matrix[:, idx].sum())
                for idx, var_id in enumerate(self.element['variants'].keys())
            },
            'winner': {
                'variant': 'B',
                'text': self.element['variants']['B']['text'],
                'cr': self.conversion_rates['B']
            }
        }
        
        with open('demo_single_element_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Metadata saved: demo_single_element_metadata.json")
        return metadata


def generate_single_element_dataset():
    """Generate dataset"""
    generator = SingleElementDemoGenerator()
    matrix = generator.generate_conversion_matrix()
    generator.save_matrix(matrix)
    metadata = generator.export_metadata(matrix)
    
    print("\n✅ Single-element dataset ready!")
    return matrix, metadata


if __name__ == '__main__':
    generate_single_element_dataset()
