# public-api/routers/onboarding.py

"""
Onboarding Flow Management - VERSIÓN PREMIUM
Handles the multi-step initialization process for new users:
1. Welcome & Introduction
2. Installation Setup (Platform config)
3. Connection Verification (Traffic detection)
4. Dashboard Activation
"""

from fastapi import APIRouter, Depends, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone as tz
import logging

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from public_api.models import APIResponse
from public_api.models.onboarding_models import OnboardingStatus, CompleteStepRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Retrieves current progress or initializes onboarding for a new user.
    
    Ensures a smooth transition from registration to the first live experiment.
    """
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
                completed_at=row['completed_at']
            )
            
    except Exception as e:
        logger.error(f"Onboarding status synchronization failed for {user_id}: {e}")
        raise APIError("Failed to synchronize onboarding status", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/update-step", response_model=APIResponse)
async def update_onboarding_step(
    request: CompleteStepRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Manually advances the user to the specified onboarding step.
    
    Used for UI-driven navigation during the guided setup.
    """
    valid_steps = {'welcome', 'install', 'verify', 'complete'}
    if request.step not in valid_steps:
        raise APIError(f"Invalid onboarding step: {request.step}. Expected: {list(valid_steps)}", code=ErrorCodes.INVALID_INPUT, status=400)
    
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
        return APIResponse(success=True, message=f"Onboarding trajectory updated to {request.step}")
        
    except Exception as e:
        logger.error(f"Step transition failed for {user_id}: {e}")
        raise APIError("Failed to update onboarding progression", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/verify-installation")
async def verify_installation(
    installation_token: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Checks for active traffic signals associated with the provided token.
    
    Validates that the Samplit tracker is correctly integrated and reachable.
    """
    try:
        async with db.pool.acquire() as conn:
            # Locate target installation and check ownership
            inst = await conn.fetchrow(
                "SELECT last_activity, status FROM platform_installations WHERE installation_token = $1 AND user_id = $2",
                installation_token, user_id
            )
            
            if not inst:
                raise APIError("Installation signature not found or unauthorized", code=ErrorCodes.NOT_FOUND, status=404)
            
            # Connection is considered verified if activity was seen in the last 15 minutes
            verified = False
            if inst['last_activity']:
                # Ensure comparison is timezone-aware
                last_act = inst['last_activity']
                if last_act.tzinfo is None:
                    last_act = last_act.replace(tzinfo=tz.utc)
                
                time_diff = datetime.now(tz.utc) - last_act
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
            "message": "Protocol handshake successful. Tracking active." if verified else "Awaiting signal synchronization... Please visit your site to trigger the tracker."
        }
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Installation verification protocol failed: {e}")
        raise APIError("External verification handshake failed", code=ErrorCodes.INTERNAL_ERROR, status=500)


@router.post("/complete", response_model=APIResponse)
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Finalizes the onboarding process and unlocks full dashboard orchestration.
    """
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_onboarding SET completed = true, current_step = 'complete', completed_at = NOW() WHERE user_id = $1",
                user_id
            )
        return APIResponse(success=True, message="Onboarding protocol finalized. Control panel unlocked.")
    except Exception as e:
        logger.error(f"Onboarding completion lock failed: {e}")
        raise APIError("Failed to finalize account initialization", code=ErrorCodes.DATABASE_ERROR, status=500)


@router.post("/skip", response_model=APIResponse)
async def skip_onboarding(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db)
):
    """
    Allows experienced users to bypass the guided technical setup.
    """
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
        return APIResponse(success=True, message="Onboarding protocol bypassed. Direct terminal access enabled.")
    except Exception as e:
        logger.error(f"Onboarding bypass failed: {e}")
        raise APIError("Operation failed while skipping initialization", code=ErrorCodes.DATABASE_ERROR, status=500)
