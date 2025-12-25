# data-access/repositories/assignment_repository.py
# RENAMED: allocation_repository.py -> assignment_repository.py
# REASON: Table is named 'assignments', should match repository name

from typing import Optional, Dict, Any, List
from .base_repository import BaseRepository
import json
from datetime import datetime, timezone

class AssignmentRepository(BaseRepository):
    """
    Repository for user assignments
    
    Manages the assignments table which tracks which variant
    each user was assigned to in an experiment.
    """
    
    async def get_assignment(
        self, 
        experiment_id: str, 
        user_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing assignment for user"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, experiment_id, variant_id, variant_assignments, user_id as user_identifier,
                    session_id, context, assigned_at, 
                    converted_at, conversion_value, metadata
                FROM assignments 
                WHERE experiment_id = $1 AND user_id = $2
                """,
                experiment_id, user_identifier
            )
        
        if not row:
            return None
        
        assignment = dict(row)
        
        # Parse JSON fields
        if assignment.get('context'):
            if isinstance(assignment['context'], str):
                assignment['context'] = json.loads(assignment['context'])
        
        if assignment.get('metadata'):
            if isinstance(assignment['metadata'], str):
                assignment['metadata'] = json.loads(assignment['metadata'])
        
        return assignment
    
    async def create_assignment(
        self,
        experiment_id: str,
        variant_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new assignment"""
        async with self.db.acquire() as conn:
            assignment_id = await conn.fetchval(
                """
                INSERT INTO assignments 
                (experiment_id, variant_id, user_id, session_id, context)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                experiment_id,
                variant_id,
                user_identifier,
                session_id,
                json.dumps(context or {})
            )
        
        return str(assignment_id)
    
    async def record_conversion(
        self,
        assignment_id: str,
        conversion_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record conversion for assignment"""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE assignments 
                SET 
                    converted_at = NOW(),
                    conversion_value = $2,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                WHERE id = $1 AND converted_at IS NULL
                """,
                assignment_id,
                conversion_value,
                json.dumps(metadata or {})
            )
        
        return result == 'UPDATE 1'
    
    async def get_experiment_assignments(
        self,
        experiment_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get recent assignments for experiment"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    a.id, a.variant_id, a.user_id as user_identifier,
                    a.assigned_at, a.converted_at, a.conversion_value,
                    ev.name as variant_name
                FROM assignments a
                LEFT JOIN element_variants ev ON a.variant_id = ev.id
                WHERE a.experiment_id = $1
                ORDER BY a.assigned_at DESC
                LIMIT $2 OFFSET $3
                """,
                experiment_id, limit, offset
            )
        
        return [dict(row) for row in rows]

    
    async def get_conversion_timeline(
        self,
        experiment_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get conversion timeline for last N hours"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('hour', assigned_at) as hour,
                    COUNT(*) as assignments,
                    COUNT(converted_at) as conversions,
                    CASE 
                        WHEN COUNT(*) > 0 
                        THEN COUNT(converted_at)::FLOAT / COUNT(*)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM assignments
                WHERE 
                    experiment_id = $1 
                    AND assigned_at >= NOW() - INTERVAL '1 hour' * $2
                GROUP BY DATE_TRUNC('hour', assigned_at)
                ORDER BY hour DESC
                """,
                experiment_id, hours
            )
        
        return [dict(row) for row in rows]
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get assignment by ID"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM assignments WHERE id = $1",
                id
            )
        
        return dict(row) if row else None
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Generic create (for base class)"""
        return await self.create_assignment(
            experiment_id=data['experiment_id'],
            variant_id=data['variant_id'],
            user_identifier=data['user_identifier'],
            session_id=data.get('session_id'),
            context=data.get('context')
        )
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update assignment"""
        if 'conversion_value' in data:
            return await self.record_conversion(
                assignment_id=id,
                conversion_value=data['conversion_value'],
                metadata=data.get('metadata')
            )
        return False
