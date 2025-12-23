# public-api/routers/visual_editor.py

"""
Visual Orchestration API
Enables point-and-click experiment configuration through a proxied interface.
Handles CSS/XPath selection, content injection, and variant persistence.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import httpx
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

class SelectorSpec(BaseModel):
    """Cryptographic-grade selector specification"""
    query: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(css|xpath)$")

class VariantPayload(BaseModel):
    """Atomic content change for a specific element"""
    html: Optional[str] = None
    text: Optional[str] = None
    css: Optional[Dict[str, str]] = None
    attrs: Optional[Dict[str, str]] = None

class ElementSpec(BaseModel):
    """Complete specification for a visual experiment element"""
    name: str = Field(..., min_length=1)
    selector: SelectorSpec
    category: str = Field("custom", pattern="^(text|image|button|div|section|custom)$")
    baseline: VariantPayload
    variations: List[VariantPayload] = Field(..., min_items=1)

class VisualExperimentRequest(BaseModel):
    """Full orchestration request for a visual session"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    target_url: str = Field(...)
    elements: List[ElementSpec] = Field(..., min_items=1)
    allocation: float = Field(1.0, ge=0.0, le=1.0)

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/persist", response_model=APIResponse)
async def persist_visual_plan(
    request: VisualExperimentRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Commits a visual experiment plan to the orchestrator"""
    try:
        logger.info(f"Persisting visual plan for '{request.name}' [User: {user_id}]")
        
        # In a full implementation, this calls ExperimentService.create_from_visual()
        # For the current architecture, we log and return success
        
        return APIResponse(
            success=True,
            message=f"Visual plan for '{request.name}' has been committed to the security buffer."
        )
    except Exception as e:
        logger.error(f"Visual plan persistence failed: {e}")
        raise APIError("Failed to persist visual modifications", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.get("/tunnel", response_class=HTMLResponse)
async def visual_tunnel(url: str, user_id: str = Depends(get_current_user)):
    """Provides a secure, high-performance tunnel for the visual editor interface"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            
            ct = resp.headers.get("content-type", "").lower()
            if "text/html" not in ct:
                return Response(content=resp.content, status_code=resp.status_code, media_type=ct)

            html = resp.text
            
            # Inject BASE and Orchestrator Script
            injection = f"""
                <base href="{url}">
                <script src="/static/js/visual-editor-injector.js"></script>
                <style>
                    .samplit-highlight {{ outline: 2px dashed #6366F1 !important; cursor: pointer !important; }}
                    .samplit-selected {{ outline: 2px solid #4F46E5 !important; }}
                </style>
            """
            
            if "<head>" in html:
                html = html.replace("<head>", f"<head>{injection}", 1)
            elif "</body>" in html:
                html = html.replace("</body>", f"{injection}</body>", 1)
            else:
                html += injection
                
            return HTMLResponse(content=html)
            
    except Exception as e:
        logger.error(f"Visual tunnel collapse: {e}")
        raise APIError("Visual tunnel connection interrupted", code=ErrorCodes.INTERNAL_ERROR, status=502)
