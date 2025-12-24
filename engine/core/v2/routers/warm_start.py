# public_api/routers/warm_start.py

"""
Warm-Start API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field

from engine.services.warm_start_service import WarmStartService
from data_access.database import get_database

router = APIRouter()


class WarmStartConfig(BaseModel):
    enabled: bool
    source_type: str = Field(..., regex='^(experiment|template|none)$')
    source_id: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class CreateTemplateRequest(BaseModel):
    name: str
    source_experiment_ids: List[str]
    category: Optional[str] = None
    description: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


@router.get('/templates')
async def list_templates(
    category: Optional[str] = None,
    db = Depends(get_database)
):
    """List available warm-start templates"""
    
    async with db.pool.acquire() as conn:
        query = """
            SELECT 
                id,
                name,
                category,
                description,
                times_used,
                avg_improvement,
                created_at
            FROM experiment_templates
            WHERE 1=1
        """
        
        params = []
        if category:
            query += " AND category = $1"
            params.append(category)
        
        query += " ORDER BY times_used DESC, created_at DESC"
        
        templates = await conn.fetch(query, *params)
    
    return {
        'templates': [
            {
                'id': str(t['id']),
                'name': t['name'],
                'category': t['category'],
                'description': t['description'],
                'times_used': t['times_used'],
                'avg_improvement': t['avg_improvement'] or 0.0,
                'created_at': t['created_at'].isoformat()
            }
            for t in templates
        ]
    }


@router.post('/templates')
async def create_template(
    request: CreateTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_database)
):
    """Create new warm-start template"""
    
    service = WarmStartService(db.pool)
    
    template_id = await service.create_template(
        user_id=user_id,
        name=request.name,
        source_experiment_ids=request.source_experiment_ids,
        category=request.category,
        description=request.description,
        confidence=request.confidence
    )
    
    return {
        'template_id': template_id,
        'message': 'Template created successfully'
    }


@router.get('/stats')
async def get_warm_start_stats(
    db = Depends(get_database)
):
    """Get warm-start usage statistics"""
    
    service = WarmStartService(db.pool)
    stats = await service.get_warm_start_stats()
    
    return stats


@router.get('/experiments/{experiment_id}/historical-data')
async def get_historical_data(
    experiment_id: str,
    db = Depends(get_database)
):
    """Get historical performance data from experiment"""
    
    service = WarmStartService(db.pool)
    
    historical_data = await service._extract_historical_data(
        experiment_id,
        min_samples=100
    )
    
    if not historical_data:
        raise HTTPException(
            status_code=404,
            detail="No historical data available (minimum 100 samples required)"
        )
    
    return {
        'experiment_id': experiment_id,
        'variants': historical_data
    }
```

**Checklist Día 16-18:**
```
✅ Create frontend/src/components/experiments/WarmStartSelector.tsx
✅ Implement warm-start UI
✅ Create public_api/routers/warm_start.py
✅ Add API endpoints
✅ Test UI flow
✅ Integration test
✅ Commit: "feat: add warm-start UI and API"
