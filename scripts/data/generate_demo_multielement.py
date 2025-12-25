# scripts/generate_demo_multielement.py

#!/usr/bin/env python3
"""
Script para generar datos de demo para experimentos multi-elemento FACTORIAL.

Este script crea una matriz de conversiones simulada para demostrar cómo funciona
el modo FACTORIAL de multi-elemento, donde cada COMBINACIÓN de elementos es tratada
como una variante separada.

MODO FACTORIAL:
- Cada combinación (CTA + Copy) es una "super-variante"
- Captura efectos de INTERACCIÓN entre elementos
- Ejemplo: "Get Started" + "10x" puede ser mejor que "Try Free" + "10x"

Output:
- demo_multielement_matrix.csv: Matriz de conversiones (10,000 visitors × 9 combinations)
- demo_multielement_metadata.json: Metadata con información del experimento
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path

class MultiElementDemoGenerator:
    """Generador de datos de demo para experimentos multi-elemento en modo FACTORIAL."""
    
    def __init__(self, n_visitors=10000, random_seed=42):
        """
        Inicializa el generador.
        
        Args:
            n_visitors: Número de visitantes a simular
            random_seed: Semilla para reproducibilidad
        """
        self.n_visitors = n_visitors
        self.random_seed = random_seed
        np.random.seed(random_seed)
        
        # Definir elementos y variantes
        # 2 elementos × 3 variantes cada uno = 9 combinaciones
        self.elements = {
            'cta_button': ['CTA-A', 'CTA-B', 'CTA-C'],  # "Get Started", "Try Free", "Sign Up"
            'hero_copy': ['Copy-X', 'Copy-Y', 'Copy-Z']  # "Transform", "10x Your", "Unlock"
        }
        
        # Definir conversion rates para cada COMBINACIÓN (modo FACTORIAL)
        # Esto simula INTERACCIONES entre elementos
        self.combination_conversion_rates = {
            ('CTA-A', 'Copy-X'): 0.025,  # Peor combinación
            ('CTA-A', 'Copy-Y'): 0.035,  # Mediocre
            ('CTA-A', 'Copy-Z'): 0.032,
            ('CTA-B', 'Copy-X'): 0.038,  # Buena
            ('CTA-B', 'Copy-Y'): 0.045,  # MEJOR COMBINACIÓN ⭐
            ('CTA-B', 'Copy-Z'): 0.041,  # Buena
            ('CTA-C', 'Copy-X'): 0.022,  # Muy mala
            ('CTA-C', 'Copy-Y'): 0.028,  # Mala
            ('CTA-C', 'Copy-Z'): 0.033,  # Mediocre
        }
        
        # Encontrar combinación ganadora
        self.winner = max(self.combination_conversion_rates.items(), 
                         key=lambda x: x[1])
        
        print(f"\n📊 Configuración del Demo:")
        print(f"  Visitantes: {n_visitors:,}")
        print(f"  Elementos: {len(self.elements)}")
        print(f"  Variantes por elemento: {[len(v) for v in self.elements.values()]}")
        print(f"  Total combinaciones: {len(self.combination_conversion_rates)}")
        print(f"\n🏆 Combinación ganadora (verdadera):")
        print(f"  {self.winner[0][0]} + {self.winner[0][1]} → {self.winner[1]:.1%} CR")
        print("\n⚠️  NOTA: Modo FACTORIAL captura estas interacciones.")
        print("   Modo INDEPENDENT no podría descubrir esto.\n")
    
    def generate_conversion_matrix(self):
        """
        Genera matriz de conversiones simulada.
        
        Returns:
            numpy.ndarray: Matriz de shape (n_visitors, n_combinations)
                          Valores binarios: 1 = conversión, 0 = no conversión
        """
        print("🔄 Generando matriz de conversiones...")
        
        n_combinations = len(self.combination_conversion_rates)
        matrix = np.zeros((self.n_visitors, n_combinations), dtype=int)
        
        # Para cada combinación, generar conversiones según su CR real
        for idx, ((cta, copy), conversion_rate) in enumerate(
            sorted(self.combination_conversion_rates.items())
        ):
            # Generar conversiones binarias con probabilidad = conversion_rate
            conversions = np.random.binomial(1, conversion_rate, self.n_visitors)
            matrix[:, idx] = conversions
            
            total_conversions = conversions.sum()
            actual_cr = total_conversions / self.n_visitors
            
            print(f"  {cta} + {copy}: {total_conversions:,} conversiones "
                  f"({actual_cr:.1%} vs {conversion_rate:.1%} esperado)")
        
        print(f"\n✅ Matriz generada: {matrix.shape[0]:,} × {matrix.shape[1]}")
        return matrix
    
    def export_to_csv(self, matrix, filename='demo_multielement_matrix.csv'):
        """
        Exporta matriz a CSV.
        
        Args:
            matrix: Matriz de conversiones
            filename: Nombre del archivo
        """
        # Crear nombres de columnas
        columns = [
            f"combo_{idx}_{cta}_{copy}"
            for idx, (cta, copy) in enumerate(
                sorted(self.combination_conversion_rates.keys())
            )
        ]
        
        df = pd.DataFrame(matrix, columns=columns)
        df.to_csv(filename, index=False)
        
        print(f"💾 CSV exportado: {filename}")
        print(f"   Shape: {df.shape}")
        print(f"   Size: {Path(filename).stat().st_size / 1024:.1f} KB")
        
        return filename
    
    def export_metadata(self, filename='demo_multielement_metadata.json'):
        """
        Exporta metadata del experimento.
        
        Args:
            filename: Nombre del archivo JSON
        """
        # Crear lista de combinaciones con sus IDs
        combinations = []
        for idx, (cta, copy) in enumerate(
            sorted(self.combination_conversion_rates.keys())
        ):
            combinations.append({
                'combination_id': idx,
                'element_values': {
                    'cta_button': cta,
                    'hero_copy': copy
                },
                'expected_conversion_rate': self.combination_conversion_rates[(cta, copy)],
                'is_winner': (cta, copy) == self.winner[0]
            })
        
        metadata = {
            'experiment_name': 'Demo Multi-Element Factorial',
            'experiment_type': 'multi_element_factorial',
            'combination_mode': 'factorial',
            'n_visitors': self.n_visitors,
            'random_seed': self.random_seed,
            'elements': {
                name: {
                    'variants': variants,
                    'n_variants': len(variants)
                }
                for name, variants in self.elements.items()
            },
            'total_combinations': len(self.combination_conversion_rates),
            'combinations': combinations,
            'winner': {
                'combination_id': next(
                    c['combination_id'] for c in combinations 
                    if c['is_winner']
                ),
                'element_values': {
                    'cta_button': self.winner[0][0],
                    'hero_copy': self.winner[0][1]
                },
                'expected_conversion_rate': self.winner[1]
            },
            'notes': [
                'This is a FACTORIAL experiment',
                'Each combination is treated as a separate variant',
                'Adaptive Optimization learns the best COMBINATION',
                'Captures interaction effects between elements',
                'Example: CTA-B + Copy-Y (4.5%) > CTA-C + Copy-Y (2.8%)'
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n📄 Metadata exportada: {filename}")
        print(f"   Total combinaciones: {metadata['total_combinations']}")
        print(f"   Combinación ganadora: ID {metadata['winner']['combination_id']}")
        print(f"   CR esperado del ganador: {metadata['winner']['expected_conversion_rate']:.1%}")
        
        return filename


def main():
    """Función principal."""
    print("=" * 70)
    print("  GENERADOR DE DATOS DEMO - MULTI-ELEMENTO FACTORIAL")
    print("=" * 70)
    
    # Generar datos
    generator = MultiElementDemoGenerator(n_visitors=10000, random_seed=42)
    matrix = generator.generate_conversion_matrix()
    
    # Exportar archivos
    print("\n" + "=" * 70)
    print("  EXPORTANDO ARCHIVOS")
    print("=" * 70)
    csv_file = generator.export_to_csv(matrix)
    json_file = generator.export_metadata()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("  ✅ GENERACIÓN COMPLETA")
    print("=" * 70)
    print(f"\nArchivos creados:")
    print(f"  1. {csv_file}")
    print(f"  2. {json_file}")
    print(f"\nPróximos pasos:")
    print(f"  1. Validar: python scripts/validate_factorial_setup.py")
    print(f"  2. Ejecutar demo: python scripts/run_demo_multielement.py")
    print("\n")


if __name__ == '__main__':
    main()
