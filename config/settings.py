# config/settings.py

from pydantic import BaseSettings, validator
from typing import Optional, List
import os

class Settings(BaseSettings):
    """
    Application settings
    
    All sensitive configuration loaded from environment
    """
    
    # ============================================
    # APP SETTINGS
    # ============================================
    APP_NAME: str = "Samplit"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"  # development, staging, production
    DEBUG: bool = False
    
    # ============================================
    # SUPABASE (Database + Auth)
    # ============================================
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # Public key for frontend
    SUPABASE_SERVICE_KEY: str  # Secret key for backend
    SUPABASE_JWT_SECRET: str  # For JWT verification
    
    @validator('SUPABASE_URL')
    def validate_supabase_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('SUPABASE_URL must start with https://')
        return v
    
    # ============================================
    # DATABASE
    # ============================================
    DATABASE_URL: str
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        # Supabase needs postgresql:// not postgres://
        if v.startswith('postgres://'):
            v = v.replace('postgres://', 'postgresql://', 1)
        return v
    
    # ============================================
    # SECURITY
    # ============================================
    # Secret para cifrar estado de algoritmos
    ALGORITHM_STATE_SECRET: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Configurar en producción
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @validator('ALGORITHM_STATE_SECRET')
    def validate_algorithm_secret(cls, v):
        if len(v) < 32:
            raise ValueError('ALGORITHM_STATE_SECRET must be at least 32 characters')
        return v
    
    # ============================================
    # OPTIMIZATION ENGINE
    # ============================================
    # Configuración de algoritmos (valores ofuscados)
    OPT_DEFAULT_STRATEGY: str = "adaptive"
    OPT_MIN_SAMPLES: int = 30
    OPT_CONFIDENCE_THRESHOLD: float = 0.95
    OPT_EXPLORATION_RATE: float = 0.1
    OPT_EXPLORATION_DECAY: float = 0.995
    
    # ============================================
    # API CONFIGURATION
    # ============================================
    API_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 1000  # requests per hour
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # ============================================
    # FEATURES FLAGS
    # ============================================
    ENABLE_FUNNEL_OPTIMIZATION: bool = True
    ENABLE_EMAIL_OPTIMIZATION: bool = True
    ENABLE_PUSH_OPTIMIZATION: bool = True
    
    # ============================================
    # PROXY CONFIGURATION
    # ============================================
    PROXY_ENABLED: bool = True
    PROXY_TIMEOUT: int = 30  # seconds
    BASE_URL: str = ""  # Your domain, e.g., "https://samplit.com"
    
    # ============================================
    # CACHE CONFIGURATION
    # ============================================
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes
    REDIS_URL: Optional[str] = None  # For future Redis integration
    
    # ============================================
    # VISUAL EDITOR
    # ============================================
    VISUAL_EDITOR_ENABLED: bool = True
    ALLOW_IFRAME_EMBEDDING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

settings = get_settings()
