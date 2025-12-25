# public-api/routers/auth.py

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

from data_access.database import DatabaseManager
from public_api.dependencies import get_db, check_rate_limit, get_current_user
from public_api.middleware.error_handler import APIError, ErrorCodes
from config.settings import settings

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field('client', pattern='^(client|admin|editor)$')

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)

class AuthResponse(BaseModel):
    success: bool = True
    token: str
    user_id: str
    email: str
    name: str
    role: str

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            password_hash.encode('utf-8')
        )
    except Exception:
        return False

def create_token(user_id: str, role: str = 'client') -> str:
    """Create JWT token with role"""
    payload = {
        'sub': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(
        payload, 
        settings.SUPABASE_JWT_SECRET, 
        algorithm='HS256'
    )
    
    return token

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.post("/register", response_model=AuthResponse, dependencies=[Depends(check_rate_limit)])
async def register(
    request: RegisterRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Register new user"""
    
    # Check if user exists
    async with db.pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            request.email.lower()
        )
    
    if existing:
        raise APIError(
            message="Email already registered",
            code=ErrorCodes.VALIDATION_ERROR,
            status=400
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    try:
        async with db.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, name, company, role)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                request.email.lower(),
                password_hash,
                request.name,
                request.company,
                request.role
            )
    except Exception as e:
        raise APIError(
            message=f"Failed to create user: {str(e)}",
            code=ErrorCodes.DATABASE_ERROR,
            status=500
        )
    
    # Generate token
    token = create_token(str(user_id), request.role)
    
    return AuthResponse(
        token=token,
        user_id=str(user_id),
        email=request.email,
        name=request.name,
        role=request.role
    )

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(check_rate_limit)])
async def login(
    request: LoginRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Login user"""
    
    # Get user
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, name, role
            FROM users
            WHERE email = $1
            """,
            request.email.lower()
        )
    
    if not user:
        raise APIError(
            message="Invalid email or password",
            code=ErrorCodes.UNAUTHORIZED,
            status=401
        )
    
    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise APIError(
            message="Invalid email or password",
            code=ErrorCodes.UNAUTHORIZED,
            status=401
        )
    
    # Generate token
    # Handle nullable role (migration safety) by defaulting to client
    role = user['role'] if user.get('role') else 'client'
    token = create_token(str(user['id']), role)
    
    return AuthResponse(
        token=token,
        user_id=str(user['id']),
        email=user['email'],
        name=user['name'],
        role=role
    )

@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: DatabaseManager = Depends(get_db)
):
    """Get current user info"""
    
    # Auth is handled by dependencies or middleware in production
    # For now, we manually verify the token to provide a robust example
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise APIError("Missing or invalid authorization header", code=ErrorCodes.UNAUTHORIZED, status=401)
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('sub')
    except jwt.ExpiredSignatureError:
        raise APIError("Token expired", code=ErrorCodes.TOKEN_EXPIRED, status=401)
    except jwt.InvalidTokenError:
        raise APIError("Invalid token", code=ErrorCodes.INVALID_TOKEN, status=401)
        
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, name, company, role, created_at
            FROM users
            WHERE id = $1
            """,
            user_id
        )
    
    if not user:
        raise APIError("User not found", code=ErrorCodes.USER_NOT_FOUND, status=404)
    
    # Return dict with role (defaults to client if None due to migration)
    user_dict = dict(user)
    if not user_dict.get('role'):
        user_dict['role'] = 'client'
        
    return user_dict

    return dict(user)
