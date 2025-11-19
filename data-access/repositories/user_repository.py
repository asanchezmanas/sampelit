# data-access/repositories/user_repository.py

from typing import Optional, Dict, Any
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for users"""
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, name, company, created_at FROM users WHERE id = $1",
                id
            )
        return dict(row) if row else None
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, name, company, password_hash, created_at FROM users WHERE email = $1",
                email
            )
        return dict(row) if row else None
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create new user"""
        async with self.db.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                data['email'],
                data['password_hash'],
                data['name'],
                data.get('company')
            )
        return str(user_id)
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update user"""
        update_fields = []
        values = []
        param_num = 1
        
        if 'name' in data:
            update_fields.append(f"name = ${param_num}")
            values.append(data['name'])
            param_num += 1
        
        if 'company' in data:
            update_fields.append(f"company = ${param_num}")
            values.append(data['company'])
            param_num += 1
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = NOW()")
        values.append(id)
        
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = ${param_num}
        """
        
        async with self.db.acquire() as conn:
            result = await conn.execute(query, *values)
        
        return result == 'UPDATE 1'
