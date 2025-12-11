# data-access/database.py

"""
✅ FIXED:
- Corrected environment variable names (DATABASE_URL, SUPABASE_SERVICE_KEY)
- Fixed table name consistency (allocations instead of assignments)
- Added proper error handling
"""

import os
import asyncpg
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

class DatabaseManager:
    """
    Supabase/PostgreSQL connection manager
    
    Handles:
    - Connection pooling
    - Service role access (for encrypted state)
    - Row Level Security bypass where needed
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
        # ✅ FIXED: Use correct environment variable names from settings.py
        self.database_url = os.environ.get("DATABASE_URL")
        self.service_role_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL not set in environment")
    
    async def initialize(self):
        """Initialize connection pool"""
        
        # Parse Supabase URL - fix postgres:// to postgresql://
        if "supabase.co" in self.database_url:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace(
                    "postgres://", 
                    "postgresql://", 
                    1
                )
        
        # Create pool
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60,
            ssl='require' if 'supabase.co' in self.database_url else None,
            server_settings={
                # Use service role to bypass RLS for backend operations
                'request.jwt.claims': '{"role":"service_role"}',
            }
        )
        
        print("✅ Database pool initialized")
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("✅ Database pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Connection pool stats
                pool_stats = {
                    'pool_size': self.pool.get_size(),
                    'pool_free': self.pool.get_idle_size(),
                    'pool_used': self.pool.get_size() - self.pool.get_idle_size()
                }
            
                # ✅ FIXED: Use correct table name 'allocations'
                counts = await conn.fetch("""
                    SELECT 
                        (SELECT COUNT(*) FROM experiments) as experiments,
                        (SELECT COUNT(*) FROM element_variants) as variants,
                        (SELECT COUNT(*) FROM allocations) as allocations,
                        (SELECT COUNT(*) FROM users) as users
                """)
            
                return {
                    'pool': pool_stats,
                    'counts': dict(counts[0]) if counts else {}
                }
        except Exception as e:
            return {'error': str(e)}

    async def get_funnel(self, funnel_id: str) -> Optional[Dict[str, Any]]:
        """Get funnel definition"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM funnels WHERE id = $1",
                funnel_id
            )
        return dict(row) if row else None

    async def get_variant_performance(self, variant_id: str, step_id: str = None) -> Dict[str, Any]:
        """Get variant performance data"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    total_allocations as sample_size,
                    conversion_rate as conversion_rate
                FROM element_variants
                WHERE id = $1
            """, variant_id)
        return dict(row) if row else {'sample_size': 0, 'conversion_rate': 0.0}

    async def create_funnel_session(self, session: 'FunnelSession'):
        """Create funnel session"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO funnel_sessions 
                (session_id, user_id, funnel_id, current_step, started_at)
                VALUES ($1, $2, $3, $4, $5)
            """, 
            session.session_id, 
            session.user_id, 
            session.funnel_id, 
            session.current_step,
            session.started_at)

    async def update_funnel_session(self, session: 'FunnelSession', metadata: Dict = None):
        """Update funnel session"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE funnel_sessions
                SET current_step = $1, last_activity_at = NOW()
                WHERE session_id = $2
            """, session.current_step, session.session_id)

    async def record_funnel_conversion(self, session: 'FunnelSession', value: float, metadata: Dict = None):
        """Record funnel conversion"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE funnel_sessions
                SET completed = true, converted = true, completed_at = NOW()
                WHERE session_id = $1
            """, session.session_id)

    async def get_funnel_step_analytics(self, funnel_id: str) -> Dict[str, Any]:
        """Get funnel step analytics"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(*) FILTER (WHERE completed) as conversions,
                    CASE 
                        WHEN COUNT(*) > 0 
                        THEN COUNT(*) FILTER (WHERE completed)::FLOAT / COUNT(*)::FLOAT
                        ELSE 0
                    END as conversion_rate,
                    AVG(current_step) as avg_steps
                FROM funnel_sessions
                WHERE funnel_id = $1
            """, funnel_id)
        
            return dict(rows[0]) if rows else {}

    async def get_email_variants(self, campaign_id: str) -> List[Dict]:
        """Get email campaign variants"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT v.* FROM email_variants v
                JOIN email_elements e ON v.element_id = e.id
                WHERE e.campaign_id = $1
            """, campaign_id)
        return [dict(row) for row in rows]

    async def record_email_performance(self, variant_id: str, action: str, reward: float, context: Dict):
        """Record email performance"""
        # Implementación simplificada
        pass

    async def get_notification_variants(self, campaign_id: str) -> List[Dict]:
        """Get notification variants"""
        # Placeholder - implementar según schema
        return []

# Global instance
_db_manager: Optional[DatabaseManager] = None

async def get_database() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager
