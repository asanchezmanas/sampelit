"""
EJEMPLO COMPLETO: Sistema de Auditoría en Tiempo Real

Este script demuestra:
1. Crear experimento con auditoría
2. Simular tráfico
3. Registrar conversiones
4. Verificar integridad
5. Exportar audit trail
6. Generar prueba de fairness

Ejecutar:
    python examples/audit_demo.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from datetime import datetime, timedelta
import random
import time
import json

from database.connection import DatabaseManager
from repositories.experiment_repository import ExperimentRepository
from services.experiment_service import ExperimentService
from services.audit_service import AuditableExperimentService


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

N_VISITORS = 1000
CONVERSION_RATES = {
    'control': 0.02,      # 2% CR
    'variant_a': 0.025,   # 2.5% CR
    'variant_b': 0.03     # 3% CR (ganadora)
}


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def print_section(title):
    """Imprime título de sección."""
    print("\n" + "═" * 70)
    print(f"  {title}")
    print("═" * 70 + "\n")


def print_stats(label, value):
    """Imprime estadística."""
    print(f"  {label:.<50} {value}")


# ═══════════════════════════════════════════════════════════════════════════
# PASO 1: Setup
# ═══════════════════════════════════════════════════════════════════════════

def setup_experiment():
    """
    Crea un experimento de prueba.
    """
    print_section("PASO 1: Creando Experimento")
    
    db = DatabaseManager()
    repo = ExperimentRepository(db)
    
    # Crear experimento
    experiment_id = repo.create_experiment(
        user_id='demo_user',
        name='Audit Demo - CTA Button Test',
        description='Demostración del sistema de auditoría'
    )
    
    print_stats("Experimento creado", experiment_id)
    
    # Crear variantes
    control_id = repo.create_variant(
        experiment_id=experiment_id,
        name='Control',
        description='Botón azul "Sign Up"',
        config={'button_color': 'blue', 'button_text': 'Sign Up'}
    )
    
    variant_a_id = repo.create_variant(
        experiment_id=experiment_id,
        name='Variant A',
        description='Botón verde "Get Started"',
        config={'button_color': 'green', 'button_text': 'Get Started'}
    )
    
    variant_b_id = repo.create_variant(
        experiment_id=experiment_id,
        name='Variant B',
        description='Botón rojo "Start Free Trial"',
        config={'button_color': 'red', 'button_text': 'Start Free Trial'}
    )
    
    print_stats("Control", control_id)
    print_stats("Variant A", variant_a_id)
    print_stats("Variant B", variant_b_id)
    
    # Activar experimento
    repo.start_experiment(experiment_id)
    
    print_stats("Estado", "ACTIVE")
    
    return {
        'experiment_id': experiment_id,
        'variants': {
            'control': control_id,
            'variant_a': variant_a_id,
            'variant_b': variant_b_id
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# PASO 2: Simular Tráfico con Auditoría
# ═══════════════════════════════════════════════════════════════════════════

def simulate_traffic(experiment_data):
    """
    Simula tráfico real con auditoría automática.
    """
    print_section("PASO 2: Simulando Tráfico (con auditoría automática)")
    
    db = DatabaseManager()
    service = AuditableExperimentService(db)
    
    experiment_id = experiment_data['experiment_id']
    assignments = []
    
    print(f"Simulando {N_VISITORS} visitantes...")
    print("(cada decisión se registra en el audit trail)\n")
    
    for i in range(N_VISITORS):
        visitor_id = f"visitor_{i}"
        
        # Contexto de la request (se hasheará, NO se guarda completo)
        context = {
            'ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'user_agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Mozilla/5.0 (X11; Linux x86_64)'
            ]),
            'referer': random.choice([
                'https://google.com',
                'https://facebook.com',
                'direct'
            ])
        }
        
        # Asignar usuario
        # ✅ Esto AUTOMÁTICAMENTE registra la decisión en audit_trail
        assignment = service.allocate_user(
            experiment_id=experiment_id,
            visitor_id=visitor_id,
            context=context
        )
        
        assignments.append({
            'assignment_id': assignment.id,
            'visitor_id': visitor_id,
            'variant_id': assignment.variant_id,
            'variant_name': assignment.variant_name
        })
        
        # Progress
        if (i + 1) % 100 == 0:
            print(f"  Procesados: {i + 1}/{N_VISITORS} visitantes")
    
    print(f"\n✅ {N_VISITORS} decisiones registradas en audit trail")
    
    # Mostrar distribución
    print("\n  Distribución de variantes:")
    variants_count = {}
    for a in assignments:
        name = a['variant_name']
        variants_count[name] = variants_count.get(name, 0) + 1
    
    for name, count in sorted(variants_count.items()):
        pct = (count / N_VISITORS) * 100
        print(f"    {name:.<40} {count:>4} ({pct:>5.1f}%)")
    
    return assignments


# ═══════════════════════════════════════════════════════════════════════════
# PASO 3: Simular Conversiones
# ═══════════════════════════════════════════════════════════════════════════

def simulate_conversions(experiment_data, assignments):
    """
    Simula conversiones según tasas predefinidas.
    """
    print_section("PASO 3: Simulando Conversiones")
    
    db = DatabaseManager()
    service = AuditableExperimentService(db)
    repo = ExperimentRepository(db)
    
    # Mapear variant_id a nombre
    variant_names = {}
    with db.get_cursor() as cursor:
        for name, vid in experiment_data['variants'].items():
            variant_names[vid] = name
    
    conversions = 0
    
    print("Procesando conversiones...")
    
    for assignment in assignments:
        variant_name = variant_names.get(assignment['variant_id'])
        
        if not variant_name:
            continue
        
        # Determinar si convierte según CR de la variante
        conversion_rate = CONVERSION_RATES.get(variant_name, 0.02)
        converts = random.random() < conversion_rate
        
        if converts:
            # Simular delay (conversión ocurre después de la decisión)
            # En realidad esto ya pasó, solo estamos registrándolo
            conversion_value = round(random.uniform(9.99, 99.99), 2)
            
            # Registrar conversión
            # ✅ Esto AUTOMÁTICAMENTE actualiza el audit trail
            service.record_conversion(
                assignment_id=assignment['assignment_id'],
                conversion_value=conversion_value
            )
            
            conversions += 1
    
    print(f"\n✅ {conversions}/{N_VISITORS} conversiones registradas")
    
    # Mostrar tasas por variante
    print("\n  Tasas de conversión observadas:")
    
    results = service.get_results(experiment_data['experiment_id'])
    
    for variant in results['variants']:
        expected_cr = CONVERSION_RATES.get(variant['name'].lower().replace(' ', '_'), 0)
        actual_cr = variant['conversion_rate']
        
        print(f"    {variant['name']:.<30} "
              f"Esperada: {expected_cr*100:>4.1f}%  "
              f"Observada: {actual_cr:>4.1f}%  "
              f"({variant['conversions']}/{variant['visitors']})")


# ═══════════════════════════════════════════════════════════════════════════
# PASO 4: Auditoría - Verificar Integridad
# ═══════════════════════════════════════════════════════════════════════════

def verify_audit_integrity(experiment_id):
    """
    Verifica la integridad del audit trail.
    """
    print_section("PASO 4: Verificando Integridad del Audit Trail")
    
    db = DatabaseManager()
    service = AuditableExperimentService(db)
    
    # 1. Obtener estadísticas
    print("1. Estadísticas de auditoría:")
    stats = service.get_audit_stats(experiment_id)
    
    print_stats("Total decisiones", stats['total_decisions'])
    print_stats("Conversiones observadas", stats['conversions'])
    print_stats("Conversiones pendientes", stats['pending_conversions'])
    print_stats("Tasa de conversión", f"{stats['conversion_rate']}%")
    print_stats("Tiempo promedio a conversión", 
                f"{stats['avg_decision_to_conversion_seconds']:.1f}s")
    print_stats("Integridad de cadena", 
                "✅ VÁLIDA" if stats['chain_integrity'] else "❌ INVÁLIDA")
    
    # 2. Verificación detallada de integridad
    print("\n2. Verificación detallada de integridad:")
    integrity = service.verify_integrity(experiment_id)
    
    print_stats("Total registros verificados", integrity['total_checked'])
    print_stats("Registros inválidos", len(integrity['invalid_records']))
    print_stats("Estado final", 
                "✅ VÁLIDO" if integrity['is_valid'] else "❌ INVÁLIDO")
    
    if not integrity['is_valid']:
        print("\n  ⚠️ Registros con problemas:")
        for record in integrity['invalid_records'][:5]:  # Primeros 5
            print(f"    - Secuencia #{record['sequence_number']}")
    
    # 3. Verificar timestamps
    print("\n3. Verificando orden de timestamps:")
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM algorithm_audit_trail
            WHERE experiment_id = %s
            AND conversion_timestamp IS NOT NULL
            AND decision_timestamp >= conversion_timestamp
        """, (str(experiment_id),))
        
        invalid_timestamps = cursor.fetchone()[0]
    
    print_stats("Registros con timestamps inválidos", invalid_timestamps)
    
    if invalid_timestamps > 0:
        print("  ⚠️ ERROR: Hay decisiones registradas DESPUÉS de conversiones")
        print("  Esto sugiere manipulación o error del sistema")
    else:
        print("  ✅ Todas las decisiones fueron registradas ANTES de conversiones")


# ═══════════════════════════════════════════════════════════════════════════
# PASO 5: Exportar Audit Trail
# ═══════════════════════════════════════════════════════════════════════════

def export_audit_trail(experiment_id):
    """
    Exporta el audit trail a CSV.
    """
    print_section("PASO 5: Exportando Audit Trail")
    
    db = DatabaseManager()
    service = AuditableExperimentService(db)
    
    filepath = f"audit_trail_{experiment_id}.csv"
    
    count = service.audit.export_audit_trail_csv(
        experiment_id=experiment_id,
        filepath=filepath
    )
    
    print_stats("Registros exportados", count)
    print_stats("Archivo creado", filepath)
    
    # Mostrar primeras líneas
    print("\n  Primeras 5 líneas del CSV:")
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if i >= 6:  # Header + 5 líneas
                break
            print(f"    {line.strip()}")
    
    print("\n  ✅ Audit trail exportado exitosamente")
    print("  Este archivo puede ser revisado por un auditor externo")


# ═══════════════════════════════════════════════════════════════════════════
# PASO 6: Generar Prueba de Fairness
# ═══════════════════════════════════════════════════════════════════════════

def generate_fairness_proof(experiment_id):
    """
    Genera una prueba completa de que el algoritmo no hace trampa.
    """
    print_section("PASO 6: Prueba de Fairness")
    
    db = DatabaseManager()
    
    print("Ejecutando verificaciones...\n")
    
    checks = {
        'chain_integrity': None,
        'timestamp_order': None,
        'sequence_continuity': None,
        'no_duplicates': None
    }
    
    with db.get_cursor() as cursor:
        # 1. Integridad de cadena
        cursor.execute("""
            SELECT COUNT(*)
            FROM verify_audit_chain(%s)
            WHERE NOT is_valid
        """, (str(experiment_id),))
        
        invalid_chain = cursor.fetchone()[0]
        checks['chain_integrity'] = {
            'passed': invalid_chain == 0,
            'details': f"0 registros con hash inválido" if invalid_chain == 0 
                      else f"{invalid_chain} registros con hash inválido"
        }
        
        # 2. Orden de timestamps
        cursor.execute("""
            SELECT COUNT(*)
            FROM algorithm_audit_trail
            WHERE experiment_id = %s
            AND conversion_timestamp IS NOT NULL
            AND decision_timestamp >= conversion_timestamp
        """, (str(experiment_id),))
        
        invalid_timestamps = cursor.fetchone()[0]
        checks['timestamp_order'] = {
            'passed': invalid_timestamps == 0,
            'details': f"0 violaciones" if invalid_timestamps == 0
                      else f"{invalid_timestamps} violaciones"
        }
        
        # 3. Continuidad de secuencia
        cursor.execute("""
            WITH sequences AS (
                SELECT 
                    sequence_number,
                    sequence_number - LAG(sequence_number) 
                        OVER (ORDER BY sequence_number) as gap
                FROM algorithm_audit_trail
                WHERE experiment_id = %s
            )
            SELECT COUNT(*)
            FROM sequences
            WHERE gap > 1
        """, (str(experiment_id),))
        
        sequence_gaps = cursor.fetchone()[0]
        checks['sequence_continuity'] = {
            'passed': sequence_gaps == 0,
            'details': f"0 gaps encontrados" if sequence_gaps == 0
                      else f"{sequence_gaps} gaps encontrados"
        }
        
        # 4. Sin duplicados
        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT visitor_id, COUNT(*) as cnt
                FROM algorithm_audit_trail
                WHERE experiment_id = %s
                GROUP BY visitor_id
                HAVING COUNT(*) > 1
            ) duplicates
        """, (str(experiment_id),))
        
        duplicate_decisions = cursor.fetchone()[0]
        checks['no_duplicates'] = {
            'passed': duplicate_decisions == 0,
            'details': f"0 duplicados" if duplicate_decisions == 0
                      else f"{duplicate_decisions} visitantes con múltiples asignaciones"
        }
    
    # Resultado final
    is_fair = all(check['passed'] for check in checks.values())
    
    print("  Verificaciones completadas:\n")
    
    for name, check in checks.items():
        status = "✅ PASS" if check['passed'] else "❌ FAIL"
        print(f"    {name:.<35} {status}")
        print(f"      {check['details']}")
    
    print(f"\n{'═' * 70}")
    if is_fair:
        print("  🎉 RESULTADO: Experimento es JUSTO y AUDITABLE")
        print("  ✅ Todas las verificaciones pasaron")
        print("  ✅ No hay evidencia de manipulación")
        print("  ✅ Algoritmo tomó decisiones sin ver resultados")
    else:
        print("  ⚠️ RESULTADO: Se encontraron problemas")
        print("  ❌ Revisar detalles arriba")
    print(f"{'═' * 70}\n")
    
    # Crear JSON de prueba
    proof = {
        'experiment_id': str(experiment_id),
        'is_fair': is_fair,
        'checks': checks,
        'verified_at': datetime.utcnow().isoformat(),
        'verifier': 'Samplit Audit System v1.0'
    }
    
    filepath = f"fairness_proof_{experiment_id}.json"
    with open(filepath, 'w') as f:
        json.dump(proof, f, indent=2)
    
    print(f"  Prueba guardada en: {filepath}")
    
    return is_fair


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Ejecuta la demostración completa del sistema de auditoría.
    """
    print("\n" + "═" * 70)
    print("  SAMPLIT - Sistema de Auditoría en Tiempo Real")
    print("  Demostración Completa")
    print("═" * 70)
    
    try:
        # Paso 1: Setup
        experiment_data = setup_experiment()
        
        # Paso 2: Simular tráfico
        assignments = simulate_traffic(experiment_data)
        
        # Paso 3: Simular conversiones
        simulate_conversions(experiment_data, assignments)
        
        # Paso 4: Verificar integridad
        verify_audit_integrity(experiment_data['experiment_id'])
        
        # Paso 5: Exportar
        export_audit_trail(experiment_data['experiment_id'])
        
        # Paso 6: Prueba de fairness
        is_fair = generate_fairness_proof(experiment_data['experiment_id'])
        
        # Resumen final
        print_section("RESUMEN")
        print("  ✅ Experimento creado y ejecutado")
        print(f"  ✅ {N_VISITORS} visitantes procesados")
        print("  ✅ Conversiones registradas")
        print("  ✅ Auditoría verificada")
        print("  ✅ Audit trail exportado")
        print(f"  {'✅' if is_fair else '❌'} Prueba de fairness generada")
        
        print("\n  Archivos generados:")
        print(f"    - audit_trail_{experiment_data['experiment_id']}.csv")
        print(f"    - fairness_proof_{experiment_data['experiment_id']}.json")
        
        print("\n  " + "═" * 66)
        print("  🎉 Demostración completada exitosamente")
        print("  " + "═" * 66 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
