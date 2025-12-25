# data-access/repositories/experiment_repository.py

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
import json
from datetime import datetime, timezone

class ExperimentRepository(BaseRepository):
    """Repository for experiments"""
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create new experiment"""
        async with self.db.acquire() as conn:
            experiment_id = await conn.fetchval(
                """
                INSERT INTO experiments 
                (
                    user_id, name, description, 
                    optimization_strategy, config, 
                    status, url
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                data['user_id'],
                data['name'],
                data.get('description'),
                data.get('optimization_strategy', 'adaptive'),
                json.dumps(data.get('config', {})),
                data.get('status', 'draft'),
                data.get('url')
            )
        return str(experiment_id)
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    id, user_id, name, description, status,
                    optimization_strategy,
                    config, url,
                    created_at, started_at, completed_at, updated_at
                FROM experiments 
                WHERE id = $1
                """,
                id
            )
        
        if not row:
            return None
        
        experiment = dict(row)
        
        # Parse JSON fields
        if experiment.get('config'):
            if isinstance(experiment['config'], str):
                experiment['config'] = json.loads(experiment['config'])
        
        return experiment
    
    async def find_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all experiments for user"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    e.id, e.name, e.description, e.status, e.optimization_strategy,
                    e.created_at, e.started_at, e.target_url,
                    COUNT(DISTINCT v.id) as variant_count,
                    COALESCE(SUM(v.total_allocations), 0) as total_users,
                    CASE 
                        WHEN COALESCE(SUM(v.total_allocations), 0) > 0 
                        THEN COALESCE(SUM(v.total_conversions), 0)::FLOAT / 
                             COALESCE(SUM(v.total_allocations), 1)::FLOAT
                        ELSE 0
                    END as conversion_rate
                FROM experiments e
                LEFT JOIN experiment_elements ee ON e.id = ee.experiment_id
                LEFT JOIN element_variants v ON ee.id = v.element_id
                WHERE e.user_id = $1
                GROUP BY e.id
                ORDER BY e.created_at DESC
                """,
                user_id
            )
        
        return [dict(row) for row in rows]
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update experiment"""
        async with self.db.acquire() as conn:
            # Build dynamic update query
            update_fields = []
            values = []
            param_num = 1
            
            if 'name' in data:
                update_fields.append(f"name = ${param_num}")
                values.append(data['name'])
                param_num += 1
            
            if 'description' in data:
                update_fields.append(f"description = ${param_num}")
                values.append(data['description'])
                param_num += 1
            
            if 'config' in data:
                update_fields.append(f"config = ${param_num}")
                values.append(json.dumps(data['config']))
                param_num += 1
            
            if 'status' in data:
                update_fields.append(f"status = ${param_num}")
                values.append(data['status'])
                param_num += 1
            
            if not update_fields:
                return False
            
            # Always update updated_at
            update_fields.append("updated_at = NOW()")
            
            # Add id as last parameter
            values.append(id)
            
            query = f"""
                UPDATE experiments 
                SET {', '.join(update_fields)}
                WHERE id = ${param_num}
            """
            
            result = await conn.execute(query, *values)
            
        return result == 'UPDATE 1'
    
    async def update_status(
        self, 
        id: str, 
        status: str, 
        user_id: str
    ) -> bool:
        """Update experiment status"""
        async with self.db.acquire() as conn:
            # Set started_at if going to active
            if status == 'active':
                result = await conn.execute(
                    """
                    UPDATE experiments 
                    SET 
                        status = $1,
                        started_at = COALESCE(started_at, NOW()),
                        updated_at = NOW()
                    WHERE id = $2 AND user_id = $3
                    """,
                    status, id, user_id
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE experiments 
                    SET status = $1, updated_at = NOW()
                    WHERE id = $2 AND user_id = $3
                    """,
                    status, id, user_id
                )
        
        return result == 'UPDATE 1'
    
    async def delete(self, id: str, user_id: str) -> bool:
        """Delete experiment (soft delete - archive)"""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE experiments 
                SET status = 'archived', updated_at = NOW()
                WHERE id = $1 AND user_id = $2
                """,
                id, user_id
            )
        
        return result == 'UPDATE 1'
    
    async def get_active_count(self, user_id: str) -> int:
        """Get count of active experiments"""
        async with self.db.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM experiments 
                WHERE user_id = $1 AND status = 'active'
                """,
                user_id
            )
        
        return count or 0
