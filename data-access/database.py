# data-access/database.py

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
        # ✅ FIXED: Removed server_settings - not supported by asyncpg
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60,
            ssl='require' if 'supabase.co' in self.database_url else None
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
            
                counts = await conn.fetch("""
                    SELECT 
                        (SELECT COUNT(*) FROM experiments) as experiments,
                        (SELECT COUNT(*) FROM element_variants) as variants,
                        (SELECT COUNT(*) FROM assignments) as assignments,
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

    # ========================================================================
    # ✅ FIXED: Email/Notification Methods con NotImplementedError
    # ========================================================================

    async def record_email_performance(
        self, 
        variant_id: str, 
        action: str, 
        reward: float, 
        context: Dict
    ):
        """
        Record email performance
        
        ⚠️ NOT IMPLEMENTED - Email experiments en roadmap v1.1
        
        Esta funcionalidad está planificada para una versión futura.
        Requiere:
        - Schema adicional para email campaigns
        - Integration con email service providers (SendGrid, Mailchimp, etc)
        - Tracking de opens/clicks/conversions
        
        Args:
            variant_id: Variant ID
            action: 'open' | 'click' | 'convert'
            reward: Reward value (1.0 for success, 0.0 for failure)
            context: Additional context (email_id, campaign_id, etc)
            
        Raises:
            NotImplementedError: Email experiments not available in MVP
            
        Workaround:
            Usa experimentos web estándar para testear landing pages
            que reciben tráfico de email campaigns.
            
        Example:
            # En lugar de testear el email directamente:
            # await db.record_email_performance(variant_id, 'click', 1.0, {...})
            
            # Testea la landing page:
            # 1. Usuario hace click en email → landing page
            # 2. Landing page tiene experimento A/B
            # 3. Trackeas conversión en la landing page
        """
        raise NotImplementedError(
            "❌ Email experiments no disponibles en MVP.\n\n"
            "STATUS: Roadmap v1.1 (Q1 2026)\n\n"
            "ALTERNATIVA:\n"
            "- Usa experimentos web estándar en landing pages\n"
            "- Trackea parámetro UTM en URL (?email_variant=A)\n"
            "- Analiza conversiones por variante de email externamente\n\n"
            "Si necesitas esta feature urgentemente, contacta con soporte:\n"
            "support@samplit.com"
        )

    async def get_notification_variants(self, campaign_id: str) -> List[Dict]:
        """
        Get push notification campaign variants
        
        ⚠️ NOT IMPLEMENTED - Push notification experiments en roadmap v1.1
        
        Esta funcionalidad está planificada para una versión futura.
        Requiere:
        - Schema para notification campaigns
        - Integration con push notification providers (Firebase, OneSignal, etc)
        - Tracking de impressions/clicks/conversions
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List of notification variants (empty - not implemented)
            
        Raises:
            NotImplementedError: Push notification experiments not available in MVP
            
        Workaround:
            Usa deep links con experimentos web:
            1. Push notification con deep link
            2. Deep link abre app/web con experiment
            3. Trackeas conversión en destino
            
        Example:
            # En lugar de testear la notificación directamente:
            # variants = await db.get_notification_variants(campaign_id)
            
            # Testea el destino:
            # 1. Notification → deep link → landing page/screen
            # 2. Landing page/screen tiene experimento A/B
            # 3. Trackeas conversión normal
        """
        raise NotImplementedError(
            "❌ Push notification experiments no disponibles en MVP.\n\n"
            "STATUS: Roadmap v1.1 (Q1 2026)\n\n"
            "ALTERNATIVA:\n"
            "- Usa experimentos web en destinos de notificaciones\n"
            "- Trackea parámetro en deep link (?notification_variant=A)\n"
            "- Analiza conversiones por variante externamente\n\n"
            "INTEGRACIONES PLANIFICADAS:\n"
            "- Firebase Cloud Messaging (FCM)\n"
            "- OneSignal\n"
            "- Apple Push Notification Service (APNS)\n"
            "- Custom webhook integration\n\n"
            "Si necesitas esta feature urgentemente, contacta con soporte:\n"
            "support@samplit.com"
        )


# Global instance
_db_manager: Optional[DatabaseManager] = None

async def get_database() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager
