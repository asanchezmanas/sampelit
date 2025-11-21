# public-api/routers/onboarding.py

"""
Onboarding Flow Endpoints

Gestiona el proceso de onboarding de nuevos usuarios:
1. Welcome
2. Installation setup
3. Verification
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager

router = APIRouter()

# ============================================
# MODELS
# ============================================

class OnboardingStatus(BaseModel):
    """Onboarding status response"""
    completed: bool
    current_step: str
    installation_verified: bool
    installation_token: Optional[str] = None

class CompleteStepRequest(BaseModel):
    """Mark step as complete"""
    step: str

# ============================================
# GET ONBOARDING STATUS
# ============================================

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Get current onboarding status for user
    """
    try:
        async with db.pool.acquire() as conn:
            # Check if user has onboarding record
            onboarding = await conn.fetchrow(
                "SELECT * FROM user_onboarding WHERE user_id = $1",
                user_id
            )
            
            if not onboarding:
                # Create initial onboarding record
                await conn.execute(
                    """
                    INSERT INTO user_onboarding (user_id, current_step)
                    VALUES ($1, 'welcome')
                    """,
                    user_id
                )
                
                return OnboardingStatus(
                    completed=False,
                    current_step='welcome',
                    installation_verified=False
                )
            
            # Get installation token if exists
            installation_token = None
            if onboarding['current_step'] in ['install', 'verify']:
                token_row = await conn.fetchrow(
                    """
                    SELECT installation_token 
                    FROM platform_installations 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT 1
                    """,
                    user_id
                )
                if token_row:
                    installation_token = token_row['installation_token']
            
            return OnboardingStatus(
                completed=onboarding['completed'],
                current_step=onboarding['current_step'],
                installation_verified=onboarding['installation_verified'],
                installation_token=installation_token
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
        )

# ============================================
# UPDATE ONBOARDING STEP
# ============================================

@router.post("/update-step")
async def update_onboarding_step(
    request: CompleteStepRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Update current onboarding step
    """
    
    valid_steps = ['welcome', 'install', 'verify', 'complete']
    
    if request.step not in valid_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step. Must be one of: {', '.join(valid_steps)}"
        )
    
    try:
        async with db.pool.acquire() as conn:
            # Update step
            await conn.execute(
                """
                UPDATE user_onboarding
                SET current_step = $1, completed = $2
                WHERE user_id = $3
                """,
                request.step,
                request.step == 'complete',
                user_id
            )
        
        return {"status": "success", "step": request.step}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update step: {str(e)}"
        )

# ============================================
# VERIFY INSTALLATION
# ============================================

@router.post("/verify-installation")
async def verify_installation(
    installation_token: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Verify that installation is working
    
    Checks if we've received any events from this installation
    in the last 5 minutes
    """
    try:
        async with db.pool.acquire() as conn:
            # Check recent activity
            installation = await conn.fetchrow(
                """
                SELECT last_activity, status
                FROM platform_installations
                WHERE installation_token = $1 AND user_id = $2
                """,
                installation_token,
                user_id
            )
            
            if not installation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Installation not found"
                )
            
            # Check if verified (activity in last 5 minutes)
            verified = False
            if installation['last_activity']:
                from datetime import timezone as tz
                time_diff = datetime.now(tz.utc) - installation['last_activity']
                verified = time_diff.total_seconds() < 300  # 5 minutes
            
            if verified:
                # Mark installation as verified
                await conn.execute(
                    """
                    UPDATE platform_installations
                    SET status = 'active', verified_at = NOW()
                    WHERE installation_token = $1
                    """,
                    installation_token
                )
                
                # Update onboarding
                await conn.execute(
                    """
                    UPDATE user_onboarding
                    SET installation_verified = true
                    WHERE user_id = $1
                    """,
                    user_id
                )
        
        return {
            "verified": verified,
            "message": "Installation working!" if verified else "No activity detected yet. Please visit your site."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

# ============================================
# COMPLETE ONBOARDING
# ============================================

@router.post("/complete")
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Mark onboarding as complete
    """
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_onboarding
                SET completed = true, 
                    current_step = 'complete',
                    completed_at = NOW()
                WHERE user_id = $1
                """,
                user_id
            )
        
        return {
            "status": "success",
            "message": "Onboarding completed!"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )

# ============================================
# SKIP ONBOARDING
# ============================================

@router.post("/skip")
async def skip_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Skip onboarding (for experienced users)
    """
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_onboarding (user_id, completed, current_step)
                VALUES ($1, true, 'complete')
                ON CONFLICT (user_id) DO UPDATE
                SET completed = true, current_step = 'complete'
                """,
                user_id
            )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip onboarding: {str(e)}"
        )
