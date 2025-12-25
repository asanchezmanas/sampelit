# scripts/audit_demo.py
# ✅ FIXED: Corrected all imports to match project structure

"""
EJEMPLO COMPLETO: Sistema de Auditoría en Tiempo Real

Este script demuestra:
1. Crear experimento con auditoría
2. Simular tráfico
3. Registrar conversiones
4. Verificar integridad
5. Exportar audit trail
6. Generar prueba de fairness

⚠️ NOTA IMPORTANTE:
Este script es una DEMOSTRACIÓN del concepto de auditoría.
La implementación completa de AuditableExperimentService está
en el roadmap para v1.1 (Q1 2026).

Por ahora, este script muestra cómo FUNCIONARÍA el sistema de auditoría
cuando esté implementado.

Ejecutar:
    python scripts/audit_demo.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from datetime import datetime, timedelta, timezone
import random
import time
import json
import hashlib

# ✅ FIXED: Corrected imports
from data_access.database import DatabaseManager
from data_access.repositories.experiment_repository import ExperimentRepository
from orchestration.services.experiment_service import ExperimentService


# ═══════════════════════════════════════════════════════════════════════
# MOCK AUDIT SERVICE - Para demostración
# ═══════════════════════════════════════════════════════════════════════

class MockAuditService:
    """
    ⚠️ MOCK SERVICE - Para demostración
    
    En producción (v1.1), esto sería AuditableExperimentService que:
    1. Registra cada decisión en algorithm_audit_trail
    2. Crea hash chain para integridad
    3. Permite exportar pruebas de fairness
    4. NO revela parámetros del algoritmo
    
    Esta versión MOCK simula el comportamiento para demostración.
    """
    
    def __init__(self, experiment_service: ExperimentService):
        self.service = experiment_service
        self.audit_records = []
        self.sequence_number = 0
        self.last_hash = None
        
        print("⚠️  Usando MockAuditService (demo only)")
        print("    En producción: AuditableExperimentService (v1.1)")
    
    async def allocate_with_audit(
        self, 
        experiment_id: str, 
        user_identifier: str
    ):
        """
        Asigna variante Y registra decisión en audit trail.
        
        ✅ REGISTRA: visitor_id, variant_id, timestamp, hash
        ❌ NO REGISTRA: alpha, beta, probabilidades
        """
        # 1. Algoritmo decide (privado)
        assignment = await self.service.allocate_user_to_variant(
            experiment_id=experiment_id,
            user_identifier=user_identifier
        )
        
        # 2. Auditoría registra (público)
        decision_timestamp = datetime.now(timezone.utc)
        
        decision_data = {
            "visitor_id": user_identifier,
            "variant_id": assignment['variant_id'],
            "experiment_id": experiment_id,
            "timestamp": decision_timestamp.isoformat(),
            "previous_hash": self.last_hash or "GENESIS",
            "sequence": self.sequence_number
        }
        
        decision_str = json.dumps(decision_data, sort_keys=True)
        decision_hash = hashlib.sha256(decision_str.encode()).hexdigest()
        
        audit_record = {
            "visitor_id": user_identifier,
            "variant_id": assignment['variant_id'],
            "variant_name": assignment['variant']['name'],
            "decision_timestamp": decision_timestamp.isoformat(),
            "decision_hash": decision_hash,
            "previous_hash": self.last_hash,
            "sequence_number": self.sequence_number,
            "converted": False,
            "conversion_timestamp": None
        }
        
        self.audit_records.append(audit_record)
        self.last_hash = decision_hash
        self.sequence_number += 1
        
        return assignment, audit_record
    
    async def record_conversion_with_audit(
        self,
        experiment_id: str,
        user_identifier: str,
        value: float = 1.0
    ):
        """
        Registra conversión Y actualiza audit trail.
        """
        # 1. Registrar conversión en backend
        await self.service.record_conversion(
            experiment_id=experiment_id,
            user_identifier=user_identifier,
            value=value
        )
        
        # 2. Actualizar audit trail
        conversion_timestamp = datetime.now(timezone.utc)
        
        for record in self.audit_records:
            if record["visitor_id"] == user_identifier:
                record["converted"] = True
                record["conversion_timestamp"] = conversion_timestamp.isoformat()
                
                # Verificar integridad temporal
                decision_time = datetime.fromisoformat(record["decision_timestamp"])
                if decision_time >= conversion_timestamp:
                    raise ValueError(
                        "INTEGRITY VIOLATION: conversion before decision!"
                    )
                
                return record
        
        raise ValueError(f"No decision found for visitor {user_identifier}")
    
    def verify_integrity(self):
        """Verifica integridad del audit trail"""
        checks = {
            "chain_integrity": True,
            "timestamp_order": True,
            "sequence_continuity": True
        }
        
        # 1. Chain integrity
        previous_hash = None
        for record in self.audit_records:
            if record["previous_hash"] != previous_hash:
                checks["chain_integrity"] = False
            previous_hash = record["decision_hash"]
        
        # 2. Timestamp order
        for record in self.audit_records:
            if (record["conversion_timestamp"] and 
                record["decision_timestamp"] >= record["conversion_timestamp"]):
                checks["timestamp_order"] = False
        
        # 3. Sequence continuity
        for i, record in enumerate(self.audit_records):
            if record["sequence_number"] != i:
                checks["sequence_continuity"] = False
        
        return {
            "is_valid": all(checks.values()),
            "checks": checks,
            "total_records": len(self.audit_records)
        }
    
    def export_audit_trail(self, filename: str):
        """Exporta audit trail a archivo JSON"""
        integrity = self.verify_integrity()
        
        export_data = {
            "experiment_type": "audit_demo",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_records": len(self.audit_records),
            "integrity_verification": integrity,
            "audit_records": self.audit_records
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename


# ═══════════════════════════════════════════════════════════════════════
# DEMO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

async def run_audit_demo():
    """
    Ejecuta demo completo del sistema de auditoría
    """
    
    print("=" * 70)
    print("  🔍 DEMO: SISTEMA DE AUDITORÍA")
    print("=" * 70)
    print("\nEste demo muestra cómo funcionará el audit trail en v1.1:")
    print("  1. Cada decisión se registra con hash")
    print("  2. Conversiones se auditan")
    print("  3. Integridad verificable")
    print("  4. NO se revelan parámetros del algoritmo")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # PASO 1: Conectar BD
    # ─────────────────────────────────────────────────────────────
    print("[1/8] Conectando a base de datos...")
    
    db = DatabaseManager()
    await db.initialize()
    
    try:
        service = ExperimentService(db)
        audit_service = MockAuditService(service)
        
        # ─────────────────────────────────────────────────────────────
        # PASO 2: Crear usuario de prueba
        # ─────────────────────────────────────────────────────────────
        print("[2/8] Creando usuario de prueba...")
        
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('audit_demo@test.com', 'test', 'Audit Demo User', 'Demo Co')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        
        print(f"  ✅ Usuario creado: {user_id[:8]}...")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 3: Crear experimento
        # ─────────────────────────────────────────────────────────────
        print("[3/8] Creando experimento con 3 variantes...")
        
        result = await service.create_experiment(
            user_id=user_id,
            name="Audit Demo Experiment",
            variants_data=[
                {
                    'name': 'Control',
                    'description': 'Original version',
                    'content': {'text': 'Buy Now'}
                },
                {
                    'name': 'Variant A',
                    'description': 'Green button',
                    'content': {'text': 'Get Started'}
                },
                {
                    'name': 'Variant B',
                    'description': 'Urgency copy',
                    'content': {'text': 'Limited Time Offer'}
                }
            ],
            config={'expected_daily_traffic': 1000}
        )
        
        exp_id = result['experiment_id']
        variant_ids = result['variant_ids']
        
        print(f"  ✅ Experimento creado: {exp_id[:8]}...")
        print(f"  ✅ {len(variant_ids)} variantes creadas")
        
        # Activar
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        await exp_repo.update_status(exp_id, 'active', user_id)
        
        print("  ✅ Experimento activado")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 4: Simular tráfico CON AUDITORÍA
        # ─────────────────────────────────────────────────────────────
        print("[4/8] Simulando 100 visitantes CON auditoría...")
        print("  Cada decisión se registra en audit trail")
        
        allocation_counts = {vid: 0 for vid in variant_ids}
        
        for i in range(100):
            visitor_id = f"audit_visitor_{i}"
            
            # Asignar CON auditoría
            assignment, audit_record = await audit_service.allocate_with_audit(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            
            allocation_counts[assignment['variant_id']] += 1
            
            if (i + 1) % 25 == 0:
                print(f"  {i+1}/100 visitantes procesados + auditados")
        
        print("  ✅ 100 visitantes asignados")
        print("  ✅ 100 decisiones en audit trail")
        
        # Mostrar distribución
        print("\n  Distribución inicial:")
        for i, vid in enumerate(variant_ids):
            count = allocation_counts[vid]
            pct = (count / 100) * 100
            bar = "█" * int(pct / 5)
            print(f"    Variant {i}: {count:>3} ({pct:>5.1f}%) {bar}")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 5: Simular conversiones
        # ─────────────────────────────────────────────────────────────
        print("\n[5/8] Simulando conversiones en Variant B...")
        print("  Conversiones también se auditan")
        
        # Dar 20 conversiones a Variant B
        conversions = 0
        attempts = 0
        
        while conversions < 20 and attempts < 200:
            visitor_id = f"converting_visitor_{attempts}"
            
            # Asignar
            assignment, audit_record = await audit_service.allocate_with_audit(
                experiment_id=exp_id,
                user_identifier=visitor_id
            )
            
            # Si es Variant B, convertir
            if assignment['variant_id'] == variant_ids[2]:
                await audit_service.record_conversion_with_audit(
                    experiment_id=exp_id,
                    user_identifier=visitor_id,
                    value=1.0
                )
                conversions += 1
            
            attempts += 1
        
        print(f"  ✅ {conversions} conversiones registradas + auditadas")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 6: Verificar integridad
        # ─────────────────────────────────────────────────────────────
        print("\n[6/8] Verificando integridad del audit trail...")
        
        integrity = audit_service.verify_integrity()
        
        print("\n  Verificación de integridad:")
        for check, passed in integrity['checks'].items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check}: {'PASSED' if passed else 'FAILED'}")
        
        if integrity['is_valid']:
            print(f"\n  ✅ Audit trail VÁLIDO ({integrity['total_records']} registros)")
        else:
            print("\n  ⚠️  Problemas de integridad detectados")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 7: Exportar audit trail
        # ─────────────────────────────────────────────────────────────
        print("\n[7/8] Exportando audit trail...")
        
        export_file = "audit_trail_export.json"
        audit_service.export_audit_trail(export_file)
        
        print(f"  ✅ Audit trail exportado: {export_file}")
        
        # Mostrar ejemplo
        if audit_service.audit_records:
            sample = audit_service.audit_records[0]
            print("\n  Ejemplo de registro:")
            print(f"    ✅ visitor_id: {sample['visitor_id']}")
            print(f"    ✅ variant_id: {sample['variant_id'][:8]}...")
            print(f"    ✅ decision_timestamp: {sample['decision_timestamp']}")
            print(f"    ✅ decision_hash: {sample['decision_hash'][:16]}...")
            print(f"    ❌ (NO hay alpha, beta, ni probabilidades)")
        
        # ─────────────────────────────────────────────────────────────
        # PASO 8: Demostrar transparencia
        # ─────────────────────────────────────────────────────────────
        print("\n[8/8] Demostrando transparencia del sistema...")
        
        print("\n  ✅ LO QUE EL CLIENTE PUEDE VER (Audit Trail):")
        print("    • Cada decisión de asignación")
        print("    • Timestamp exacto")
        print("    • Qué variante se eligió")
        print("    • Si hubo conversión")
        print("    • Hash chain para verificar integridad")
        
        print("\n  ❌ LO QUE EL CLIENTE NO VE (Propiedad Intelectual):")
        print("    • Parámetros internos de optimización adaptativa")
        print("    • Probabilidades calculadas")
        print("    • Lógica interna del algoritmo")
        print("    • Razón específica de por qué se eligió cada variante")
        
        print("\n  💡 Esto permite:")
        print("    ✅ Cliente puede auditar que no hay trampa")
        print("    ✅ Cliente puede exportar prueba de fairness")
        print("    ✅ Samplit protege su IP")
        print("    ✅ Competencia NO puede copiar el algoritmo")
        
        # ─────────────────────────────────────────────────────────────
        # Cleanup
        # ─────────────────────────────────────────────────────────────
        print("\n" + "-" * 70)
        print("🧹 Limpiando datos de prueba...")
        
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM experiments WHERE id = $1", exp_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        
        print("  ✅ Limpieza completada")
        
        # ─────────────────────────────────────────────────────────────
        # Resultado Final
        # ─────────────────────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("  ✅ DEMO COMPLETADO")
        print("=" * 70)
        print("\nResultados:")
        print(f"  • {integrity['total_records']} decisiones auditadas")
        print(f"  • {conversions} conversiones registradas")
        print(f"  • Integridad: {'✅ VÁLIDA' if integrity['is_valid'] else '❌ INVÁLIDA'}")
        print(f"  • Audit trail exportado: {export_file}")
        
        print("\n⚠️  NOTA: Este fue un DEMO usando MockAuditService")
        print("    La implementación completa estará en v1.1 (Q1 2026)")
        print("    con tabla algorithm_audit_trail en base de datos.")
        print()
        
    except Exception as e:
        print(f"\n❌ Error durante demo: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.close()


def main():
    """Entry point"""
    import asyncio
    
    try:
        asyncio.run(run_audit_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
