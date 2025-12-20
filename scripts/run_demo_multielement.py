# scripts/run_demo_multielement.py

"""
Script para ejecutar demo completo de experimentos multi-elemento FACTORIAL.

Este script simula un experimento multi-elemento real usando el modo FACTORIAL,
comparando el enfoque tradicional (split uniforme) contra el enfoque adaptativo
de Samplit con Thompson Sampling.

MODO FACTORIAL:
- Adaptive learning trata cada combinación completa como una variante
- Aprende qué COMBINACIÓN funciona mejor (no elementos individuales)
- Captura efectos de interacción entre elementos
- Asigna más tráfico automáticamente a las mejores combinaciones

Requiere:
- demo_multielement_matrix.csv (generado por generate_demo_data.py)
- demo_multielement_metadata.json (generado por generate_demo_data.py)
- Base de datos PostgreSQL corriendo

Output:
- demo_comparison_results.json: Resultados comparativos
- Logs detallados del progreso
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to import from orchestration
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import DatabaseManager
from orchestration.repositories.experiment_repository import ExperimentRepository
from orchestration.services.multi_element_service import (
    create_multi_element_experiment,
    allocate_user_multi_element,
    record_conversion_multi_element
)


class MultiElementDemo:
    """Ejecuta demo de experimento multi-elemento factorial."""
    
    def __init__(self):
        """Inicializa el demo."""
        self.matrix_file = 'demo_multielement_matrix.csv'
        self.metadata_file = 'demo_multielement_metadata.json'
        
        # Cargar datos
        self.matrix = None
        self.metadata = None
        self.n_visitors = 0
        self.n_combinations = 0
        
    def load_data(self):
        """Carga matriz de conversiones y metadata."""
        print("\n📥 Cargando datos del demo...")
        
        # Verificar archivos
        if not Path(self.matrix_file).exists():
            raise FileNotFoundError(
                f"❌ No se encuentra {self.matrix_file}\n"
                f"   Ejecuta primero: python scripts/generate_demo_data.py"
            )
        
        if not Path(self.metadata_file).exists():
            raise FileNotFoundError(
                f"❌ No se encuentra {self.metadata_file}\n"
                f"   Ejecuta primero: python scripts/generate_demo_data.py"
            )
        
        # Cargar matriz
        print(f"  Leyendo {self.matrix_file}...")
        self.matrix = pd.read_csv(self.matrix_file)
        self.n_visitors = len(self.matrix)
        self.n_combinations = len(self.matrix.columns)
        
        # Cargar metadata
        print(f"  Leyendo {self.metadata_file}...")
        with open(self.metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        print(f"\n✅ Datos cargados:")
        print(f"  Visitantes: {self.n_visitors:,}")
        print(f"  Combinaciones: {self.n_combinations}")
        print(f"  Modo: {self.metadata['combination_mode'].upper()}")
        
        # Mostrar combinación ganadora esperada
        winner = self.metadata['winner']
        print(f"\n🏆 Combinación ganadora esperada:")
        print(f"  ID: {winner['combination_id']}")
        print(f"  Elementos: {winner['element_values']}")
        print(f"  CR esperado: {winner['expected_conversion_rate']:.1%}")
        
    def simulate_traditional_split(self):
        """
        Simula enfoque tradicional con split uniforme.
        
        Returns:
            dict: Resultados de la simulación
        """
        print("\n" + "=" * 70)
        print("  SIMULACIÓN: ENFOQUE TRADICIONAL (Split Uniforme)")
        print("=" * 70)
        
        # Split uniforme: cada combinación recibe igual tráfico
        visitors_per_combo = self.n_visitors // self.n_combinations
        
        print(f"\n📊 Configuración:")
        print(f"  Tráfico por combinación: {visitors_per_combo:,} visitors")
        print(f"  Distribución: Uniforme (11.1% cada una)")
        
        # Calcular conversiones
        total_conversions = 0
        combination_stats = {}
        
        print(f"\n🔄 Procesando conversiones...")
        
        for idx in range(self.n_combinations):
            # Tomar primeros N visitantes para esta combinación
            start_idx = idx * visitors_per_combo
            end_idx = start_idx + visitors_per_combo
            
            # Obtener conversiones de la matriz
            conversions = self.matrix.iloc[start_idx:end_idx, idx].sum()
            total_conversions += conversions
            
            conversion_rate = conversions / visitors_per_combo
            
            combination_stats[idx] = {
                'visitors': visitors_per_combo,
                'conversions': int(conversions),
                'conversion_rate': conversion_rate,
                'traffic_percentage': 100.0 / self.n_combinations
            }
            
            combo_info = self.metadata['combinations'][idx]
            print(f"  Combo {idx} ({combo_info['element_values']}): "
                  f"{conversions:,} conversions ({conversion_rate:.1%})")
        
        results = {
            'approach': 'traditional_uniform_split',
            'total_visitors': self.n_visitors,
            'total_conversions': int(total_conversions),
            'overall_conversion_rate': total_conversions / self.n_visitors,
            'combination_stats': combination_stats
        }
        
        print(f"\n✅ Resultados Tradicionales:")
        print(f"  Total conversiones: {total_conversions:,}")
        print(f"  CR promedio: {results['overall_conversion_rate']:.2%}")
        
        return results
    
    def simulate_with_samplit_factorial(self):
        """
        Simula enfoque de Samplit con Thompson Sampling en modo FACTORIAL.
        
        Returns:
            dict: Resultados de la simulación
        """
        print("\n" + "=" * 70)
        print("  SIMULACIÓN: SAMPLIT ADAPTATIVO (Factorial Thompson Sampling)")
        print("=" * 70)
        
        # Inicializar base de datos
        db = DatabaseManager()
        db.ensure_schema()
        
        repo = ExperimentRepository(db.get_session())
        
        # Crear experimento multi-elemento
        print(f"\n🎯 Creando experimento multi-elemento...")
        
        elements_config = [
            {
                'name': name,
                'variants': data['variants']
            }
            for name, data in self.metadata['elements'].items()
        ]
        
        experiment = create_multi_element_experiment(
            repo=repo,
            name="Demo Multi-Element Factorial",
            elements=elements_config,
            combination_mode='factorial'  # MODO FACTORIAL
        )
        
        print(f"  ✅ Experimento creado: ID {experiment.id}")
        print(f"  Modo: FACTORIAL")
        print(f"  Total combinaciones: {len(experiment.combinations)}")
        
        # Simular visitantes
        print(f"\n🔄 Procesando {self.n_visitors:,} visitantes...")
        print(f"  Thompson Sampling aprenderá la mejor combinación...")
        
        combination_allocations = {i: 0 for i in range(self.n_combinations)}
        combination_conversions = {i: 0 for i in range(self.n_combinations)}
        
        # Procesar visitantes en batches (para mostrar progreso)
        batch_size = 1000
        for batch_start in range(0, self.n_visitors, batch_size):
            batch_end = min(batch_start + batch_size, self.n_visitors)
            
            for visitor_idx in range(batch_start, batch_end):
                user_id = f"demo_user_{visitor_idx}"
                
                # Asignar combinación usando Thompson Sampling
                result = allocate_user_multi_element(
                    repo=repo,
                    experiment_id=experiment.id,
                    user_id=user_id
                )
                
                combination_id = result['combination_id']
                combination_allocations[combination_id] += 1
                
                # Verificar si hubo conversión (desde la matriz)
                converted = bool(self.matrix.iloc[visitor_idx, combination_id])
                
                if converted:
                    # Registrar conversión
                    record_conversion_multi_element(
                        repo=repo,
                        experiment_id=experiment.id,
                        user_id=user_id,
                        combination_id=combination_id
                    )
                    combination_conversions[combination_id] += 1
            
            # Mostrar progreso
            if (batch_end % 2000) == 0 or batch_end == self.n_visitors:
                progress = (batch_end / self.n_visitors) * 100
                total_conv = sum(combination_conversions.values())
                print(f"  Progreso: {batch_end:,}/{self.n_visitors:,} ({progress:.0f}%) "
                      f"- Conversiones: {total_conv:,}")
        
        # Calcular estadísticas finales
        total_conversions = sum(combination_conversions.values())
        
        combination_stats = {}
        for idx in range(self.n_combinations):
            visitors = combination_allocations[idx]
            conversions = combination_conversions[idx]
            conversion_rate = conversions / visitors if visitors > 0 else 0
            traffic_pct = (visitors / self.n_visitors) * 100
            
            combination_stats[idx] = {
                'visitors': visitors,
                'conversions': conversions,
                'conversion_rate': conversion_rate,
                'traffic_percentage': traffic_pct
            }
        
        results = {
            'approach': 'samplit_factorial_thompson_sampling',
            'experiment_id': experiment.id,
            'total_visitors': self.n_visitors,
            'total_conversions': total_conversions,
            'overall_conversion_rate': total_conversions / self.n_visitors,
            'combination_stats': combination_stats
        }
        
        # Encontrar combinación ganadora (la que más conversiones generó)
        winner_id = max(combination_conversions.items(), key=lambda x: x[1])[0]
        winner_stats = combination_stats[winner_id]
        
        print(f"\n✅ Resultados Samplit:")
        print(f"  Total conversiones: {total_conversions:,}")
        print(f"  CR promedio: {results['overall_conversion_rate']:.2%}")
        print(f"\n🏆 Combinación ganadora detectada:")
        print(f"  ID: {winner_id}")
        print(f"  Elementos: {self.metadata['combinations'][winner_id]['element_values']}")
        print(f"  Tráfico recibido: {winner_stats['traffic_percentage']:.1f}%")
        print(f"  Conversiones: {winner_stats['conversions']:,}")
        print(f"  CR: {winner_stats['conversion_rate']:.1%}")
        
        # Cleanup
        db.close()
        
        return results
    
    def compare_results(self, traditional_results, samplit_results):
        """
        Compara resultados y genera reporte.
        
        Args:
            traditional_results: Resultados del enfoque tradicional
            samplit_results: Resultados de Samplit
        """
        print("\n" + "=" * 70)
        print("  COMPARACIÓN DE RESULTADOS")
        print("=" * 70)
        
        trad_conv = traditional_results['total_conversions']
        samp_conv = samplit_results['total_conversions']
        
        improvement = samp_conv - trad_conv
        improvement_pct = (improvement / trad_conv) * 100 if trad_conv > 0 else 0
        
        print(f"\n📊 Conversiones Totales:")
        print(f"  Traditional:    {trad_conv:,}")
        print(f"  Samplit:        {samp_conv:,}")
        print(f"  Diferencia:     {improvement:+,} ({improvement_pct:+.1f}%)")
        
        if improvement > 0:
            print(f"\n🎉 ¡Samplit ganó! +{improvement:,} conversiones extra")
        
        # Mostrar distribución de tráfico
        print(f"\n📈 Distribución de Tráfico:")
        print(f"\n  TRADITIONAL (Uniforme):")
        for idx in range(3):  # Mostrar primeras 3
            stats = traditional_results['combination_stats'][idx]
            combo = self.metadata['combinations'][idx]
            print(f"    Combo {idx} ({combo['element_values']}): "
                  f"{stats['traffic_percentage']:.1f}%")
        print(f"    ... (todas 11.1%)")
        
        print(f"\n  SAMPLIT (Adaptativo):")
        # Ordenar por tráfico
        sorted_combos = sorted(
            samplit_results['combination_stats'].items(),
            key=lambda x: x[1]['traffic_percentage'],
            reverse=True
        )
        for idx, stats in sorted_combos[:5]:  # Top 5
            combo = self.metadata['combinations'][idx]
            print(f"    Combo {idx} ({combo['element_values']}): "
                  f"{stats['traffic_percentage']:.1f}% "
                  f"({stats['conversions']:,} conv)")
        
        # Guardar resultados
        comparison = {
            'traditional': traditional_results,
            'samplit': samplit_results,
            'comparison': {
                'improvement_conversions': improvement,
                'improvement_percentage': improvement_pct,
                'winner': 'samplit' if improvement > 0 else 'traditional'
            },
            'metadata': self.metadata
        }
        
        output_file = 'demo_comparison_results.json'
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f"\n💾 Resultados guardados en: {output_file}")
    
    def run(self):
        """Ejecuta el demo completo."""
        print("\n" + "=" * 70)
        print("  DEMO: MULTI-ELEMENTO FACTORIAL")
        print("=" * 70)
        
        try:
            # Cargar datos
            self.load_data()
            
            # Simular enfoque tradicional
            traditional_results = self.simulate_traditional_split()
            
            # Simular con Samplit
            samplit_results = self.simulate_with_samplit_factorial()
            
            # Comparar
            self.compare_results(traditional_results, samplit_results)
            
            print("\n" + "=" * 70)
            print("  ✅ DEMO COMPLETADO")
            print("=" * 70)
            print("\nResultados guardados en: demo_comparison_results.json\n")
            
        except Exception as e:
            print(f"\n❌ Error durante el demo: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        return 0


def main():
    """Función principal."""
    demo = MultiElementDemo()
    return demo.run()


if __name__ == '__main__':
    sys.exit(main())
