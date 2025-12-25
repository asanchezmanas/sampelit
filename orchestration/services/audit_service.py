"""
AUDIT SERVICE - Sistema de Auditoría en Tiempo Real

Principio: "Decision-First Logging"
El algoritmo registra su decisión ANTES de ver el resultado.
Esto prueba que no hace trampa.

Qué NO se revela:
- Parámetros Thompson Sampling (alpha, beta)
- Probabilidades internas
- Lógica de decisión
- Estado interno del algoritmo

Qué SÍ se revela:
- Decisión tomada (qué variante)
- Timestamp de decisión
- Resultado observado (después)
- Prueba criptográfica de integridad
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID

from data_access.database import DatabaseManager


class AuditService:
    """
    Servicio de auditoría que registra todas las decisiones del algoritmo
    sin revelar su funcionamiento interno.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.algorithm_version = "adaptive-thompson-v3.0-enterprise"  # Versión profesional
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO DE DECISIÓN (ANTES de ver el resultado)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def log_decision(
        self,
        experiment_id: UUID,
        visitor_id: str,
        selected_variant_id: UUID,
        assignment_id: UUID,
        segment_key: str = 'default',
        context: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Registra la decisión del algoritmo INMEDIATAMENTE después de tomarla.
        
        CRÍTICO: Este método se llama ANTES de que el usuario vea la variante,
        por lo tanto ANTES de que sepamos si convertirá.
        
        Args:
            experiment_id: ID del experimento
            visitor_id: ID del visitante
            selected_variant_id: Variante elegida por el algoritmo
            assignment_id: ID del assignment (link a tabla principal)
            context: Contexto de la request (se hashea, NO se guarda completo)
        
        Returns:
            UUID del registro de auditoría creado
        """
        async with self.db.pool.acquire() as conn:
            # Obtener el último hash y sequence number
            previous_hash, sequence_number = await self._get_chain_state(
                conn, experiment_id
            )
            
            # Timestamp de decisión
            decision_timestamp = datetime.now(timezone.utc)
            
            # Hash del contexto (NO el contexto completo)
            context_hash = None
            user_agent_hash = None
            if context:
                context_hash = self._hash_dict(context)
                if 'user_agent' in context:
                    user_agent_hash = self._hash_string(context['user_agent'])
            
            # Calcular hash de este registro
            decision_hash = self._calculate_decision_hash(
                visitor_id=visitor_id,
                variant_id=selected_variant_id,
                segment_key=segment_key,
                timestamp=decision_timestamp,
                previous_hash=previous_hash,
                sequence_number=sequence_number
            )
            
            # Insertar registro
            audit_id = await conn.fetchval("""
                INSERT INTO algorithm_audit_trail (
                    experiment_id,
                    visitor_id,
                    selected_variant_id,
                    decision_timestamp,
                    decision_hash,
                    previous_hash,
                    sequence_number,
                    context_hash,
                    user_agent_hash,
                    assignment_id,
                    segment_key,
                    algorithm_version
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """, 
                experiment_id,
                visitor_id,
                selected_variant_id,
                decision_timestamp,
                decision_hash,
                previous_hash,
                sequence_number,
                context_hash,
                user_agent_hash,
                assignment_id,
                segment_key,
                self.algorithm_version
            )
            
            return audit_id
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO DE CONVERSIÓN (DESPUÉS de la decisión)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def log_conversion(
        self,
        assignment_id: UUID,
        conversion_value: Optional[float] = None
    ) -> bool:
        """
        Actualiza el registro de auditoría con el resultado de conversión.
        
        CRÍTICO: Este método se llama DESPUÉS de que el usuario ha convertido.
        El timestamp de conversión DEBE ser > decision_timestamp.
        
        Args:
            assignment_id: ID del assignment
            conversion_value: Valor de la conversión (opcional)
        
        Returns:
            True si se actualizó correctamente
        """
        async with self.db.pool.acquire() as conn:
            conversion_timestamp = datetime.now(timezone.utc)
            
            result = await conn.fetchrow("""
                UPDATE algorithm_audit_trail
                SET 
                    conversion_observed = TRUE,
                    conversion_timestamp = $1,
                    conversion_value = $2
                WHERE assignment_id = $3
                AND (conversion_observed IS NULL OR conversion_observed = FALSE)
                RETURNING id, decision_timestamp
            """, conversion_timestamp, conversion_value, assignment_id)
            
            if not result:
                return False
            
            audit_id = result['id']
            decision_timestamp = result['decision_timestamp']
            
            # VERIFICACIÓN: decision_timestamp < conversion_timestamp
            if decision_timestamp >= conversion_timestamp:
                raise ValueError(
                    f"INTEGRITY VIOLATION: Decision timestamp "
                    f"({decision_timestamp}) is not before conversion timestamp "
                    f"({conversion_timestamp})"
                )
            
            return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONSULTAS PÚBLICAS (para clientes)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_audit_trail(
        self,
        experiment_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el audit trail público de un experimento.
        
        NO incluye:
        - Parámetros internos del algoritmo
        - Hashes de contexto (privacidad)
        - Assignment IDs (internos)
        
        SÍ incluye:
        - Decisiones tomadas
        - Timestamps
        - Conversiones observadas
        - Pruebas de integridad
        """
        async with self.db.pool.acquire() as conn:
            query = """
                SELECT 
                    id,
                    visitor_id,
                    selected_variant_id,
                    segment_key,
                    decision_timestamp,
                    conversion_observed,
                    conversion_timestamp,
                    conversion_value,
                    decision_hash,
                    sequence_number,
                    algorithm_version,
                    EXTRACT(EPOCH FROM (
                        conversion_timestamp - decision_timestamp
                    )) as decision_to_conversion_seconds
                FROM algorithm_audit_trail
                WHERE experiment_id = $1
            """
            
            params = [experiment_id]
            i = 2
            
            if start_date:
                query += f" AND decision_timestamp >= ${i}"
                params.append(start_date)
                i += 1
            
            if end_date:
                query += f" AND decision_timestamp <= ${i}"
                params.append(end_date)
                i += 1
            
            query += f" ORDER BY sequence_number DESC LIMIT ${i}"
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                record = dict(row)
                # Convertir UUIDs a strings para JSON
                record['id'] = str(record['id'])
                record['selected_variant_id'] = str(record['selected_variant_id'])
                results.append(record)
            
            return results
    
    async def get_audit_stats(self, experiment_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas de auditoría para un experimento.
        
        Incluye:
        - Total de decisiones
        - Tasa de conversión
        - Tiempo promedio a conversión
        - Integridad de la cadena de hashes
        """
        async with self.db.pool.acquire() as conn:
            # Stats básicas si no queremos usar el stored procedure
            row = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(*) FILTER (WHERE conversion_observed) as conversions,
                    COUNT(*) FILTER (WHERE NOT conversion_observed) as pending_conversions,
                    AVG(EXTRACT(EPOCH FROM (conversion_timestamp - decision_timestamp))) FILTER (WHERE conversion_observed) as avg_time_to_conversion
                FROM algorithm_audit_trail
                WHERE experiment_id = $1
            """, experiment_id)
            
            return dict(row) if row else {}
    
    async def verify_chain_integrity(
        self,
        experiment_id: UUID,
        start_sequence: int = 1,
        end_sequence: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verifica la integridad de la cadena de hashes.
        
        Si alguien modifica un registro histórico, todos los hashes
        subsecuentes dejarán de coincidir.
        
        Returns:
            {
                'is_valid': bool,
                'total_checked': int,
                'invalid_records': [...]
            }
        """
        async with self.db.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT * FROM verify_audit_chain($1, $2, $3)
            """, experiment_id, start_sequence, end_sequence)
            
            invalid_records = [
                {
                    'sequence_number': row['sequence_number'],
                    'expected_hash': row['expected_hash'],
                    'actual_hash': row['actual_hash']
                }
                for row in results
                if not row['is_valid']
            ]
            
            return {
                'is_valid': len(invalid_records) == 0,
                'total_checked': len(results),
                'invalid_records': invalid_records
            }
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPORTACIÓN (para auditoría externa)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def export_audit_trail_csv(
        self,
        experiment_id: UUID,
        filepath: str
    ) -> int:
        """
        Exporta el audit trail a CSV para auditoría externa.
        
        El auditor puede verificar:
        1. Todas las decisiones están registradas
        2. decision_timestamp < conversion_timestamp (siempre)
        3. Hash chain es válido
        4. No hay registros duplicados o faltantes (sequence_number continuo)
        """
        import csv
        
        records = await self.get_audit_trail(
            experiment_id=experiment_id,
            limit=1000000  # Todos los registros
        )
        
        if not records:
            return 0
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        
        return len(records)
    
    # ═══════════════════════════════════════════════════════════════════════
    # UTILIDADES PRIVADAS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_chain_state(self, conn, experiment_id: UUID) -> tuple:
        """
        Obtiene el estado actual de la cadena de hashes.
        
        Returns:
            (previous_hash, next_sequence_number)
        """
        row = await conn.fetchrow("""
            SELECT decision_hash, sequence_number
            FROM algorithm_audit_trail
            WHERE experiment_id = $1
            ORDER BY sequence_number DESC
            LIMIT 1
        """, experiment_id)
        
        if row:
            return row['decision_hash'], row['sequence_number'] + 1
        else:
            return None, 1  # Primera entrada
    
    def _calculate_decision_hash(
        self,
        visitor_id: str,
        variant_id: UUID,
        segment_key: str,
        timestamp: datetime,
        previous_hash: Optional[str],
        sequence_number: int
    ) -> str:
        """
        Calcula el hash SHA256 de un registro de decisión.
        
        Incluye:
        - visitor_id
        - variant_id
        - timestamp (ISO format)
        - previous_hash (si existe)
        - sequence_number
        
        Esto crea una "blockchain" donde cada registro depende del anterior.
        """
        data = {
            'visitor_id': visitor_id,
            'variant_id': str(variant_id),
            'segment_key': segment_key,
            'timestamp': timestamp.isoformat(),
            'previous_hash': previous_hash or '',
            'sequence_number': sequence_number
        }
        
        # Ordenar keys para consistencia
        data_str = json.dumps(data, sort_keys=True)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _hash_dict(self, data: Dict[str, Any]) -> str:
        """Hash de un diccionario (para context_hash)."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _hash_string(self, s: str) -> str:
        """Hash de un string (para user_agent_hash, etc)."""
        return hashlib.sha256(s.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRACIÓN CON ExperimentService
# ═══════════════════════════════════════════════════════════════════════════

# Auditoría automática integrada en ExperimentService.
# No se requiere AuditableExperimentService.


# ═══════════════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    """
    Ejemplo de cómo usar el sistema de auditoría.
    """
    
    db = DatabaseManager()
    service = AuditableExperimentService(db)
    
    experiment_id = UUID('...')  # Tu experimento
    
    # 1. Usuario visita el sitio
    assignment = service.allocate_user(
        experiment_id=experiment_id,
        visitor_id='user_123',
        context={
            'ip': '192.168.1.1',
            'user_agent': 'Mozilla/5.0...',
            'referer': 'https://google.com'
        }
    )
    
    # ✅ En este momento ya se registró la decisión
    # El audit trail contiene:
    # - Qué variante eligió el algoritmo
    # - Timestamp exacto de la decisión
    # - Hash de integridad
    
    print(f"Usuario asignado a variante: {assignment.variant_id}")
    
    # 2. Usuario convierte (más tarde)
    service.record_conversion(
        assignment_id=assignment.id,
        conversion_value=49.99
    )
    
    # ✅ Ahora el audit trail también contiene:
    # - Que el usuario convirtió
    # - Timestamp de la conversión
    # - Valor de la conversión
    
    # 3. Auditoría
    stats = service.get_audit_stats(experiment_id)
    print(f"Estadísticas: {stats}")
    
    integrity = service.verify_integrity(experiment_id)
    print(f"Integridad: {integrity['is_valid']}")
    
    # 4. Exportar para auditor externo
    service.audit.export_audit_trail_csv(
        experiment_id=experiment_id,
        filepath='audit_trail.csv'
    )
    
    print("✅ Audit trail exportado a audit_trail.csv")
