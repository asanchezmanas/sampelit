#!/usr/bin/env python3
"""
Script de validación para setup de experimentos multi-elemento FACTORIAL.

Valida que los archivos de demo estén correctamente generados y listos
para ejecutar el demo. Verifica formato, consistencia y datos esperados.

Ejecutar antes de run_demo_multielement.py para detectar problemas.
"""

import sys
import json
import pandas as pd
from pathlib import Path


class FactorialSetupValidator:
    """Validador de setup factorial."""
    
    def __init__(self):
        """Inicializa el validador."""
        self.matrix_file = 'demo_multielement_matrix.csv'
        self.metadata_file = 'demo_multielement_metadata.json'
        self.errors = []
        self.warnings = []
        
    def log_error(self, message):
        """Registra un error."""
        self.errors.append(message)
        print(f"  ❌ ERROR: {message}")
    
    def log_warning(self, message):
        """Registra un warning."""
        self.warnings.append(message)
        print(f"  ⚠️  WARNING: {message}")
    
    def log_success(self, message):
        """Registra un éxito."""
        print(f"  ✅ {message}")
    
    def validate_files_exist(self):
        """Valida que los archivos existan."""
        print("\n📁 Validando existencia de archivos...")
        
        if not Path(self.matrix_file).exists():
            self.log_error(f"No se encuentra {self.matrix_file}")
            return False
        else:
            self.log_success(f"Archivo encontrado: {self.matrix_file}")
        
        if not Path(self.metadata_file).exists():
            self.log_error(f"No se encuentra {self.metadata_file}")
            return False
        else:
            self.log_success(f"Archivo encontrado: {self.metadata_file}")
        
        return True
    
    def validate_matrix_format(self):
        """Valida el formato de la matriz."""
        print("\n📊 Validando formato de matriz...")
        
        try:
            df = pd.read_csv(self.matrix_file)
            
            # Verificar shape
            n_rows, n_cols = df.shape
            self.log_success(f"Matriz cargada: {n_rows:,} × {n_cols}")
            
            # Verificar que todos los valores sean 0 o 1 (binarios)
            if not df.isin([0, 1]).all().all():
                self.log_error("La matriz contiene valores que no son 0 o 1")
                return False
            else:
                self.log_success("Todos los valores son binarios (0 o 1)")
            
            # Verificar nombres de columnas
            expected_pattern = "combo_"
            if not all(col.startswith(expected_pattern) for col in df.columns):
                self.log_warning("Algunos nombres de columna no siguen el patrón 'combo_X_...'")
            else:
                self.log_success("Nombres de columnas correctos")
            
            # Calcular estadísticas
            total_conversions = df.sum().sum()
            overall_cr = total_conversions / (n_rows * n_cols)
            
            print(f"\n  📈 Estadísticas de la matriz:")
            print(f"    Total visitantes: {n_rows:,}")
            print(f"    Total combinaciones: {n_cols}")
            print(f"    Total conversiones: {total_conversions:,}")
            print(f"    CR promedio global: {overall_cr:.2%}")
            
            # Validar CR por columna
            print(f"\n  📊 Conversion Rate por combinación:")
            for idx, col in enumerate(df.columns):
                cr = df[col].mean()
                conv = df[col].sum()
                print(f"    {col}: {cr:.1%} ({conv:,} conversiones)")
                
                if cr < 0.01 or cr > 0.10:
                    self.log_warning(
                        f"CR de {col} fuera de rango típico (1%-10%): {cr:.1%}"
                    )
            
            return True
            
        except Exception as e:
            self.log_error(f"Error al cargar matriz: {e}")
            return False
    
    def validate_metadata_format(self):
        """Valida el formato del metadata."""
        print("\n📄 Validando formato de metadata...")
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Campos requeridos
            required_fields = [
                'experiment_name',
                'experiment_type',
                'combination_mode',
                'elements',
                'combinations',
                'winner'
            ]
            
            for field in required_fields:
                if field not in metadata:
                    self.log_error(f"Campo requerido faltante: {field}")
                    return False
                else:
                    self.log_success(f"Campo presente: {field}")
            
            # Validar modo
            if metadata['combination_mode'] != 'factorial':
                self.log_error(
                    f"Modo incorrecto: {metadata['combination_mode']} "
                    f"(esperado: 'factorial')"
                )
                return False
            else:
                self.log_success("Modo correcto: factorial")
            
            # Validar combinaciones
            n_combinations = len(metadata['combinations'])
            print(f"\n  🎯 Combinaciones definidas: {n_combinations}")
            
            for combo in metadata['combinations']:
                if 'combination_id' not in combo:
                    self.log_error("Combinación sin ID")
                    return False
                if 'element_values' not in combo:
                    self.log_error(f"Combinación {combo['combination_id']} sin element_values")
                    return False
            
            self.log_success("Todas las combinaciones tienen formato correcto")
            
            # Validar ganador
            if 'combination_id' not in metadata['winner']:
                self.log_error("Winner sin combination_id")
                return False
            if 'expected_conversion_rate' not in metadata['winner']:
                self.log_error("Winner sin expected_conversion_rate")
                return False
            
            winner_id = metadata['winner']['combination_id']
            winner_cr = metadata['winner']['expected_conversion_rate']
            
            print(f"\n  🏆 Ganador esperado:")
            print(f"    ID: {winner_id}")
            print(f"    CR esperado: {winner_cr:.1%}")
            print(f"    Elementos: {metadata['winner']['element_values']}")
            
            self.log_success("Winner correctamente definido")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"JSON inválido: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error al validar metadata: {e}")
            return False
    
    def validate_consistency(self):
        """Valida consistencia entre matriz y metadata."""
        print("\n🔗 Validando consistencia matriz-metadata...")
        
        try:
            # Cargar ambos archivos
            df = pd.read_csv(self.matrix_file)
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verificar número de combinaciones
            n_matrix_combos = len(df.columns)
            n_metadata_combos = len(metadata['combinations'])
            
            if n_matrix_combos != n_metadata_combos:
                self.log_error(
                    f"Número de combinaciones no coincide: "
                    f"matriz={n_matrix_combos}, metadata={n_metadata_combos}"
                )
                return False
            else:
                self.log_success(
                    f"Número de combinaciones coincide: {n_matrix_combos}"
                )
            
            # Verificar que el ganador existe
            winner_id = metadata['winner']['combination_id']
            if winner_id >= n_metadata_combos:
                self.log_error(
                    f"Winner ID {winner_id} fuera de rango (max: {n_metadata_combos-1})"
                )
                return False
            else:
                self.log_success(f"Winner ID válido: {winner_id}")
            
            # Comparar CRs esperados vs reales
            print(f"\n  📊 Comparación CR esperado vs real:")
            
            max_diff = 0
            for idx, combo in enumerate(metadata['combinations']):
                expected_cr = combo['expected_conversion_rate']
                actual_cr = df.iloc[:, idx].mean()
                diff = abs(actual_cr - expected_cr)
                max_diff = max(max_diff, diff)
                
                status = "✅" if diff < 0.005 else "⚠️"
                print(f"    {status} Combo {idx}: "
                      f"esperado={expected_cr:.1%}, "
                      f"real={actual_cr:.1%}, "
                      f"diff={diff:.1%}")
                
                if diff > 0.01:
                    self.log_warning(
                        f"Combo {idx}: diferencia grande entre esperado y real ({diff:.1%})"
                    )
            
            if max_diff < 0.005:
                self.log_success("CRs muy cercanos a los esperados")
            elif max_diff < 0.01:
                self.log_warning("Algunas diferencias detectadas en CRs")
            else:
                self.log_error("Diferencias significativas en CRs")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error al validar consistencia: {e}")
            return False
    
    def run_validation(self):
        """Ejecuta todas las validaciones."""
        print("=" * 70)
        print("  VALIDACIÓN DE SETUP FACTORIAL")
        print("=" * 70)
        
        # Ejecutar validaciones
        validations = [
            self.validate_files_exist,
            self.validate_matrix_format,
            self.validate_metadata_format,
            self.validate_consistency,
        ]
        
        all_passed = True
        for validation in validations:
            if not validation():
                all_passed = False
        
        # Resumen
        print("\n" + "=" * 70)
        print("  RESUMEN DE VALIDACIÓN")
        print("=" * 70)
        
        if self.errors:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
            all_passed = False
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if all_passed:
            print("\n✅ VALIDACIÓN EXITOSA")
            print("\nPuedes ejecutar el demo:")
            print("  python scripts/run_demo_multielement.py\n")
            return 0
        else:
            print("\n❌ VALIDACIÓN FALLIDA")
            print("\nCorrige los errores antes de continuar.\n")
            return 1


def main():
    """Función principal."""
    validator = FactorialSetupValidator()
    return validator.run_validation()


if __name__ == '__main__':
    sys.exit(main())
