# public-api/routers/visual_editor.py

"""
Visual Editor Backend

Endpoints para guardar y recuperar elementos seleccionados
por el Visual Editor
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
import json

router = APIRouter()

# ============================================
# MODELS
# ============================================

class SelectorConfig(BaseModel):
    """Selector configuration"""
    type: str
    selector: str
    fallback_selectors: List[str] = Field(default_factory=list)

class ElementData(BaseModel):
    """Element data from Visual Editor"""
    id: str
    name: str
    selector: SelectorConfig
    element_type: str
    original_content: Dict[str, Any]
    xpath: Optional[str] = None

class SaveElementRequest(BaseModel):
    """Save element request"""
    experiment_id: str
    elements: List[ElementData]

class TestSelectorRequest(BaseModel):
    """Test selector uniqueness"""
    page_url: str
    selector: str

# ============================================
# SAVE ELEMENTS
# ============================================

@router.post("/save-element")
async def save_element(
    request: SaveElementRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Save selected elements for experiment
    """
    try:
        async with db.pool.acquire() as conn:
            # Verify experiment ownership
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                request.experiment_id,
                user_id
            )
            
            if not exp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found or access denied"
                )
            
            # Delete existing elements
            await conn.execute(
                "DELETE FROM experiment_elements WHERE experiment_id = $1",
                request.experiment_id
            )
            
            # Save new elements
            element_ids = []
            for idx, element in enumerate(request.elements):
                element_id = await conn.fetchval(
                    """
                    INSERT INTO experiment_elements (
                        experiment_id, element_order, name,
                        selector_type, selector_value, fallback_selectors,
                        element_type, original_content
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    request.experiment_id,
                    idx,
                    element.name,
                    element.selector.type,
                    element.selector.selector,
                    json.dumps(element.selector.fallback_selectors),
                    element.element_type,
                    json.dumps(element.original_content)
                )
                element_ids.append(str(element_id))
        
        return {
            "status": "success",
            "element_ids": element_ids,
            "count": len(element_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save elements: {str(e)}"
        )

# ============================================
# GET ELEMENTS
# ============================================

@router.get("/elements/{experiment_id}")
async def get_elements(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get saved elements for experiment
    """
    try:
        async with db.pool.acquire() as conn:
            # Verify ownership
            exp = await conn.fetchrow(
                "SELECT id FROM experiments WHERE id = $1 AND user_id = $2",
                experiment_id,
                user_id
            )
            
            if not exp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found"
                )
            
            # Get elements
            rows = await conn.fetch(
                """
                SELECT 
                    id, name, element_order,
                    selector_type, selector_value, fallback_selectors,
                    element_type, original_content
                FROM experiment_elements
                WHERE experiment_id = $1
                ORDER BY element_order
                """,
                experiment_id
            )
        
        elements = [
            {
                'id': str(row['id']),
                'name': row['name'],
                'element_order': row['element_order'],
                'selector': {
                    'type': row['selector_type'],
                    'selector': row['selector_value'],
                    'fallback_selectors': json.loads(row['fallback_selectors']) if row['fallback_selectors'] else []
                },
                'element_type': row['element_type'],
                'original_content': json.loads(row['original_content']) if isinstance(row['original_content'], str) else row['original_content']
            }
            for row in rows
        ]
        
        return {
            "elements": elements,
            "count": len(elements)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get elements: {str(e)}"
        )

# ============================================
# TEST SELECTOR
# ============================================

@router.post("/test-selector")
async def test_selector(
    request: TestSelectorRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Test if selector is unique and valid
    
    Este endpoint podría usar headless browser (playwright/puppeteer)
    para verificar selectores, pero por ahora solo valida sintaxis
    """
    
    # Basic validation
    if not request.selector or len(request.selector.strip()) == 0:
        return {
            "valid": False,
            "unique": False,
            "error": "Selector is empty"
        }
    
    # Check if it looks like valid CSS selector
    if request.selector.startswith('#') or request.selector.startswith('.') or ' ' in request.selector:
        return {
            "valid": True,
            "unique": None,  # Can't verify without actually testing on page
            "message": "Selector appears valid. Test on your page to confirm uniqueness."
        }
    
    return {
        "valid": True,
        "unique": None,
        "message": "Selector syntax looks valid"
    }
