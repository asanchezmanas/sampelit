# public-api/routers/onboarding.py

"""
Onboarding Flow Management
Handles the multi-step initialization process for new users:
1. Welcome & Introduction
2. Installation Setup (Platform config)
3. Connection Verification (Trafic detection)
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone as tz
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

class OnboardingStatus(BaseModel):
    """Cumulative state of the user's onboarding journey"""
    completed: bool
    current_step: str
    installation_verified: bool
    installation_token: Optional[str] = None
    completed_at: Optional[datetime] = None

class CompleteStepRequest(BaseModel):
    """Payload to transition between onboarding steps"""
    step: str = Field(..., description="Target step: welcome, install, verify, complete")

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves current progress or initializes onboarding for a new user"""
    try:
        async with db.pool.acquire() as conn:
            # Check for existing record
            row = await conn.fetchrow("SELECT * FROM user_onboarding WHERE user_id = $1", user_id)
            
            if not row:
                # Initialize onboarding record on first access
                await conn.execute(
                    "INSERT INTO user_onboarding (user_id, current_step) VALUES ($1, 'welcome')",
                    user_id
                )
                return OnboardingStatus(completed=False, current_step='welcome', installation_verified=False)
            
            # Fetch the most recent installation token if applicable
            token = None
            if row['current_step'] in ['install', 'verify']:
                token = await conn.fetchval(
                    "SELECT installation_token FROM platform_installations WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
                    user_id
                )
            
            return OnboardingStatus(
                completed=row['completed'],
                current_step=row['current_step'],
                installation_verified=row['installation_verified'],
                installation_token=token,
                completed_at=row.get('completed_at')
            )
            
    except Exception as e:
        logger.error(f"Onboarding status fetch failed: {e}")
        raise APIError("Failed to fetch onboarding status", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/update-step", response_model=APIResponse)
async def update_onboarding_step(
    request: CompleteStepRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Manually advances the user to the specified onboarding step"""
    valid_steps = {'welcome', 'install', 'verify', 'complete'}
    if request.step not in valid_steps:
        raise APIError(f"Invalid step. Expected: {list(valid_steps)}", code=ErrorCodes.INVALID_INPUT, status=400)
    
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_onboarding
                SET current_step = $1, 
                    completed = $2,
                    completed_at = CASE WHEN $2 THEN NOW() ELSE completed_at END
                WHERE user_id = $3
                """,
                request.step, request.step == 'complete', user_id
            )
        return APIResponse(success=True, message=f"Step updated to {request.step}")
        
    except Exception as e:
        logger.error(f"Step update failed: {e}")
        raise APIError("Failed to update onboarding progress", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/verify-installation")
async def verify_installation(
    installation_token: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Checks for active traffic signals associated with the provided token"""
    try:
        async with db.pool.acquire() as conn:
            # Locate target installation and check ownership
            inst = await conn.fetchrow(
                "SELECT last_activity, status FROM platform_installations WHERE installation_token = $1 AND user_id = $2",
                installation_token, user_id
            )
            
            if not inst:
                raise APIError("Installation token not found or unauthorized", code=ErrorCodes.NOT_FOUND, status=404)
            
            # Connection is considered verified if activity was seen in the last 15 minutes
            verified = False
            if inst['last_activity']:
                time_diff = datetime.now(tz.utc) - inst['last_activity']
                verified = time_diff.total_seconds() < 900  # 15 minute window
            
            if verified:
                # Synchronously update verification status
                await conn.execute(
                    "UPDATE platform_installations SET status = 'active', verified_at = NOW() WHERE installation_token = $1",
                    installation_token
                )
                await conn.execute(
                    "UPDATE user_onboarding SET installation_verified = true, current_step = 'complete' WHERE user_id = $1",
                    user_id
                )
        
        return {
            "verified": verified,
            "message": "Signal detected. Integration successful." if verified else "Waiting for signal... Please visit your site to trigger verification."
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Installation verification failed: {e}")
        raise APIError("Internal verification error", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/complete", response_model=APIResponse)
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Finalizes the onboarding process and unlocks full dashboard access"""
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_onboarding SET completed = true, current_step = 'complete', completed_at = NOW() WHERE user_id = $1",
                user_id
            )
        return APIResponse(success=True, message="Onboarding workflow finalized")
    except Exception as e:
        logger.error(f"Onboarding completion failed: {e}")
        raise APIError("Initialization failed", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/skip", response_model=APIResponse)
async def skip_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """Allows experienced users to bypass the guided setup"""
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_onboarding (user_id, completed, current_step, completed_at)
                VALUES ($1, true, 'complete', NOW())
                ON CONFLICT (user_id) DO UPDATE SET completed = true, current_step = 'complete', completed_at = NOW()
                """,
                user_id
            )
        return APIResponse(success=True, message="Onboarding bypassed")
    except Exception as e:
        logger.error(f"Onboarding skip failed: {e}")
        raise APIError("Operation failed", code=ErrorCodes.DATABASE_ERROR, status=500)
