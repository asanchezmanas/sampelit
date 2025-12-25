# data-access/repositories/funnel_repository.py
"""
Funnel Repository - CRUD operations for funnel system.
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
import json
from datetime import datetime, timezone


class FunnelRepository(BaseRepository):
    """
    Repository for Funnel operations.
    Manages funnels, nodes, edges, and sessions.
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FUNNEL CRUD
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def create_funnel(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        conversion_type: str = "url",
        conversion_config: Optional[Dict[str, Any]] = None,
        session_timeout_hours: int = 168
    ) -> str:
        """Create a new funnel."""
        async with self.db.acquire() as conn:
            funnel_id = await conn.fetchval(
                """
                INSERT INTO funnels (
                    user_id, name, description, conversion_type, 
                    conversion_config, session_timeout_hours
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                user_id,
                name,
                description,
                conversion_type,
                json.dumps(conversion_config or {}),
                session_timeout_hours
            )
        return str(funnel_id)
    
    async def get_funnel(self, funnel_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get funnel by ID (with ownership check)."""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM funnels 
                WHERE id = $1 AND user_id = $2
                """,
                funnel_id, user_id
            )
        return dict(row) if row else None
    
    async def get_funnel_public(self, funnel_id: str) -> Optional[Dict[str, Any]]:
        """Get funnel by ID (no ownership check - for tracker)."""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM funnels WHERE id = $1 AND status = 'active'",
                funnel_id
            )
        return dict(row) if row else None
    
    async def list_funnels(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List funnels for user with stats."""
        async with self.db.acquire() as conn:
            query = """
                SELECT 
                    f.*,
                    (SELECT COUNT(*) FROM funnel_nodes WHERE funnel_id = f.id) as node_count,
                    (SELECT COUNT(*) FROM funnel_sessions WHERE funnel_id = f.id) as total_sessions,
                    (
                        SELECT COUNT(*)::FLOAT / NULLIF(COUNT(*), 0) 
                        FROM funnel_sessions 
                        WHERE funnel_id = f.id AND status = 'converted'
                    ) as conversion_rate
                FROM funnels f
                WHERE f.user_id = $1
            """
            params = [user_id]
            
            if status:
                query += " AND f.status = $2"
                params.append(status)
            
            query += " ORDER BY f.created_at DESC LIMIT $3 OFFSET $4"
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def update_funnel(
        self,
        funnel_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update funnel fields."""
        if not updates:
            return False
        
        # Build dynamic update
        set_clauses = []
        params = [funnel_id, user_id]
        param_idx = 3
        
        for key, value in updates.items():
            if key in ['name', 'description', 'status', 'conversion_type', 'session_timeout_hours']:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
            elif key == 'conversion_config':
                set_clauses.append(f"conversion_config = ${param_idx}")
                params.append(json.dumps(value))
                param_idx += 1
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = NOW()")
        
        # Handle status changes
        if updates.get('status') == 'active':
            set_clauses.append("started_at = COALESCE(started_at, NOW())")
        elif updates.get('status') == 'completed':
            set_clauses.append("completed_at = NOW()")
        
        async with self.db.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE funnels 
                SET {', '.join(set_clauses)}
                WHERE id = $1 AND user_id = $2
                """,
                *params
            )
        
        return result == 'UPDATE 1'
    
    async def delete_funnel(self, funnel_id: str, user_id: str) -> bool:
        """Delete funnel (cascades to nodes, edges, sessions)."""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM funnels WHERE id = $1 AND user_id = $2",
                funnel_id, user_id
            )
        return result == 'DELETE 1'
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NODE CRUD
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def create_node(
        self,
        funnel_id: str,
        name: str,
        node_type: str,
        parent_node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_conversion_node: bool = False,
        is_entry_node: bool = False,
        position_x: int = 0,
        position_y: int = 0
    ) -> str:
        """Create a funnel node."""
        async with self.db.acquire() as conn:
            # Get next order number
            max_order = await conn.fetchval(
                "SELECT COALESCE(MAX(node_order), -1) + 1 FROM funnel_nodes WHERE funnel_id = $1",
                funnel_id
            )
            
            node_id = await conn.fetchval(
                """
                INSERT INTO funnel_nodes (
                    funnel_id, name, node_type, node_order, parent_node_id,
                    config, is_conversion_node, is_entry_node, position_x, position_y
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                funnel_id, name, node_type, max_order, parent_node_id,
                json.dumps(config or {}), is_conversion_node, is_entry_node,
                position_x, position_y
            )
        return str(node_id)
    
    async def get_nodes(self, funnel_id: str) -> List[Dict[str, Any]]:
        """Get all nodes for a funnel."""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM funnel_nodes 
                WHERE funnel_id = $1 
                ORDER BY node_order
                """,
                funnel_id
            )
        return [dict(row) for row in rows]
    
    async def update_node(
        self,
        node_id: str,
        funnel_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a node."""
        if not updates:
            return False
        
        set_clauses = []
        params = [node_id, funnel_id]
        param_idx = 3
        
        for key, value in updates.items():
            if key in ['name', 'node_type', 'parent_node_id', 'is_conversion_node', 
                       'is_entry_node', 'position_x', 'position_y', 'experiment_id']:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
            elif key == 'config':
                set_clauses.append(f"config = ${param_idx}")
                params.append(json.dumps(value))
                param_idx += 1
        
        if not set_clauses:
            return False
        
        async with self.db.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE funnel_nodes 
                SET {', '.join(set_clauses)}
                WHERE id = $1 AND funnel_id = $2
                """,
                *params
            )
        
        return result == 'UPDATE 1'
    
    async def delete_node(self, node_id: str, funnel_id: str) -> bool:
        """Delete a node."""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM funnel_nodes WHERE id = $1 AND funnel_id = $2",
                node_id, funnel_id
            )
        return result == 'DELETE 1'
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EDGE CRUD
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def create_edge(
        self,
        funnel_id: str,
        from_node_id: str,
        to_node_id: str,
        condition_type: str = "always",
        condition_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create an edge between nodes."""
        async with self.db.acquire() as conn:
            edge_id = await conn.fetchval(
                """
                INSERT INTO funnel_edges (
                    funnel_id, from_node_id, to_node_id, 
                    condition_type, condition_config
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                funnel_id, from_node_id, to_node_id,
                condition_type, json.dumps(condition_config or {})
            )
        return str(edge_id)
    
    async def get_edges(self, funnel_id: str) -> List[Dict[str, Any]]:
        """Get all edges for a funnel."""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM funnel_edges WHERE funnel_id = $1",
                funnel_id
            )
        return [dict(row) for row in rows]
    
    async def delete_edge(self, edge_id: str, funnel_id: str) -> bool:
        """Delete an edge."""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM funnel_edges WHERE id = $1 AND funnel_id = $2",
                edge_id, funnel_id
            )
        return result == 'DELETE 1'
    
    async def increment_edge_stats(
        self,
        edge_id: str,
        traversal: bool = True,
        conversion: bool = False
    ):
        """Increment edge traversal/conversion stats."""
        async with self.db.acquire() as conn:
            if conversion:
                await conn.execute(
                    """
                    UPDATE funnel_edges 
                    SET total_traversals = total_traversals + 1,
                        successful_conversions = successful_conversions + 1
                    WHERE id = $1
                    """,
                    edge_id
                )
            elif traversal:
                await conn.execute(
                    """
                    UPDATE funnel_edges 
                    SET total_traversals = total_traversals + 1
                    WHERE id = $1
                    """,
                    edge_id
                )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION TRACKING
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def create_session(
        self,
        funnel_id: str,
        user_identifier: str,
        session_id: Optional[str] = None,
        entry_node_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create or get existing funnel session."""
        async with self.db.acquire() as conn:
            # Check for existing active session
            existing = await conn.fetchval(
                """
                SELECT id FROM funnel_sessions 
                WHERE funnel_id = $1 AND user_identifier = $2 AND status = 'active'
                """,
                funnel_id, user_identifier
            )
            
            if existing:
                return str(existing)
            
            # Create new session
            initial_path = []
            if entry_node_id:
                initial_path = [{"node_id": entry_node_id, "entered_at": datetime.now(timezone.utc).isoformat()}]
            
            session_id = await conn.fetchval(
                """
                INSERT INTO funnel_sessions (
                    funnel_id, user_identifier, session_id, 
                    current_node_id, path, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                funnel_id, user_identifier, session_id,
                entry_node_id, json.dumps(initial_path),
                json.dumps(metadata or {})
            )
        
        return str(session_id)
    
    async def get_session(
        self,
        funnel_id: str,
        user_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get active session for user in funnel."""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM funnel_sessions 
                WHERE funnel_id = $1 AND user_identifier = $2 AND status = 'active'
                """,
                funnel_id, user_identifier
            )
        return dict(row) if row else None
    
    async def update_session_step(
        self,
        session_id: str,
        node_id: str,
        variant_id: Optional[str] = None
    ):
        """Add step to session path."""
        step = {
            "node_id": node_id,
            "entered_at": datetime.now(timezone.utc).isoformat()
        }
        if variant_id:
            step["variant_id"] = variant_id
        
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE funnel_sessions 
                SET 
                    current_node_id = $2,
                    path = path || $3::jsonb,
                    last_activity_at = NOW()
                WHERE id = $1
                """,
                session_id, node_id, json.dumps([step])
            )
    
    async def convert_session(
        self,
        session_id: str,
        conversion_value: float = 1.0
    ) -> bool:
        """Mark session as converted."""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE funnel_sessions 
                SET 
                    status = 'converted',
                    converted_at = NOW(),
                    conversion_value = $2
                WHERE id = $1 AND status = 'active'
                """,
                session_id, conversion_value
            )
        return result == 'UPDATE 1'
    
    async def get_session_path(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the path taken in a session (for reward distribution)."""
        async with self.db.acquire() as conn:
            path = await conn.fetchval(
                "SELECT path FROM funnel_sessions WHERE id = $1",
                session_id
            )
        
        if path:
            if isinstance(path, str):
                return json.loads(path)
            return path
        return []


# For base class compatibility
async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
    """Generic find - not used for funnels."""
    return None

async def create(self, data: Dict[str, Any]) -> str:
    """Generic create - use specific methods."""
    raise NotImplementedError("Use create_funnel, create_node, etc.")

async def update(self, id: str, data: Dict[str, Any]) -> bool:
    """Generic update - use specific methods."""
    raise NotImplementedError("Use update_funnel, update_node, etc.")
