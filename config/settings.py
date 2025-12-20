# config/settings.py
# ✅ FIXED: Pydantic v2 compatibility + SECRET_KEY validation

import os
from typing import List
from enum import Enum

# ✅ FIXED: Pydantic v2 imports
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings
    
    ✅ FIXED: Compatible con Pydantic v2
    ✅ FIXED: SECRET_KEY con validación obligatoria
    """
    
    # ─────────────────────────────────────────────────────────────
    # Environment
    # ─────────────────────────────────────────────────────────────
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="ENVIRONMENT"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        ...,  # Required
        env="SECRET_KEY",
        min_length=32,
        description="Secret key for JWT encoding (min 32 chars)"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        env="ALGORITHM"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        ...,  # Required
        env="DATABASE_URL"
    )
    
    SUPABASE_SERVICE_KEY: str = Field(
        default="",
        env="SUPABASE_SERVICE_KEY"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Redis
    # ─────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    CACHE_TTL: int = Field(
        default=300,  # 5 minutes
        env="CACHE_TTL"
    )
    
    # ─────────────────────────────────────────────────────────────
    # API
    # ─────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        env="API_V1_PREFIX"
    )
    
    PROJECT_NAME: str = Field(
        default="Samplit A/B Testing API",
        env="PROJECT_NAME"
    )
    
    # ─────────────────────────────────────────────────────────────
    # CORS
    # ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8080",
        env="CORS_ORIGINS"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Experiment Defaults
    # ─────────────────────────────────────────────────────────────
    DEFAULT_SIGNIFICANCE_LEVEL: float = Field(
        default=0.05,
        env="DEFAULT_SIGNIFICANCE_LEVEL"
    )
    
    DEFAULT_MINIMUM_SAMPLE_SIZE: int = Field(
        default=100,
        env="DEFAULT_MINIMUM_SAMPLE_SIZE"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Thompson Sampling
    # ─────────────────────────────────────────────────────────────
    THOMPSON_ALPHA_PRIOR: float = Field(
        default=1.0,
        env="THOMPSON_ALPHA_PRIOR"
    )
    
    THOMPSON_BETA_PRIOR: float = Field(
        default=1.0,
        env="THOMPSON_BETA_PRIOR"
    )
    
    # ─────────────────────────────────────────────────────────────
    # Validators
    # ─────────────────────────────────────────────────────────────
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Valida que SECRET_KEY sea seguro
        
        ✅ NUEVO: Validación obligatoria de SECRET_KEY
        """
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long.\n"
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Evitar valores por defecto inseguros
        dangerous_values = {
            'changeme', 'default', 'secret', 'password', 
            'test', 'admin', '12345', 'secretkey'
        }
        
        if v.lower() in dangerous_values:
            raise ValueError(
                f"SECRET_KEY cannot be '{v}'.\n"
                f"This is a known insecure default value.\n"
                f"Generate a secure random key with:\n"
                f"  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Advertir si parece muy simple
        if len(set(v)) < 16:  # Menos de 16 caracteres únicos
            import warnings
            warnings.warn(
                "SECRET_KEY has low entropy (few unique characters). "
                "Consider using a more random value.",
                UserWarning
            )
        
        return v
    
    @field_validator('CORS_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v: str, info) -> List[str]:
        """
        Valida CORS origins
        
        ✅ FIXED: Pydantic v2 style validator con info.data
        """
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(',')]
        else:
            origins = v
        
        # En producción, advertir si se usa wildcard
        environment = info.data.get('ENVIRONMENT', Environment.DEVELOPMENT)
        if environment == Environment.PRODUCTION and '*' in origins:
            import warnings
            warnings.warn(
                "Using wildcard (*) in CORS_ORIGINS in PRODUCTION is insecure!",
                UserWarning
            )
        
        return origins
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Valida DATABASE_URL"""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        
        # Fix postgres:// to postgresql://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        
        if not (v.startswith("postgresql://") or v.startswith("postgres://")):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgres://"
            )
        
        return v
    
    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Valida REDIS_URL"""
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")
        return v
    
    # ─────────────────────────────────────────────────────────────
    # Config
    # ─────────────────────────────────────────────────────────────
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ═══════════════════════════════════════════════════════════════════════
# Global settings instance
# ═══════════════════════════════════════════════════════════════════════

def get_settings() -> Settings:
    """
    Get settings instance
    
    This function creates a new Settings instance each time it's called.
    For production, you might want to use lru_cache to cache the instance.
    """
    return Settings()


# Create settings instance
settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════════════

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.ENVIRONMENT == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production mode"""
    return settings.ENVIRONMENT == Environment.PRODUCTION


def is_staging() -> bool:
    """Check if running in staging mode"""
    return settings.ENVIRONMENT == Environment.STAGING


# ═══════════════════════════════════════════════════════════════════════
# Validation on import
# ═══════════════════════════════════════════════════════════════════════

def validate_settings():
    """
    Validate critical settings on import
    
    This ensures that the application won't start with invalid configuration.
    """
    issues = []
    
    # Check SECRET_KEY
    if len(settings.SECRET_KEY) < 32:
        issues.append(
            "❌ SECRET_KEY is too short (< 32 chars)\n"
            "   Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check DATABASE_URL
    if not settings.DATABASE_URL:
        issues.append("❌ DATABASE_URL is not set")
    
    # Production-specific checks
    if is_production():
        if '*' in settings.CORS_ORIGINS:
            issues.append("⚠️  CORS wildcard (*) is insecure in PRODUCTION")
        
        if settings.SECRET_KEY.lower() in {'changeme', 'default', 'test'}:
            issues.append("❌ SECRET_KEY is using default value in PRODUCTION")
    
    if issues:
        print("\n" + "=" * 70)
        print("  ⚠️  CONFIGURATION ISSUES DETECTED")
        print("=" * 70)
        for issue in issues:
            print(f"\n{issue}")
        print("\n" + "=" * 70)
        
        if is_production():
            raise ValueError("Cannot start application with configuration issues in PRODUCTION")


# Run validation on import
validate_settings()


# ═══════════════════════════════════════════════════════════════════════
# Export
# ═══════════════════════════════════════════════════════════════════════

__all__ = [
    'Settings',
    'settings',
    'get_settings',
    'Environment',
    'is_development',
    'is_production',
    'is_staging'
]
