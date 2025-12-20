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
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from database.connection import DatabaseManager
from models.experiments import Assignment


class AuditService:
    """
    Servicio de auditoría que registra todas las decisiones del algoritmo
    sin revelar su funcionamiento interno.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.algorithm_version = "adaptive-thompson-v2.1"  # Versión pública
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO DE DECISIÓN (ANTES de ver el resultado)
    # ═══════════════════════════════════════════════════════════════════════
    
    def log_decision(
        self,
        experiment_id: UUID,
        visitor_id: str,
        selected_variant_id: UUID,
        assignment_id: UUID,
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
        with self.db.get_cursor() as cursor:
            # Obtener el último hash y sequence number
            previous_hash, sequence_number = self._get_chain_state(
                cursor, experiment_id
            )
            
            # Timestamp de decisión
            decision_timestamp = datetime.utcnow()
            
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
                timestamp=decision_timestamp,
                previous_hash=previous_hash,
                sequence_number=sequence_number
            )
            
            # Insertar registro
            cursor.execute("""
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
                    algorithm_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                str(experiment_id),
                visitor_id,
                str(selected_variant_id),
                decision_timestamp,
                decision_hash,
                previous_hash,
                sequence_number,
                context_hash,
                user_agent_hash,
                str(assignment_id),
                self.algorithm_version
            ))
            
            audit_id = cursor.fetchone()[0]
            
            return UUID(audit_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO DE CONVERSIÓN (DESPUÉS de la decisión)
    # ═══════════════════════════════════════════════════════════════════════
    
    def log_conversion(
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
        with self.db.get_cursor() as cursor:
            conversion_timestamp = datetime.utcnow()
            
            cursor.execute("""
                UPDATE algorithm_audit_trail
                SET 
                    conversion_observed = TRUE,
                    conversion_timestamp = %s,
                    conversion_value = %s
                WHERE assignment_id = %s
                AND conversion_observed IS NULL  -- Solo primera conversión
                RETURNING id, decision_timestamp
            """, (
                conversion_timestamp,
                conversion_value,
                str(assignment_id)
            ))
            
            result = cursor.fetchone()
            
            if not result:
                return False
            
            audit_id, decision_timestamp = result
            
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
    
    def get_audit_trail(
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
        with self.db.get_cursor() as cursor:
            query = """
                SELECT 
                    id,
                    visitor_id,
                    selected_variant_id,
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
                WHERE experiment_id = %s
            """
            
            params = [str(experiment_id)]
            
            if start_date:
                query += " AND decision_timestamp >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND decision_timestamp <= %s"
                params.append(end_date)
            
            query += " ORDER BY sequence_number DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                # Convertir UUIDs a strings para JSON
                record['id'] = str(record['id'])
                record['selected_variant_id'] = str(record['selected_variant_id'])
                results.append(record)
            
            return results
    
    def get_audit_stats(self, experiment_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas de auditoría para un experimento.
        
        Incluye:
        - Total de decisiones
        - Tasa de conversión
        - Tiempo promedio a conversión
        - Integridad de la cadena de hashes
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT get_audit_stats(%s)",
                (str(experiment_id),)
            )
            
            stats = cursor.fetchone()[0]
            return stats
    
    def verify_chain_integrity(
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
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM verify_audit_chain(%s, %s, %s)
            """, (
                str(experiment_id),
                start_sequence,
                end_sequence
            ))
            
            results = cursor.fetchall()
            invalid_records = [
                {
                    'sequence_number': row[0],
                    'expected_hash': row[2],
                    'actual_hash': row[3]
                }
                for row in results
                if not row[1]  # is_valid = False
            ]
            
            return {
                'is_valid': len(invalid_records) == 0,
                'total_checked': len(results),
                'invalid_records': invalid_records
            }
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXPORTACIÓN (para auditoría externa)
    # ═══════════════════════════════════════════════════════════════════════
    
    def export_audit_trail_csv(
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
        
        records = self.get_audit_trail(
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
    
    def _get_chain_state(self, cursor, experiment_id: UUID) -> tuple:
        """
        Obtiene el estado actual de la cadena de hashes.
        
        Returns:
            (previous_hash, next_sequence_number)
        """
        cursor.execute("""
            SELECT decision_hash, sequence_number
            FROM algorithm_audit_trail
            WHERE experiment_id = %s
            ORDER BY sequence_number DESC
            LIMIT 1
        """, (str(experiment_id),))
        
        result = cursor.fetchone()
        
        if result:
            return result[0], result[1] + 1
        else:
            return None, 1  # Primera entrada
    
    def _calculate_decision_hash(
        self,
        visitor_id: str,
        variant_id: UUID,
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

class AuditableExperimentService:
    """
    Wrapper del ExperimentService que agrega auditoría automática.
    
    Uso:
        # En lugar de:
        service = ExperimentService(db_manager)
        
        # Usar:
        service = AuditableExperimentService(db_manager)
        
    Todas las operaciones se auditan automáticamente.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        from services.experiment_service import ExperimentService
        
        self.service = ExperimentService(db_manager)
        self.audit = AuditService(db_manager)
        self.db = db_manager
    
    def allocate_user(
        self,
        experiment_id: UUID,
        visitor_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Assignment:
        """
        Asigna usuario a variante CON auditoría.
        
        Flujo:
        1. Algoritmo decide variante
        2. Se registra la decisión (ANTES de que el usuario la vea)
        3. Se retorna el assignment
        """
        # El algoritmo toma la decisión
        assignment = self.service.allocate_user(
            experiment_id=experiment_id,
            visitor_id=visitor_id
        )
        
        # Registramos la decisión INMEDIATAMENTE
        # (antes de que el usuario vea la variante)
        self.audit.log_decision(
            experiment_id=experiment_id,
            visitor_id=visitor_id,
            selected_variant_id=assignment.variant_id,
            assignment_id=assignment.id,
            context=context
        )
        
        return assignment
    
    def record_conversion(
        self,
        assignment_id: UUID,
        conversion_value: Optional[float] = None
    ) -> bool:
        """
        Registra conversión CON auditoría.
        
        Flujo:
        1. Se registra conversión en sistema principal
        2. Se actualiza audit trail con el resultado observado
        """
        # Registrar en sistema principal
        success = self.service.record_conversion(
            assignment_id=assignment_id,
            conversion_value=conversion_value
        )
        
        if success:
            # Actualizar audit trail
            self.audit.log_conversion(
                assignment_id=assignment_id,
                conversion_value=conversion_value
            )
        
        return success
    
    def get_results(self, experiment_id: UUID) -> Dict[str, Any]:
        """Obtiene resultados del experimento."""
        return self.service.get_results(experiment_id)
    
    def get_audit_trail(self, experiment_id: UUID) -> List[Dict[str, Any]]:
        """Obtiene audit trail del experimento."""
        return self.audit.get_audit_trail(experiment_id)
    
    def get_audit_stats(self, experiment_id: UUID) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría."""
        return self.audit.get_audit_stats(experiment_id)
    
    def verify_integrity(self, experiment_id: UUID) -> Dict[str, Any]:
        """Verifica integridad de la cadena de auditoría."""
        return self.audit.verify_chain_integrity(experiment_id)


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
