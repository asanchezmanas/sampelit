# public-api/routers/funnels.py
"""
Funnel Management API - Tree-based conversion paths with bandit optimization.
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
import logging

from data_access.database import DatabaseManager
from data_access.repositories.funnel_repository import FunnelRepository
from public_api.models.funnel_models import (
    CreateFunnelRequest, UpdateFunnelRequest,
    CreateNodeRequest, UpdateNodeRequest, CreateEdgeRequest,
    FunnelResponse, FunnelListResponse, FunnelNodeResponse, FunnelEdgeResponse,
    FunnelStatus
)
from public_api.models import APIResponse, PaginatedResponse
from public_api.dependencies import get_db, get_current_user, PaginationParams, get_pagination
from public_api.middleware.error_handler import APIError
from public_api.errors import ErrorCode, get_error_description

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# FUNNEL CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/", response_model=APIResponse, status_code=201)
async def create_funnel(
    request: CreateFunnelRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Create a new funnel."""
    try:
        repo = FunnelRepository(db.pool)
        
        funnel_id = await repo.create_funnel(
            user_id=user_id,
            name=request.name,
            description=request.description,
            conversion_type=request.conversion_type.value,
            conversion_config=request.conversion_config.model_dump() if request.conversion_config else None,
            session_timeout_hours=request.session_timeout_hours
        )
        
        return APIResponse(
            success=True,
            message="Funnel created successfully",
            data={"id": funnel_id}
        )
        
    except Exception as e:
        logger.error(f"Failed to create funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.get("/", response_model=PaginatedResponse[FunnelListResponse])
async def list_funnels(
    status_filter: Optional[FunnelStatus] = Query(None),
    pagination: PaginationParams = Depends(get_pagination),
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """List user's funnels with stats."""
    try:
        repo = FunnelRepository(db.pool)
        
        funnels = await repo.list_funnels(
            user_id=user_id,
            status=status_filter.value if status_filter else None,
            limit=pagination.per_page,
            offset=pagination.offset
        )
        
        items = [
            FunnelListResponse(
                id=str(f['id']),
                name=f['name'],
                description=f.get('description'),
                status=f['status'],
                node_count=f.get('node_count', 0),
                total_sessions=f.get('total_sessions', 0),
                conversion_rate=float(f.get('conversion_rate', 0) or 0),
                created_at=f['created_at']
            )
            for f in funnels
        ]
        
        return PaginatedResponse(
            items=items,
            total=len(items),  # TODO: Add total count query
            page=pagination.page,
            per_page=pagination.per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list funnels: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.get("/{funnel_id}", response_model=FunnelResponse)
async def get_funnel(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get funnel with nodes and edges."""
    try:
        repo = FunnelRepository(db.pool)
        
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError(
                "Funnel not found",
                code=ErrorCode.EXP_READ_001,
                status=404
            )
        
        # Get nodes and edges
        nodes = await repo.get_nodes(funnel_id)
        edges = await repo.get_edges(funnel_id)
        
        return FunnelResponse(
            id=str(funnel['id']),
            user_id=str(funnel['user_id']),
            name=funnel['name'],
            description=funnel.get('description'),
            conversion_type=funnel['conversion_type'],
            conversion_config=funnel.get('conversion_config'),
            session_timeout_hours=funnel['session_timeout_hours'],
            status=funnel['status'],
            created_at=funnel['created_at'],
            updated_at=funnel['updated_at'],
            started_at=funnel.get('started_at'),
            nodes=[
                FunnelNodeResponse(
                    id=str(n['id']),
                    funnel_id=str(n['funnel_id']),
                    name=n['name'],
                    node_type=n['node_type'],
                    node_order=n['node_order'],
                    parent_node_id=str(n['parent_node_id']) if n.get('parent_node_id') else None,
                    experiment_id=str(n['experiment_id']) if n.get('experiment_id') else None,
                    config=n.get('config'),
                    is_conversion_node=n['is_conversion_node'],
                    is_entry_node=n['is_entry_node'],
                    position_x=n['position_x'],
                    position_y=n['position_y'],
                    created_at=n['created_at']
                )
                for n in nodes
            ],
            edges=[
                FunnelEdgeResponse(
                    id=str(e['id']),
                    funnel_id=str(e['funnel_id']),
                    from_node_id=str(e['from_node_id']),
                    to_node_id=str(e['to_node_id']),
                    condition_type=e['condition_type'],
                    condition_config=e.get('condition_config'),
                    total_traversals=e['total_traversals'],
                    successful_conversions=e['successful_conversions'],
                    created_at=e['created_at']
                )
                for e in edges
            ]
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.put("/{funnel_id}", response_model=APIResponse)
async def update_funnel(
    funnel_id: str,
    request: UpdateFunnelRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Update funnel settings."""
    try:
        repo = FunnelRepository(db.pool)
        
        updates = request.model_dump(exclude_none=True)
        if 'conversion_type' in updates:
            updates['conversion_type'] = updates['conversion_type'].value
        if 'status' in updates:
            updates['status'] = updates['status'].value
        if 'conversion_config' in updates:
            updates['conversion_config'] = updates['conversion_config'].model_dump() if updates['conversion_config'] else {}
        
        success = await repo.update_funnel(funnel_id, user_id, updates)
        
        if not success:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Funnel updated successfully")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to update funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.delete("/{funnel_id}", response_model=APIResponse)
async def delete_funnel(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Delete a funnel and all its data."""
    try:
        repo = FunnelRepository(db.pool)
        success = await repo.delete_funnel(funnel_id, user_id)
        
        if not success:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Funnel deleted successfully")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.post("/{funnel_id}/activate", response_model=APIResponse)
async def activate_funnel(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Activate a funnel."""
    try:
        repo = FunnelRepository(db.pool)
        success = await repo.update_funnel(funnel_id, user_id, {"status": "active"})
        
        if not success:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Funnel activated")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to activate funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.post("/{funnel_id}/pause", response_model=APIResponse)
async def pause_funnel(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Pause a funnel."""
    try:
        repo = FunnelRepository(db.pool)
        success = await repo.update_funnel(funnel_id, user_id, {"status": "paused"})
        
        if not success:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Funnel paused")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to pause funnel: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NODE CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{funnel_id}/nodes", response_model=APIResponse, status_code=201)
async def create_node(
    funnel_id: str,
    request: CreateNodeRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Add a node to the funnel."""
    try:
        repo = FunnelRepository(db.pool)
        
        # Verify funnel ownership
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        node_id = await repo.create_node(
            funnel_id=funnel_id,
            name=request.name,
            node_type=request.node_type.value,
            parent_node_id=request.parent_node_id,
            config=request.config.model_dump() if request.config else None,
            is_conversion_node=request.is_conversion_node,
            is_entry_node=request.is_entry_node,
            position_x=request.position_x,
            position_y=request.position_y
        )
        
        return APIResponse(
            success=True,
            message="Node created successfully",
            data={"id": node_id}
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to create node: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.get("/{funnel_id}/nodes", response_model=List[FunnelNodeResponse])
async def get_nodes(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get all nodes in a funnel."""
    try:
        repo = FunnelRepository(db.pool)
        
        # Verify funnel ownership
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        nodes = await repo.get_nodes(funnel_id)
        
        return [
            FunnelNodeResponse(
                id=str(n['id']),
                funnel_id=str(n['funnel_id']),
                name=n['name'],
                node_type=n['node_type'],
                node_order=n['node_order'],
                parent_node_id=str(n['parent_node_id']) if n.get('parent_node_id') else None,
                experiment_id=str(n['experiment_id']) if n.get('experiment_id') else None,
                config=n.get('config'),
                is_conversion_node=n['is_conversion_node'],
                is_entry_node=n['is_entry_node'],
                position_x=n['position_x'],
                position_y=n['position_y'],
                created_at=n['created_at']
            )
            for n in nodes
        ]
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.delete("/{funnel_id}/nodes/{node_id}", response_model=APIResponse)
async def delete_node(
    funnel_id: str,
    node_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Delete a node from the funnel."""
    try:
        repo = FunnelRepository(db.pool)
        
        # Verify funnel ownership
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        success = await repo.delete_node(node_id, funnel_id)
        
        if not success:
            raise APIError("Node not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Node deleted successfully")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete node: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{funnel_id}/edges", response_model=APIResponse, status_code=201)
async def create_edge(
    funnel_id: str,
    request: CreateEdgeRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Create an edge between two nodes."""
    try:
        repo = FunnelRepository(db.pool)
        
        # Verify funnel ownership
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        edge_id = await repo.create_edge(
            funnel_id=funnel_id,
            from_node_id=request.from_node_id,
            to_node_id=request.to_node_id,
            condition_type=request.condition_type.value,
            condition_config=request.condition_config
        )
        
        return APIResponse(
            success=True,
            message="Edge created successfully",
            data={"id": edge_id}
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to create edge: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.get("/{funnel_id}/edges", response_model=List[FunnelEdgeResponse])
async def get_edges(
    funnel_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get all edges in a funnel."""
    try:
        repo = FunnelRepository(db.pool)
        
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        edges = await repo.get_edges(funnel_id)
        
        return [
            FunnelEdgeResponse(
                id=str(e['id']),
                funnel_id=str(e['funnel_id']),
                from_node_id=str(e['from_node_id']),
                to_node_id=str(e['to_node_id']),
                condition_type=e['condition_type'],
                condition_config=e.get('condition_config'),
                total_traversals=e['total_traversals'],
                successful_conversions=e['successful_conversions'],
                created_at=e['created_at']
            )
            for e in edges
        ]
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to get edges: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )


@router.delete("/{funnel_id}/edges/{edge_id}", response_model=APIResponse)
async def delete_edge(
    funnel_id: str,
    edge_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Delete an edge."""
    try:
        repo = FunnelRepository(db.pool)
        
        funnel = await repo.get_funnel(funnel_id, user_id)
        if not funnel:
            raise APIError("Funnel not found", code=ErrorCode.EXP_READ_001, status=404)
        
        success = await repo.delete_edge(edge_id, funnel_id)
        
        if not success:
            raise APIError("Edge not found", code=ErrorCode.EXP_READ_001, status=404)
        
        return APIResponse(success=True, message="Edge deleted successfully")
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete edge: {e}", exc_info=True)
        raise APIError(
            get_error_description(ErrorCode.DB_QUERY_001),
            code=ErrorCode.DB_QUERY_001,
            status=500
        )
