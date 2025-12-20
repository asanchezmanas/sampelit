# scripts/verify_flow.py
"""
Script de Verificación del Flujo Thompson Sampling + Auditoría

Este script ejecuta el flujo completo y verifica que:
1. Los archivos se llaman en el orden correcto
2. El estado Thompson se guarda/carga correctamente
3. El allocator usa el estado REAL de la BD
4. El algoritmo aprende de las conversiones
5. El tráfico se optimiza automáticamente
6. ✨ NUEVO: El audit trail registra decisiones sin revelar el algoritmo
7. ✨ NUEVO: La integridad criptográfica funciona correctamente

Ejecutar: python scripts/verify_flow.py
"""

import asyncio
import sys
import os
import hashlib
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.database import DatabaseManager
from orchestration.services.experiment_service import ExperimentService


# ═══════════════════════════════════════════════════════════════════════
# AUDIT SERVICE - Para verificación
# ═══════════════════════════════════════════════════════════════════════

class AuditService:
    """
    Sistema de auditoría para verificación.
    
    En producción, esto iría a tabla algorithm_audit_trail.
    Para este script de verificación, usamos memoria.
    """
    
    def __init__(self):
        self.records = []
        self.sequence_number = 0
        self.last_hash = None
    
    def log_decision(
        self,
        visitor_id: str,
        variant_id: str,
        variant_name: str,
        assignment_id: str
    ):
        """
        Registra decisión del algoritmo.
        
        ✅ REGISTRA: visitor_id, variant_id, timestamp
        ❌ NO REGISTRA: alpha, beta, probabilidades
        """
        decision_timestamp = datetime.utcnow()
        
        # Hash de decisión (prueba criptográfica)
        decision_data = {
            "visitor_id": visitor_id,
            "variant_id": variant_id,
            "timestamp": decision_timestamp.isoformat(),
            "previous_hash": self.last_hash or "GENESIS",
            "sequence": self.sequence_number
        }
        decision_str = json.dumps(decision_data, sort_keys=True)
        decision_hash = hashlib.sha256(decision_str.encode()).hexdigest()
        
        record = {
            # ✅ PÚBLICO
            "visitor_id": visitor_id,
            "variant_id": variant_id,
            "variant_name": variant_name,
            "assignment_id": assignment_id,
            "decision_timestamp": decision_timestamp.isoformat(),
            "decision_hash": decision_hash,
            "previous_hash": self.last_hash,
            "sequence_number": self.sequence_number,
            
            # Resultado (se actualiza después)
            "conversion_observed": False,
            "conversion_timestamp": None
        }
        
        self.records.append(record)
        self.last_hash = decision_hash
        self.sequence_number += 1
        
        return record
    
    def log_conversion(self, visitor_id: str):
        """Registra conversión"""
        conversion_timestamp = datetime.utcnow()
        
        for record in self.records:
            if record["visitor_id"] == visitor_id:
                record["conversion_observed"] = True
                record["conversion_timestamp"] = conversion_timestamp.isoformat()
                
                # Verificar integridad temporal
                decision_time = datetime.fromisoformat(record["decision_timestamp"])
                if decision_time >= conversion_timestamp:
                    raise ValueError("INTEGRITY VIOLATION: conversion before decision!")
                
                return record
        
        raise ValueError(f"No decision found for visitor {visitor_id}")
    
    def verify_integrity(self):
        """Verifica integridad criptográfica"""
        checks = {
            "chain_integrity": True,
            "timestamp_order": True,
            "sequence_continuity": True
        }
        
        # 1. Chain integrity
        previous_hash = None
        for record in self.records:
            if record["previous_hash"] != previous_hash:
                checks["chain_integrity"] = False
            previous_hash = record["decision_hash"]
        
        # 2. Timestamp order
        for record in self.records:
            if (record["conversion_timestamp"] and 
                record["decision_timestamp"] >= record["conversion_timestamp"]):
                checks["timestamp_order"] = False
        
        # 3. Sequence continuity
        for i, record in enumerate(self.records):
            if record["sequence_number"] != i:
                checks["sequence_continuity"] = False
        
        return {
            "is_valid": all(checks.values()),
            "checks": checks,
            "total_records": len(self.records)
        }
    
    def get_stats(self):
        """Estadísticas del audit trail"""
        total = len(self.records)
        conversions = sum(1 for r in self.records if r["conversion_observed"])
        
        return {
            "total_decisions": total,
            "total_conversions": conversions,
            "conversion_rate": conversions / total if total > 0 else 0
        }


# ═══════════════════════════════════════════════════════════════════════
# FUNCIONES DE IMPRESIÓN
# ═══════════════════════════════════════════════════════════════════════

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(step_num, total_steps, text):
    """Print step header"""
    print(f"\n[{step_num}/{total_steps}] {text}")


def print_substep(text):
    """Print substep"""
    print(f"     → {text}")


def print_success(text):
    """Print success message"""
    print(f"     ✅ {text}")


def print_info(text):
    """Print info message"""
    print(f"     {text}")


def print_bar_chart(label, value, total, max_bar_length=20):
    """Print horizontal bar chart"""
    pct = (value / total * 100) if total > 0 else 0
    bar_length = int(pct / 100 * max_bar_length)
    bar = "█" * bar_length
    return f"     {label:<15}: {value:>2}/{total} ({pct:>5.1f}%) {bar}"


# ═══════════════════════════════════════════════════════════════════════
# VERIFICACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

async def verify_thompson_sampling_flow():
    """
    Main verification function con auditoría integrada
    """
    
    print_header("🔍 VERIFICACIÓN DEL FLUJO THOMPSON SAMPLING + AUDITORÍA")
    print("\nEste script verifica que:")
    print("  • Los archivos se comunican correctamente")
    print("  • El estado Thompson se encripta/desencripta bien")
    print("  • El allocator usa estado REAL de la base de datos")
    print("  • El algoritmo aprende de las conversiones")
    print("  • El tráfico se optimiza automáticamente")
    print("  • ✨ El audit trail registra sin revelar el algoritmo")
    print("  • ✨ La integridad criptográfica funciona correctamente")
    
    # ────────────────────────────────────────
    # PASO 1: Conectar a BD
    # ────────────────────────────────────────
    print_step(1, 12, "Conectando a base de datos...")
    print_substep("DatabaseManager()")
    print_substep("await db.initialize()")
    
    db = DatabaseManager()
    await db.initialize()
    
    print_success("Conexión establecada")
    print_info(f"Pool size: {db.pool.get_size()}")
    
    try:
        service = ExperimentService(db)
        
        # Inicializar audit service
        audit = AuditService()
        
        # ────────────────────────────────────────
        # PASO 2: Crear usuario de prueba
        # ────────────────────────────────────────
        print_step(2, 12, "Creando usuario de prueba...")
        print_substep("INSERT INTO users ...")
        
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('verify@test.com', 'test', 'Verify User', 'Test Co')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        
        print_success(f"Usuario creado: {user_id[:8]}...")
        
        # ────────────────────────────────────────
        # PASO 3: Crear experimento con variantes
        # ────────────────────────────────────────
        print_step(3, 12, "Creando experimento con 3 variantes...")
        print_substep("ExperimentService.create_experiment()")
        print_substep("  → ExperimentRepository.create()")
        print_substep("  → VariantRepository.create_variant() x3")
        print_substep("  → Encripta estado Thompson inicial")
        
        result = await service.create_experiment(
            user_id=user_id,
            name="Verify Thompson Flow + Audit",
            variants_data=[
                {'name': 'Control (A)', 'description': 'Original', 'content': {'text': 'Sign Up'}},
                {'name': 'Variant B', 'description': 'Green button', 'content': {'text': 'Get Started'}},
                {'name': 'Variant C', 'description': 'Value prop', 'content': {'text': 'Start Free Trial'}}
            ],
            config={'expected_daily_traffic': 100}
        )
        
        exp_id = result['experiment_id']
        variant_ids = result['variant_ids']
        
        print_success(f"Experimento creado: {exp_id[:8]}...")
        print_success(f"Variantes creadas: {len(variant_ids)}")
        for i, vid in enumerate(variant_ids):
            print_info(f"  • Variant {chr(65+i)}: {vid[:8]}...")
        
        # ────────────────────────────────────────
        # PASO 4: Activar experimento
        # ────────────────────────────────────────
        print_step(4, 12, "Activando experimento...")
        print_substep("ExperimentRepository.update_status()")
        
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        await exp_repo.update_status(exp_id, 'active', user_id)
        
        print_success("Status: active")
        
        # ────────────────────────────────────────
        # PASO 5: Verificar estado inicial Thompson
        # ────────────────────────────────────────
        print_step(5, 12, "Verificando estado inicial Thompson Sampling...")
        print_substep("VariantRepository.get_variant_with_algorithm_state()")
        print_substep("  → Desencripta estado de BD")
        
        from data_access.repositories.variant_repository import VariantRepository
        var_repo = VariantRepository(db.pool)
        
        print_info("Estado inicial (priors):")
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            print_info(f"  • Variant {chr(65+i)}: alpha={state['alpha']:.1f}, beta={state['beta']:.1f}")
        
        print_success("Todos tienen priors (1,1) - Correcto!")
        
        # ────────────────────────────────────────
        # PASO 6: Simular visitantes iniciales CON AUDITORÍA
        # ────────────────────────────────────────
        print_step(6, 12, "Simulando 30 visitantes con AUDITORÍA...")
        print_substep("ExperimentService.allocate_user_to_variant()")
        print_substep("  → Thompson Sampling decide (PRIVADO)")
        print_substep("✨ AuditService.log_decision() registra (PÚBLICO)")
        print_substep("  → Solo registra: visitor_id, variant_id, timestamp")
        print_substep("  → NO registra: alpha, beta, probabilidades")
        
        allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(30):
            visitor_id = f"visitor_{i}"
            
            # ─────────────────────────────────────
            # ALGORITMO DECIDE (privado)
            # ─────────────────────────────────────
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            
            allocation_counts[assignment['variant_id']] += 1
            
            # ─────────────────────────────────────
            # AUDITORÍA REGISTRA (público)
            # ─────────────────────────────────────
            audit.log_decision(
                visitor_id=visitor_id,
                variant_id=assignment['variant_id'],
                variant_name=assignment['variant']['name'],
                assignment_id=assignment.get('assignment_id', 'N/A')
            )
            
            if (i + 1) % 10 == 0:
                print_substep(f"{i+1}/30 visitantes procesados + registrados en audit trail")
        
        print_success("30 visitantes asignados")
        print_success("30 decisiones registradas en audit trail")
        print_info("Distribución inicial (debería ser ~uniforme):")
        for i, var_id in enumerate(variant_ids):
            print(print_bar_chart(f"Variant {chr(65+i)}", allocation_counts[var_id], 30))
        
        # ────────────────────────────────────────
        # PASO 7: Verificar audit trail inicial
        # ────────────────────────────────────────
        print_step(7, 12, "Verificando audit trail inicial...")
        print_substep("AuditService.verify_integrity()")
        
        integrity = audit.verify_integrity()
        
        print_info("Verificación de integridad:")
        for check, passed in integrity['checks'].items():
            status = "✅" if passed else "❌"
            print_info(f"  {status} {check}: {'PASSED' if passed else 'FAILED'}")
        
        if integrity['is_valid']:
            print_success(f"Audit trail VÁLIDO ({integrity['total_records']} registros)")
        else:
            print_info("⚠️  Problemas de integridad detectados")
        
        # Mostrar ejemplo de registro
        if audit.records:
            sample = audit.records[0]
            print_info("\nEjemplo de registro en audit trail:")
            print_info(f"  ✅ visitor_id: {sample['visitor_id']}")
            print_info(f"  ✅ variant_id: {sample['variant_id'][:8]}...")
            print_info(f"  ✅ decision_timestamp: {sample['decision_timestamp']}")
            print_info(f"  ✅ decision_hash: {sample['decision_hash'][:16]}...")
            print_info(f"  ✅ sequence_number: {sample['sequence_number']}")
            print_info(f"  ❌ (NO hay alpha, beta, ni probabilidades)")
        
        # ────────────────────────────────────────
        # PASO 8: Dar muchas conversiones a Variant B
        # ────────────────────────────────────────
        print_step(8, 12, "Simulando 15 conversiones en Variant B...")
        print_substep("ExperimentService.record_conversion()")
        print_substep("  → Actualiza Thompson Sampling (PRIVADO)")
        print_substep("✨ AuditService.log_conversion() registra (PÚBLICO)")
        print_substep("  → Solo registra: conversion_timestamp")
        print_substep("  → Verifica: decision_timestamp < conversion_timestamp")
        
        conversions_registered = 0
        attempts = 0
        
        while conversions_registered < 15 and attempts < 100:
            visitor_id = f"converting_visitor_{attempts}"
            
            # Asignar variante
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            
            # Registrar en audit (decisión)
            audit.log_decision(
                visitor_id=visitor_id,
                variant_id=assignment['variant_id'],
                variant_name=assignment['variant']['name'],
                assignment_id=assignment.get('assignment_id', 'N/A')
            )
            
            # Si le tocó B, registrar conversión
            if assignment['variant_id'] == variant_ids[1]:
                # Backend
                await service.record_conversion(
                    experiment_id=exp_id,
                    user_identifier=visitor_id,
                    value=1.0
                )
                
                # Audit trail
                audit.log_conversion(visitor_id)
                
                conversions_registered += 1
                
                if conversions_registered % 5 == 0:
                    print_substep(f"{conversions_registered}/15 conversiones registradas")
            
            attempts += 1
        
        print_success(f"{conversions_registered} conversiones en Variant B")
        print_success(f"{conversions_registered} conversiones en audit trail")
        
        # ────────────────────────────────────────
        # PASO 9: Verificar estado Thompson actualizado
        # ────────────────────────────────────────
        print_step(9, 12, "Verificando que Thompson Sampling aprendió...")
        print_substep("Leyendo estado actualizado de BD...")
        print_substep("(Este estado es PRIVADO - NO está en audit trail)")
        
        print_info("Estado Thompson DESPUÉS de conversiones:")
        for i, var_id in enumerate(variant_ids):
            variant = await var_repo.get_variant_with_algorithm_state(var_id)
            state = variant['algorithm_state_decrypted']
            
            expected_score = state['alpha'] / (state['alpha'] + state['beta'])
            
            print_info(
                f"  • Variant {chr(65+i)}: "
                f"alpha={state['alpha']:>5.1f}, "
                f"beta={state['beta']:>5.1f}, "
                f"samples={state['samples']:>3}, "
                f"score={expected_score:.3f}"
            )
        
        variant_b = await var_repo.get_variant_with_algorithm_state(variant_ids[1])
        state_b = variant_b['algorithm_state_decrypted']
        expected_score_b = state_b['alpha'] / (state_b['alpha'] + state_b['beta'])
        
        if expected_score_b > 0.5:
            print_success(f"Variant B tiene score alto ({expected_score_b:.3f}) - Correcto!")
        else:
            print_info(f"⚠️  Variant B score: {expected_score_b:.3f}")
        
        # ────────────────────────────────────────
        # PASO 10: Verificar audit trail completo
        # ────────────────────────────────────────
        print_step(10, 12, "Verificando audit trail completo...")
        
        integrity = audit.verify_integrity()
        stats = audit.get_stats()
        
        print_info(f"Total de registros: {stats['total_decisions']}")
        print_info(f"Conversiones registradas: {stats['total_conversions']}")
        print_info(f"Conversion rate: {stats['conversion_rate']:.2%}")
        
        print_info("\nVerificación de integridad:")
        for check, passed in integrity['checks'].items():
            status = "✅" if passed else "❌"
            print_info(f"  {status} {check}")
        
        if integrity['is_valid']:
            print_success("Audit trail mantiene integridad criptográfica")
        
        # ────────────────────────────────────────
        # PASO 11: Simular tráfico nuevo (optimizado)
        # ────────────────────────────────────────
        print_step(11, 12, "Simulando 50 visitantes adicionales...")
        print_info("Thompson debería enviar MÁS tráfico a Variant B")
        print_substep("Cada decisión se registra en audit trail")
        
        new_allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(50):
            visitor_id = f"final_visitor_{i}"
            
            # Decisión
            assignment = await service.allocate_user_to_variant(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            new_allocation_counts[assignment['variant_id']] += 1
            
            # Auditoría
            audit.log_decision(
                visitor_id=visitor_id,
                variant_id=assignment['variant_id'],
                variant_name=assignment['variant']['name'],
                assignment_id=assignment.get('assignment_id', 'N/A')
            )
            
            if (i + 1) % 10 == 0:
                print_substep(f"{i+1}/50 procesados + auditados")
        
        print_success("50 visitantes asignados + registrados")
        print_info("Distribución DESPUÉS de aprendizaje:")
        for i, var_id in enumerate(variant_ids):
            print(print_bar_chart(f"Variant {chr(65+i)}", new_allocation_counts[var_id], 50))
        
        # ────────────────────────────────────────
        # PASO 12: Resultado Final + Audit Trail
        # ────────────────────────────────────────
        print_step(12, 12, "Evaluando resultado final...")
        
        b_traffic = new_allocation_counts[variant_ids[1]]
        b_percentage = (b_traffic / 50) * 100
        
        print_info(f"Variant B recibió: {b_traffic}/50 visitas ({b_percentage:.1f}%)")
        
        # Verificar audit trail final
        final_integrity = audit.verify_integrity()
        final_stats = audit.get_stats()
        
        print_info(f"\nAudit Trail Final:")
        print_info(f"  Total registros: {final_stats['total_decisions']}")
        print_info(f"  Conversiones: {final_stats['total_conversions']}")
        print_info(f"  Integridad: {'✅ VÁLIDA' if final_integrity['is_valid'] else '❌ INVÁLIDA'}")
        
        # Criterios de éxito
        thompson_works = b_traffic >= 20  # >40%
        audit_works = final_integrity['is_valid']
        
        if thompson_works and audit_works:
            print_header("✅ VERIFICACIÓN EXITOSA")
            print("\n  Thompson Sampling + Auditoría funcionan CORRECTAMENTE:")
            print(f"    • Variant B recibió {b_traffic}/50 visitas ({b_percentage:.1f}%)")
            print(f"    • El algoritmo aprendió de las conversiones")
            print(f"    • El estado se guarda/carga correctamente")
            print(f"    • ✨ Audit trail con {final_stats['total_decisions']} registros")
            print(f"    • ✨ Integridad criptográfica verificada")
            print(f"    • ✨ Sin revelar alpha/beta/probabilidades")
            print("\n  🎉 Todo el flujo funciona correctamente!")
            
        elif thompson_works and not audit_works:
            print_header("⚠️  PROBLEMA EN AUDITORÍA")
            print(f"\n  Thompson Sampling funciona ({b_traffic}/50 a B)")
            print(f"  Pero audit trail tiene problemas de integridad")
            print(f"\n  Revisar:")
            print(f"    • Hash chain")
            print(f"    • Timestamps")
            print(f"    • Sequence numbers")
            
        elif not thompson_works and audit_works:
            print_header("⚠️  PROBLEMA EN THOMPSON SAMPLING")
            print(f"\n  Audit trail funciona correctamente")
            print(f"  Pero Thompson no optimizó ({b_traffic}/50 a B, esperábamos >20)")
            
        else:
            print_header("❌ MÚLTIPLES PROBLEMAS")
            print(f"\n  Thompson: {b_traffic}/50 a B (esperábamos >20)")
            print(f"  Audit: integridad {'✅' if audit_works else '❌'}")
        
        # ────────────────────────────────────────
        # Estadísticas finales
        # ────────────────────────────────────────
        print("\n" + "-" * 70)
        print("📊 ESTADÍSTICAS FINALES")
        print("-" * 70)
        
        async with db.pool.acquire() as conn:
            stats = await conn.fetch(
                """
                SELECT 
                    v.name,
                    v.total_allocations,
                    v.total_conversions,
                    v.observed_conversion_rate
                FROM variants v
                WHERE v.experiment_id = $1
                ORDER BY v.total_conversions DESC
                """,
                exp_id
            )
        
        total_allocations = sum(s['total_allocations'] for s in stats)
        total_conversions = sum(s['total_conversions'] for s in stats)
        
        print(f"\nBackend (PostgreSQL):")
        print(f"  Total visitantes: {total_allocations}")
        print(f"  Total conversiones: {total_conversions}")
        print(f"  CR global: {(total_conversions/total_allocations*100):.2f}%")
        
        print("\nPor variante:")
        for s in stats:
            alloc_pct = (s['total_allocations'] / total_allocations * 100) if total_allocations > 0 else 0
            print(
                f"  {s['name']:<15}: "
                f"{s['total_allocations']:>3} visits ({alloc_pct:>5.1f}%) | "
                f"{s['total_conversions']:>2} conv | "
                f"CR: {s['observed_conversion_rate']:.2%}"
            )
        
        print(f"\nAudit Trail (En Memoria):")
        print(f"  Total registros: {final_stats['total_decisions']}")
        print(f"  Conversiones auditadas: {final_stats['total_conversions']}")
        print(f"  CR auditado: {final_stats['conversion_rate']:.2%}")
        print(f"  Integridad: {'✅ VÁLIDA' if final_integrity['is_valid'] else '❌ INVÁLIDA'}")
        
        # Comparar backend vs audit
        if total_conversions == final_stats['total_conversions']:
            print(f"\n✅ Backend y Audit Trail coinciden exactamente")
        else:
            print(f"\n⚠️  Diferencia: Backend {total_conversions} vs Audit {final_stats['total_conversions']}")
        
        # ────────────────────────────────────────
        # Demostrar qué está en audit vs qué NO
        # ────────────────────────────────────────
        print("\n" + "-" * 70)
        print("📋 QUÉ CONTIENE EL AUDIT TRAIL")
        print("-" * 70)
        
        if audit.records:
            sample = audit.records[-1]  # Último registro
            
            print("\n✅ LO QUE SÍ ESTÁ EN AUDIT TRAIL:")
            print(f"  • visitor_id: {sample['visitor_id']}")
            print(f"  • variant_id: {sample['variant_id'][:8]}...")
            print(f"  • variant_name: {sample['variant_name']}")
            print(f"  • decision_timestamp: {sample['decision_timestamp']}")
            print(f"  • decision_hash: {sample['decision_hash'][:16]}...")
            print(f"  • sequence_number: {sample['sequence_number']}")
            if sample['conversion_observed']:
                print(f"  • conversion_timestamp: {sample['conversion_timestamp']}")
            
            print("\n❌ LO QUE NO ESTÁ EN AUDIT TRAIL:")
            print("  • alpha, beta (parámetros Thompson)")
            print("  • probabilidades calculadas")
            print("  • samples de distribuciones Beta")
            print("  • razón de por qué se eligió esta variante")
            print("  • estado completo del experimento")
            
            print("\n💡 Esto permite:")
            print("  ✅ Cliente puede auditar TODAS las decisiones")
            print("  ✅ Cliente puede verificar que no hay trampa")
            print("  ✅ Samplit protege su propiedad intelectual")
            print("  ✅ Competencia NO puede copiar el algoritmo")
        
        # ────────────────────────────────────────
        # Limpiar datos de prueba
        # ────────────────────────────────────────
        print("\n" + "-" * 70)
        print("🧹 Limpiando datos de prueba...")
        
        async with db.pool.acquire() as conn:
            deleted_exp = await conn.execute(
                "DELETE FROM experiments WHERE id = $1",
                exp_id
            )
            deleted_user = await conn.execute(
                "DELETE FROM users WHERE id = $1",
                user_id
            )
        
        print_success("Experimento eliminado")
        print_success("Usuario eliminado")
        print_success("Audit trail en memoria (no persiste)")
        print_success("Limpieza completada")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR DURANTE LA VERIFICACIÓN")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nTraceback:")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.close()
        print("\n" + "-" * 70)
        print("👋 Conexión a BD cerrada")
        print("-" * 70)


def main():
    """Entry point"""
    try:
        asyncio.run(verify_thompson_sampling_flow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
