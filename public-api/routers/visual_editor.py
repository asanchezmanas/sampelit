# public-api/routers/visual_editor.py

"""
Visual Editor Backend

✅ FIXED: Complete process for elements + variants

Endpoints para guardar y recuperar elementos seleccionados
por el Visual Editor, y crear variantes para cada elemento.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
from orchestration.services.experiment_service import ExperimentService
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

class VariantContent(BaseModel):
    """Content for a variant"""
    text: Optional[str] = None
    html: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    styles: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None

class ElementData(BaseModel):
    """Element data from Visual Editor"""
    name: str
    selector: SelectorConfig
    element_type: str
    original_content: VariantContent
    variants: List[VariantContent] = Field(..., min_items=1)  # ✅ NEW: variants included

class SaveElementsRequest(BaseModel):
    """✅ FIXED: Now includes variants"""
    experiment_id: str
    elements: List[ElementData]

class TestSelectorRequest(BaseModel):
    """Test selector uniqueness"""
    page_url: str
    selector: str

# ============================================
# ✅ FIXED: SAVE ELEMENTS + VARIANTS (COMPLETE PROCESS)
# ============================================

@router.post("/save-elements")
async def save_elements_and_variants(
    request: SaveElementsRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    ✅ FIXED: Save elements AND create variants
    
    Complete process:
    1. Verify experiment ownership
    2. Delete existing elements
    3. Create new elements
    4. Create variants for each element
    5. Initialize Thompson Sampling state
    """
    try:
        async with db.pool.acquire() as conn:
            # Verify experiment ownership
            exp = await conn.fetchrow(
                "SELECT id, status FROM experiments WHERE id = $1 AND user_id = $2",
                request.experiment_id,
                user_id
            )
            
            if not exp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found or access denied"
                )
            
            # Can't edit active experiments
            if exp['status'] not in ['draft']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot edit experiment with status: {exp['status']}"
                )
            
            # Delete existing elements (cascade deletes variants)
            await conn.execute(
                "DELETE FROM experiment_elements WHERE experiment_id = $1",
                request.experiment_id
            )
            
            # ✅ Save elements AND variants
            element_ids = []
            variant_ids = []
            
            for elem_idx, element in enumerate(request.elements):
                # Create element
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
                    elem_idx,
                    element.name,
                    element.selector.type,
                    element.selector.selector,
                    json.dumps(element.selector.fallback_selectors),
                    element.element_type,
                    json.dumps(element.original_content.dict())
                )
                element_ids.append(str(element_id))
                
                # ✅ NEW: Create variants for this element
                for var_idx, variant in enumerate(element.variants):
                    # Initialize Thompson Sampling state
                    initial_state = {
                        'success_count': 1,  # Prior alpha
                        'failure_count': 1,  # Prior beta
                        'samples': 0,
                        'alpha': 1.0,
                        'beta': 1.0,
                        'algorithm_type': 'bayesian'
                    }
                    
                    # Encrypt state
                    from engine.state.encryption import get_encryptor
                    encryptor = get_encryptor()
                    encrypted_state = encryptor.encrypt_state(initial_state)
                    
                    variant_id = await conn.fetchval(
                        """
                        INSERT INTO element_variants (
                            element_id, variant_order, name, content,
                            algorithm_state, total_allocations, total_conversions
                        ) VALUES ($1, $2, $3, $4, $5, 0, 0)
                        RETURNING id
                        """,
                        element_id,
                        var_idx,
                        f"Variant {chr(65 + var_idx)}",  # A, B, C...
                        json.dumps(variant.dict()),
                        encrypted_state
                    )
                    variant_ids.append(str(variant_id))
        
        return {
            "status": "success",
            "element_ids": element_ids,
            "variant_ids": variant_ids,
            "element_count": len(element_ids),
            "variant_count": len(variant_ids),
            "message": "Elements and variants saved successfully"
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
    Get saved elements for experiment (with variants)
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
            
            # Get elements with variants
            rows = await conn.fetch(
                """
                SELECT 
                    ee.id as element_id, 
                    ee.name as element_name, 
                    ee.element_order,
                    ee.selector_type, 
                    ee.selector_value, 
                    ee.fallback_selectors,
                    ee.element_type, 
                    ee.original_content,
                    ev.id as variant_id,
                    ev.variant_order,
                    ev.name as variant_name,
                    ev.content as variant_content
                FROM experiment_elements ee
                LEFT JOIN element_variants ev ON ee.id = ev.element_id
                WHERE ee.experiment_id = $1
                ORDER BY ee.element_order, ev.variant_order
                """,
                experiment_id
            )
        
        # Group by element
        elements = {}
        for row in rows:
            elem_id = str(row['element_id'])
            
            if elem_id not in elements:
                elements[elem_id] = {
                    'id': elem_id,
                    'name': row['element_name'],
                    'element_order': row['element_order'],
                    'selector': {
                        'type': row['selector_type'],
                        'selector': row['selector_value'],
                        'fallback_selectors': json.loads(row['fallback_selectors']) if row['fallback_selectors'] else []
                    },
                    'element_type': row['element_type'],
                    'original_content': json.loads(row['original_content']) if isinstance(row['original_content'], str) else row['original_content'],
                    'variants': []
                }
            
            # Add variant
            if row['variant_id']:
                elements[elem_id]['variants'].append({
                    'id': str(row['variant_id']),
                    'variant_order': row['variant_order'],
                    'name': row['variant_name'],
                    'content': row['variant_content']
                })
        
        return {
            "elements": list(elements.values()),
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
# ADD VARIANT TO ELEMENT
# ============================================

@router.post("/elements/{element_id}/variants")
async def add_variant_to_element(
    element_id: str,
    variant_content: VariantContent,
    variant_name: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    ✅ NEW: Add a new variant to an existing element
    
    Useful for adding variants after initial setup
    """
    try:
        async with db.pool.acquire() as conn:
            # Verify ownership
            element = await conn.fetchrow(
                """
                SELECT ee.id, ee.experiment_id
                FROM experiment_elements ee
                JOIN experiments e ON ee.experiment_id = e.id
                WHERE ee.id = $1 AND e.user_id = $2
                """,
                element_id,
                user_id
            )
            
            if not element:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Element not found or access denied"
                )
            
            # Get next variant order
            max_order = await conn.fetchval(
                "SELECT COALESCE(MAX(variant_order), -1) FROM element_variants WHERE element_id = $1",
                element_id
            )
            next_order = (max_order or -1) + 1
            
            # Initialize Thompson Sampling state
            initial_state = {
                'success_count': 1,
                'failure_count': 1,
                'samples': 0,
                'alpha': 1.0,
                'beta': 1.0,
                'algorithm_type': 'bayesian'
            }
            
            # Encrypt
            from engine.state.encryption import get_encryptor
            encryptor = get_encryptor()
            encrypted_state = encryptor.encrypt_state(initial_state)
            
            # Create variant
            variant_id = await conn.fetchval(
                """
                INSERT INTO element_variants (
                    element_id, variant_order, name, content,
                    algorithm_state, total_allocations, total_conversions
                ) VALUES ($1, $2, $3, $4, $5, 0, 0)
                RETURNING id
                """,
                element_id,
                next_order,
                variant_name or f"Variant {chr(65 + next_order)}",
                json.dumps(variant_content.dict()),
                encrypted_state
            )
        
        return {
            "status": "success",
            "variant_id": str(variant_id),
            "message": "Variant added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add variant: {str(e)}"
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
    
    Basic validation - en producción usar headless browser
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

# ============================================
# DELETE ELEMENT
# ============================================

@router.delete("/elements/{element_id}")
async def delete_element(
    element_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Delete element (and its variants via CASCADE)
    """
    try:
        async with db.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM experiment_elements ee
                USING experiments e
                WHERE ee.id = $1 
                  AND ee.experiment_id = e.id 
                  AND e.user_id = $2
                """,
                element_id,
                user_id
            )
            
            if result == "DELETE 0":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Element not found or access denied"
                )
        
        return {
            "status": "success",
            "message": "Element deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete element: {str(e)}"
        )
