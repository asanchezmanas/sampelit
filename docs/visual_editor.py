# public_api/routers/visual_editor.py

"""
Visual Orchestration API
Enables point-and-click experiment configuration through a proxied interface.
Handles CSS/XPath selection, content injection, and variant persistence.

UPDATED: Now uses Firecrawl for JavaScript rendering support.
"""

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse

# Firecrawl integration
from integration.firecrawl import get_visual_proxy

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
    element_type: str = "other"
    original_content: VisualVariant
    variants: List[VisualVariant]


class VisualEditorSaveRequest(BaseModel):
    """
    Payload sent by visual-editor.html
    """
    experiment_name: str
    page_url: str
    elements: List[VisualElement]
    traffic_allocation: float = 1.0


class ProxyMetadata(BaseModel):
    """Metadata returned by proxy endpoint"""
    source: str  # "firecrawl" | "fallback" | "cache"
    credits_used: Optional[int] = None
    warning: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/proxy", response_class=HTMLResponse)
async def visual_proxy(
    url: str = Query(..., description="Target URL to proxy"),
    user_id: str = Depends(get_current_user),
    force_js: bool = Query(False, description="Force Firecrawl (no fallback)"),
    skip_cache: bool = Query(False, description="Skip cache and fetch fresh")
):
    """
    Proxies a target website with JavaScript rendering.
    
    Uses Firecrawl API to render JavaScript-heavy sites (SPAs, React, Vue, etc.)
    Falls back to basic HTTP fetch if Firecrawl is unavailable.
    
    Args:
        url: URL to load in the Visual Editor
        force_js: If True, only use Firecrawl (fail if unavailable)
        skip_cache: If True, bypass cache and fetch fresh content
    
    Returns:
        HTMLResponse with the page content and injected editor scripts
        
    Response Headers:
        X-Samplit-Proxy-Source: Source of the content (firecrawl/fallback/cache)
        X-Samplit-Credits-Used: Firecrawl credits consumed (if applicable)
    """
    proxy = get_visual_proxy()
    
    result = await proxy.fetch_page(
        url=url,
        use_cache=not skip_cache,
        force_firecrawl=force_js
    )
    
    # Build response with metadata headers
    response = HTMLResponse(
        content=result.html,
        status_code=200 if result.success else 502
    )
    
    # Add informational headers
    response.headers["X-Samplit-Proxy-Source"] = result.source
    
    if result.metadata.get("credits_used"):
        response.headers["X-Samplit-Credits-Used"] = str(result.metadata["credits_used"])
    
    if result.metadata.get("warning"):
        response.headers["X-Samplit-Warning"] = result.metadata["warning"]
    
    return response


@router.get("/proxy/status")
async def proxy_status(user_id: str = Depends(get_current_user)):
    """
    Get status of the visual proxy, including Firecrawl availability.
    
    Returns:
        - firecrawl_configured: Whether Firecrawl API key is set
        - firecrawl_credits: Available credits (if configured)
        - cache_size: Current cache size
    """
    proxy = get_visual_proxy()
    
    status = {
        "firecrawl_configured": proxy.firecrawl.is_configured,
        "firecrawl_credits": None,
        "cache_size": len(proxy._cache),
        "cache_ttl_minutes": proxy.cache_ttl.total_seconds() / 60
    }
    
    # Check credits if configured
    if proxy.firecrawl.is_configured:
        credits = await proxy.firecrawl.check_credits()
        status["firecrawl_credits"] = credits
    
    return status


@router.post("/proxy/clear-cache")
async def clear_proxy_cache(user_id: str = Depends(get_current_user)):
    """
    Clear the proxy cache.
    
    Useful when debugging or when a site has been updated.
    """
    proxy = get_visual_proxy()
    cache_size_before = len(proxy._cache)
    proxy.clear_cache()
    
    return {
        "success": True,
        "cleared_entries": cache_size_before
    }


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
        
        async with db.pool.acquire() as conn:
            # Create experiment
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
            
            # Create variants for each element
            for i, element in enumerate(request.elements):
                # Create control variant (original)
                await conn.execute(
                    """
                    INSERT INTO variants (experiment_id, name, content, is_control)
                    VALUES ($1, $2, $3, true)
                    """,
                    exp_id,
                    f"{element.name} - Control",
                    {
                        "selector": element.selector.dict(),
                        "content": element.original_content.dict()
                    }
                )
                
                # Create treatment variants
                for j, variant in enumerate(element.variants):
                    await conn.execute(
                        """
                        INSERT INTO variants (experiment_id, name, content, is_control)
                        VALUES ($1, $2, $3, false)
                        """,
                        exp_id,
                        f"{element.name} - Variant {chr(66 + j)}",  # B, C, D...
                        {
                            "selector": element.selector.dict(),
                            "content": variant.dict()
                        }
                    )
        
        return APIResponse(
            success=True,
            message="Experiment saved successfully",
            data={"id": str(exp_id), "redirect": f"/experiments/{exp_id}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to save visual experiment: {e}")
        raise APIError(
            f"Failed to save experiment: {str(e)}",
            code=ErrorCodes.INTERNAL_ERROR,
            status=500
        )


# ════════════════════════════════════════════════════════════════════════════
# LIFECYCLE HOOKS
# ════════════════════════════════════════════════════════════════════════════

async def shutdown_visual_editor():
    """
    Cleanup hook to be called on application shutdown.
    
    Add to main.py:
        @app.on_event("shutdown")
        async def shutdown():
            await shutdown_visual_editor()
    """
    from integration.firecrawl import shutdown_proxy
    await shutdown_proxy()
    logger.info("Visual Editor proxy shutdown complete")
