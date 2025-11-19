# public-api/routers/auth.py

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from data_access.database import get_database, DatabaseManager
from config.settings import settings
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

router = APIRouter()

# Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field(None, max_length=255)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)

class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str
    name: str

# Helper functions
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

def create_token(user_id: str) -> str:
    """Create JWT token"""
    payload = {
        'sub': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(
        payload, 
        settings.SUPABASE_JWT_SECRET, 
        algorithm='HS256'
    )
    
    return token

# Endpoints
@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: DatabaseManager = Depends(get_database)
):
    """Register new user"""
    
    # Check if user exists
    async with db.pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            request.email.lower()
        )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    async with db.pool.acquire() as conn:
        user_id = await conn.fetchval(
            """
            INSERT INTO users (email, password_hash, name, company)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            request.email.lower(),
            password_hash,
            request.name,
            request.company
        )
    
    # Generate token
    token = create_token(str(user_id))
    
    return AuthResponse(
        token=token,
        user_id=str(user_id),
        email=request.email,
        name=request.name
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: DatabaseManager = Depends(get_database)
):
    """Login user"""
    
    # Get user
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, password_hash, name
            FROM users
            WHERE email = $1
            """,
            request.email.lower()
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_token(str(user['id']))
    
    return AuthResponse(
        token=token,
        user_id=str(user['id']),
        email=user['email'],
        name=user['name']
    )

@router.get("/me")
async def get_current_user_info(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Get current user info"""
    
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, name, company, created_at
            FROM users
            WHERE id = $1
            """,
            user_id
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return dict(user)


# Dependency for protected routes (moved from middleware/auth.py)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify JWT and return user_id"""
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=['HS256']
        )
        
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
