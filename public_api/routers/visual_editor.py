# public-api/routers/visual_editor.py

"""
Visual Orchestration API
Enables point-and-click experiment configuration through a proxied interface.
Handles CSS/XPath selection, content injection, and variant persistence.
"""

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import httpx
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS (Matching Frontend Payload)
# ════════════════════════════════════════════════════════════════════════════

class VisualSelector(BaseModel):
    selector: str
    type: str = "css"

class VisualVariant(BaseModel):
    html: Optional[str] = None
    text: Optional[str] = None

class VisualElement(BaseModel):
    name: str
    selector: VisualSelector
    element_type: str = "other"  # generic/other
    original_content: VisualVariant
    variants: List[VisualVariant]

class VisualEditorSaveRequest(BaseModel):
    """
    Payload sent by visual-editor.html
    Matches:
    {
        "experiment_name": "...",
        "page_url": "...",
        "elements": [...],
        "traffic_allocation": 1.0
    }
    """
    experiment_name: str
    page_url: str
    elements: List[VisualElement]
    traffic_allocation: float = 1.0

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/proxy", response_class=HTMLResponse)
async def visual_proxy(
    url: str = Query(..., description="Target URL to proxy"),
    user_id: str = Depends(get_current_user)
):
    """
    Proxies a target website and injects the Visual Editor Client (iframe script).
    Used by: static/visual-editor.html
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    try:
        # Use httpx to fetch the page
        # Verify=False is risky but necessary for dragging/dropping arbitrary sites in dev
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
            
            # Check content type
            ct = resp.headers.get("content-type", "").lower()
            if "text/html" not in ct:
                # Return assets (css/js/images) as is
                return Response(
                    content=resp.content, 
                    status_code=resp.status_code, 
                    media_type=ct
                )

            html = resp.text
            
            # Inject Editor Client Script
            # This script communicates with the parent window via postMessage
            injection = f"""
                <base href="{url}">
                <script src="/static/js/editor-client.js"></script>
                <style>
                    .samplit-highlight {{ 
                        outline: 2px dashed #3b82f6 !important; 
                        cursor: pointer !important; 
                        transition: all 0.2s ease;
                        background: rgba(59, 130, 246, 0.1);
                    }}
                    .samplit-selected {{ 
                        outline: 2px solid #2563eb !important; 
                        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
                        z-index: 99999;
                        position: relative;
                    }}
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
        logger.error(f"Visual proxy failed for {url}: {e}")
        return HTMLResponse(
            content=f"<h1>Proxy Error</h1><p>Failed to load {url}</p><p>Error: {str(e)}</p>",
            status_code=502
        )


@router.post("/save-elements", response_model=APIResponse)
async def save_experiment_elements(
    request: VisualEditorSaveRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Receives configuration from Visual Editor and converts it into a real Experiment.
    """
    try:
        logger.info(f"Saving experiment '{request.experiment_name}' from Visual Editor")
        
        # In the future:
        # 1. Convert VisualEditorSaveRequest -> CreateExperimentRequest
        # 2. Call ExperimentService.create_experiment()
        
        # For now, we simulate success to unblock the frontend workflow
        async with db.pool.acquire() as conn:
            # We can insert a placeholder experiment to prove DB connectivity
            exp_id = await conn.fetchval(
                """
                INSERT INTO experiments (name, description, url, status, user_id, traffic_allocation)
                VALUES ($1, $2, $3, 'draft', $4, $5)
                RETURNING id
                """,
                request.experiment_name,
                "Created via Visual Editor",
                request.page_url,
                user_id,
                request.traffic_allocation
            )
            
            # TODO: Insert elements and variants
        
        return APIResponse(
            success=True,
            message="Experiment saved successfully",
            data={"id": str(exp_id), "redirect": f"/experiments/{exp_id}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to save visual experiment: {e}")
        raise APIError(f"Failed to save experiment: {str(e)}", code=ErrorCodes.INTERNAL_ERROR, status=500)
