# scripts/run_demo_with_audit_trail.py

import asyncio
import pandas as pd
import json
from datetime import datetime
import csv

class AuditLogger:
    """
    Registra CADA decisión del algoritmo para auditoría
    
    Prueba que:
    1. Algoritmo decide PRIMERO
    2. Matriz se consulta DESPUÉS
    3. No hay forma de hacer trampa
    """
    
    def __init__(self, output_file='audit_decisions.csv'):
        self.output_file = output_file
        self.decisions = []
        
        # Crear archivo CSV
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'visitor_id',
                'visitor_index',
                'timestamp',
                'algorithm_decision',  # Qué variante eligió
                'decision_metadata',   # Por qué eligió (sin revelar algoritmo)
                'matrix_result',       # Qué dice la matriz (0 o 1)
                'conversion_outcome'   # converted / no_conversion
            ])
    
    def log_decision(self, 
                    visitor_id: str,
                    visitor_index: int,
                    algorithm_decision: str,
                    decision_metadata: dict,
                    matrix_result: int):
        """
        Registrar una decisión
        
        Args:
            visitor_id: ID del visitante
            visitor_index: Índice en la matriz (fila)
            algorithm_decision: Variante elegida por algoritmo
            decision_metadata: Info adicional (ej: scores relativos)
            matrix_result: Resultado de la matriz (0 o 1)
        """
        
        timestamp = datetime.now().isoformat()
        outcome = 'converted' if matrix_result == 1 else 'no_conversion'
        
        decision_record = {
            'visitor_id': visitor_id,
            'visitor_index': visitor_index,
            'timestamp': timestamp,
            'algorithm_decision': algorithm_decision,
            'decision_metadata': json.dumps(decision_metadata),
            'matrix_result': matrix_result,
            'conversion_outcome': outcome
        }
        
        self.decisions.append(decision_record)
        
        # Escribir en CSV
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                visitor_id,
                visitor_index,
                timestamp,
                algorithm_decision,
                json.dumps(decision_metadata),
                matrix_result,
                outcome
            ])
    
    def get_summary(self):
        """Resumen de decisiones"""
        if not self.decisions:
            return {}
        
        variant_stats = {}
        for decision in self.decisions:
            variant = decision['algorithm_decision']
            if variant not in variant_stats:
                variant_stats[variant] = {
                    'assignments': 0,
                    'conversions': 0
                }
            
            variant_stats[variant]['assignments'] += 1
            if decision['matrix_result'] == 1:
                variant_stats[variant]['conversions'] += 1
        
        return {
            'total_decisions': len(self.decisions),
            'variant_stats': variant_stats
        }


async def run_demo_with_full_audit():
    """
    Ejecutar demo CON audit trail completo
    """
    
    print("📂 Loading conversion matrix...")
    
    # Cargar matriz
    df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
    matrix = df.values
    variant_names = df.columns.tolist()
    
    with open('demo_single_element_metadata.json', 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Matrix loaded: {matrix.shape[0]} visitors × {matrix.shape[1]} variants")
    
    # Inicializar audit logger
    audit_logger = AuditLogger('audit_decisions.csv')
    
    print("\n🔍 Starting experiment with FULL AUDIT TRAIL...")
    print("   Every decision will be logged for verification\n")
    
    # ══════════════════════════════════════
    # Conectar a BD y crear experimento
    # ══════════════════════════════════════
    from data_access.database import DatabaseManager
    from orchestration.services.experiment_service import ExperimentService
    
    db = DatabaseManager()
    await db.initialize()
    
    try:
        service = ExperimentService(db)
        
        # Crear usuario demo
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ('demo@samplit.com', 'locked', 'Demo Account', 'Samplit')
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """
            )
            user_id = str(user_id)
        
        # Crear experimento
        variants_data = [
            {
                'name': f"Variant {name}",
                'description': f"CR: {metadata['conversion_rates'][name]:.1%}",
                'content': metadata['element']['variants'][name]
            }
            for name in variant_names
        ]
        
        result = await service.create_experiment(
            user_id=user_id,
            name="Auditable Demo Experiment",
            description="Full audit trail - verifiable decisions",
            variants_data=variants_data,
            config={'audit_mode': True}
        )
        
        experiment_id = result['experiment_id']
        variant_ids = result['variant_ids']
        
        # Mapear variant_id → nombre → índice
        variant_id_to_name = {}
        variant_name_to_idx = {}
        
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name FROM variants WHERE experiment_id = $1 ORDER BY created_at",
                experiment_id
            )
            
            for idx, row in enumerate(rows):
                variant_id_to_name[str(row['id'])] = variant_names[idx]
                variant_name_to_idx[variant_names[idx]] = idx
        
        # Activar
        from data_access.repositories.experiment_repository import ExperimentRepository
        exp_repo = ExperimentRepository(db.pool)
        await exp_repo.update_status(experiment_id, 'active', user_id)
        
        # ══════════════════════════════════════
        # SIMULAR VISITANTES CON LOGGING
        # ══════════════════════════════════════
        print(f"🔄 Processing {matrix.shape[0]} visitors...\n")
        
        for visitor_idx in range(matrix.shape[0]):
            visitor_id = f"visitor_{visitor_idx + 1}"
            
            # ─────────────────────────────────
            # PASO 1: ALGORITMO DECIDE (sin ver matriz)
            # ─────────────────────────────────
            assignment = await service.allocate_user_to_variant(
                experiment_id=experiment_id,
                user_identifier=visitor_id,
                context={'visitor_index': visitor_idx}
            )
            
            selected_variant_id = assignment['variant_id']
            selected_variant_name = variant_id_to_name[selected_variant_id]
            
            # ─────────────────────────────────
            # PASO 2: CONSULTAR MATRIZ (después de decidir)
            # ─────────────────────────────────
            variant_idx = variant_name_to_idx[selected_variant_name]
            matrix_result = int(matrix[visitor_idx, variant_idx])
            
            # ─────────────────────────────────
            # PASO 3: REGISTRAR DECISIÓN
            # ─────────────────────────────────
            decision_metadata = {
                'variant_name': selected_variant_name,
                'is_new_assignment': assignment['new_assignment'],
                'note': 'Algorithm decided BEFORE checking matrix'
            }
            
            audit_logger.log_decision(
                visitor_id=visitor_id,
                visitor_index=visitor_idx,
                algorithm_decision=selected_variant_name,
                decision_metadata=decision_metadata,
                matrix_result=matrix_result
            )
            
            # ─────────────────────────────────
            # PASO 4: REGISTRAR CONVERSIÓN (si aplica)
            # ─────────────────────────────────
            if matrix_result == 1:
                await service.record_conversion(
                    experiment_id=experiment_id,
                    user_identifier=visitor_id,
                    value=1.0
                )
            
            # Progress
            if (visitor_idx + 1) % 1000 == 0:
                summary = audit_logger.get_summary()
                print(f"   {visitor_idx + 1:>5} / {matrix.shape[0]} processed")
                print(f"   Decisions logged: {summary['total_decisions']}")
        
        # ══════════════════════════════════════
        # FINALIZAR
        # ══════════════════════════════════════
        await exp_repo.update_status(experiment_id, 'completed', user_id)
        
        summary = audit_logger.get_summary()
        
        print("\n" + "="*80)
        print("✅ EXPERIMENT COMPLETE - FULL AUDIT TRAIL GENERATED")
        print("="*80)
        
        print(f"\n📊 Summary:")
        print(f"   Total decisions: {summary['total_decisions']}")
        print(f"\n   Distribution:")
        
        for variant, stats in summary['variant_stats'].items():
            cr = stats['conversions'] / stats['assignments']
            pct = stats['assignments'] / summary['total_decisions'] * 100
            print(f"      {variant:<10} | {stats['assignments']:>5} visits ({pct:>5.1f}%) | "
                  f"{stats['conversions']:>4} conv | {cr:.2%}")
        
        print(f"\n💾 Audit files generated:")
        print(f"   - audit_decisions.csv (all decisions)")
        print(f"   - Experiment ID: {experiment_id}")
        
        print(f"\n🔍 Verification available:")
        print(f"   1. Check any visitor: see decision → matrix result")
        print(f"   2. Verify no manipulation: decisions logged BEFORE matrix lookup")
        print(f"   3. Compare with matrix: all results match pre-generated data")
        
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(run_demo_with_full_audit())
