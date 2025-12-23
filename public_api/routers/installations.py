# public-api/routers/installations.py

"""
Installation Management API
Handles the generation of tracking snippets, platform-specific integrations (WordPress, Shopify),
and proxy configurations for various backend environments.
"""

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone as tz
import secrets
import uuid
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class SimpleInstallationRequest(BaseModel):
    """Schema for ultra-fast 1-line installation setup"""
    site_url: str = Field(..., description="Target website URL")
    site_name: Optional[str] = Field(None, description="Human-readable name")

    @field_validator('site_url')
    @classmethod
    def ensure_protocol(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            return f"https://{v}"
        return v

class InstallationResponse(BaseModel):
    """Response containing tracking snippets and setup instructions"""
    id: str
    token: str
    site_url: str
    site_name: str
    tracking_code: str
    instructions: List[str]
    status: str
    created_at: datetime

class InstallationSummary(BaseModel):
    """Summarized installation data for lists"""
    id: str
    site_url: str
    site_name: Optional[str]
    platform: str
    status: str
    active_experiments: int
    last_activity: Optional[datetime] = None
    created_at: datetime

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/simple", response_model=InstallationResponse, status_code=status.HTTP_201_CREATED)
async def create_simple_installation(
    request: SimpleInstallationRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Generates a 1-line tracking snippet for immediate deployment"""
    try:
        token = f"inst_{secrets.token_urlsafe(18)}"
        site_name = request.site_name or request.site_url
        
        async with db.pool.acquire() as conn:
            inst_id = await conn.fetchval(
                """
                INSERT INTO platform_installations (user_id, platform, installation_method, site_url, site_name, installation_token, status)
                VALUES ($1, 'web', 'simple_snippet', $2, $3, $4, 'pending')
                RETURNING id
                """,
                user_id, request.site_url, site_name, token
            )
            
            await conn.execute(
                "INSERT INTO installation_logs (installation_id, event_type, message) VALUES ($1, 'created', 'Simple installation initialized')",
                inst_id
            )
            
        snippet = f'<script src="https://cdn.samplit.com/t.js?token={token}" async></script>'
        
        return InstallationResponse(
            id=str(inst_id),
            token=token,
            site_url=request.site_url,
            site_name=site_name,
            tracking_code=snippet,
            instructions=[
                "Copy the snippet provided below.",
                "Insert it into the <head> section of your website.",
                "Deploy the changes and visit your site once.",
                "Return here to verify the connection."
            ],
            status="pending",
            created_at=datetime.now(tz.utc)
        )
        
    except Exception as e:
        logger.error(f"Failed to create installation: {e}", exc_info=True)
        raise APIError("Installation creation failed", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.get("/", response_model=List[InstallationSummary])
async def list_installations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves all active and pending installations for the current user"""
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    pi.id, pi.site_url, pi.site_name, pi.platform, pi.status, pi.last_activity, pi.created_at,
                    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'active') as active_exps
                FROM platform_installations pi
                LEFT JOIN experiments e ON e.user_id = pi.user_id AND e.target_url LIKE pi.site_url || '%'
                WHERE pi.user_id = $1 AND pi.status != 'archived'
                GROUP BY pi.id ORDER BY pi.created_at DESC
                """,
                user_id
            )
            
        return [
            InstallationSummary(
                id=str(row['id']),
                site_url=row['site_url'],
                site_name=row['site_name'],
                platform=row['platform'],
                status=row['status'],
                active_experiments=row['active_exps'] or 0,
                last_activity=row['last_activity'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Failed to list installations for {user_id}: {e}")
        raise APIError("Search failed", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/{installation_id}/verify")
async def verify_installation(
    installation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Trigger manual remote verification of the tracking snippet on the target site"""
    try:
        async with db.pool.acquire() as conn:
            inst = await conn.fetchrow("SELECT site_url, installation_token FROM platform_installations WHERE id = $1 AND user_id = $2", installation_id, user_id)
            if not inst:
                raise APIError("Installation not found", code=ErrorCodes.NOT_FOUND, status=404)
            
            # Simple remote check (mocking logic from helper)
            success = await _check_remote_snippet(inst['site_url'], inst['installation_token'])
            
            if success:
                await conn.execute(
                    "UPDATE platform_installations SET status = 'active', verified_at = NOW(), last_activity = NOW() WHERE id = $1",
                    installation_id
                )
                await conn.execute(
                    "INSERT INTO installation_logs (installation_id, event_type, message) VALUES ($1, 'verified', 'Verified via remote crawler')",
                    installation_id
                )
                return {"verified": True, "status": "active"}
            
            return {"verified": False, "error": "Snippet not detected. Ensure it's inside the <head> tags."}
            
    except Exception as e:
        if isinstance(e, APIError): raise
        logger.error(f"Verification error: {e}")
        raise APIError("Verification service reached a timeout", code=ErrorCodes.INTERNAL_ERROR, status=503)


@router.get("/{id}/code")
async def get_snippet_params(
    id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieve existing tracking configuration and snippet for an installation"""
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT installation_token, site_url FROM platform_installations WHERE id = $1 AND user_id = $2", id, user_id)
        if not row:
            raise APIError("Forbidden or not found", code=ErrorCodes.FORBIDDEN, status=403)
            
        token = row['installation_token']
        return {
            "id": id,
            "token": token,
            "tracking_code": f'<script src="https://cdn.samplit.com/t.js?token={token}" async></script>',
            "site_url": row['site_url']
        }


@router.delete("/{installation_id}", response_model=APIResponse)
async def delete_installation(
    installation_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Archives the installation and halts all tracking/experimentation for that site"""
    async with db.pool.acquire() as conn:
        result = await conn.execute("UPDATE platform_installations SET status = 'archived', updated_at = NOW() WHERE id = $1 AND user_id = $2", installation_id, user_id)
        if result == "UPDATE 0":
            raise APIError("Not found", code=ErrorCodes.NOT_FOUND, status=404)
            
    return APIResponse(success=True, message="Installation archived successfully")

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def _check_remote_snippet(url: str, token: str) -> bool:
    """Internal crawler to verify snippet presence"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, allow_redirects=True) as resp:
                if resp.status != 200: return False
                html = await resp.text()
                return token in html and 'cdn.samplit.com' in html
    except:
        return False
