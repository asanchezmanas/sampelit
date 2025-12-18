# config/settings.py

"""
Application Settings - VERSIÓN COMPLETA
✅ Incluye configuración para instalación simple de 1 línea
"""

from pydantic import BaseSettings, Field, validator
from typing import List, Optional
import os
from enum import Enum


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # ════════════════════════════════════════════════════════════════════════
    # APPLICATION
    # ════════════════════════════════════════════════════════════════════════
    
    APP_NAME: str = "Samplit A/B Testing"
    APP_VERSION: str = "2.0.0"  # ✅ Updated version
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="ENVIRONMENT"
    )
    DEBUG: bool = Field(
        default=False,
        env="DEBUG"
    )
    
    # ════════════════════════════════════════════════════════════════════════
    # ✅ NUEVO: CDN & TRACKER URLS
    # ════════════════════════════════════════════════════════════════════════
    
    CDN_URL: str = Field(
        default="https://cdn.samplit.com",
        env="CDN_URL",
        description="CDN URL for tracker script"
    )
    
    API_BASE_URL: str = Field(
        default="https://api.samplit.com",
        env="API_BASE_URL",
        description="Base URL for API endpoints"
    )
    
    TRACKER_SCRIPT_PATH: str = "/t.js"  # Simple tracker script
    
    # ════════════════════════════════════════════════════════════════════════
    # SECURITY
    # ════════════════════════════════════════════════════════════════════════
    
    # CORS Origins
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: _parse_cors_origins()
    )
    
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Secret keys
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM_ENCRYPTION_KEY: str = Field(..., env="ALGORITHM_ENCRYPTION_KEY")
    
    # JWT
    JWT_SECRET: Optional[str] = Field(None, env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    @validator('CORS_ORIGINS')
    def validate_cors_origins(cls, v, values):
        """Validate CORS configuration"""
        environment = values.get('ENVIRONMENT', Environment.DEVELOPMENT)
        
        if environment == Environment.PRODUCTION:
            if "*" in v:
                raise ValueError(
                    "CORS wildcard (*) not allowed in production. "
                    "Set CORS_ORIGINS environment variable with specific domains."
                )
            
            if not v or len(v) == 0:
                raise ValueError(
                    "CORS_ORIGINS must be set in production. "
                    "Example: CORS_ORIGINS=https://app.samplit.com,https://samplit.com"
                )
        
        elif environment == Environment.STAGING:
            if "*" in v:
                import logging
                logging.warning(
                    "⚠️  CORS wildcard (*) detected in staging. "
                    "Consider using specific domains."
                )
        
        return v
    
    # ════════════════════════════════════════════════════════════════════════
    # DATABASE
    # ════════════════════════════════════════════════════════════════════════
    
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20
    DB_POOL_MAX_QUERIES: int = 50000
    DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME: float = 300.0
    
    # ════════════════════════════════════════════════════════════════════════
    # REDIS
    # ════════════════════════════════════════════════════════════════════════
    
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    REDIS_POOL_MIN_SIZE: int = 5
    REDIS_POOL_MAX_SIZE: int = 20
    
    # Redis auto-detection thresholds
    REDIS_AUTO_ENABLE_THRESHOLD: int = 1000  # req/min
    REDIS_AUTO_DISABLE_THRESHOLD: int = 500  # req/min
    
    # ════════════════════════════════════════════════════════════════════════
    # RATE LIMITING
    # ════════════════════════════════════════════════════════════════════════
    
    # Tracker API rate limits (PUBLIC endpoints)
    RATE_LIMIT_TRACKER_PER_TOKEN: int = 1000  # requests per minute
    RATE_LIMIT_TRACKER_PER_IP: int = 2000  # requests per minute
    RATE_LIMIT_TRACKER_LIST: int = 100  # requests per minute
    
    # Admin API rate limits
    RATE_LIMIT_ADMIN_PER_USER: int = 100  # requests per minute
    
    # ════════════════════════════════════════════════════════════════════════
    # THOMPSON SAMPLING
    # ════════════════════════════════════════════════════════════════════════
    
    THOMPSON_ALPHA_PRIOR: float = 1.0
    THOMPSON_BETA_PRIOR: float = 1.0
    THOMPSON_MIN_SAMPLES: int = 100
    
    # Monte Carlo simulation
    MONTE_CARLO_SAMPLES: int = 10000
    MONTE_CARLO_ADAPTIVE: bool = True
    
    # ════════════════════════════════════════════════════════════════════════
    # METRICS & MONITORING
    # ════════════════════════════════════════════════════════════════════════
    
    METRICS_CHECK_INTERVAL: int = 300  # seconds (5 minutes)
    METRICS_AUTO_SCALE_ENABLED: bool = True
    
    # Health check
    HEALTH_CHECK_INTERVAL: int = 60  # seconds
    
    # ════════════════════════════════════════════════════════════════════════
    # INTEGRATIONS
    # ════════════════════════════════════════════════════════════════════════
    
    # WordPress
    WORDPRESS_OAUTH_CLIENT_ID: Optional[str] = Field(None, env="WORDPRESS_OAUTH_CLIENT_ID")
    WORDPRESS_OAUTH_CLIENT_SECRET: Optional[str] = Field(None, env="WORDPRESS_OAUTH_CLIENT_SECRET")
    WORDPRESS_OAUTH_REDIRECT_URI: Optional[str] = Field(None, env="WORDPRESS_OAUTH_REDIRECT_URI")
    
    # Shopify
    SHOPIFY_API_KEY: Optional[str] = Field(None, env="SHOPIFY_API_KEY")
    SHOPIFY_API_SECRET: Optional[str] = Field(None, env="SHOPIFY_API_SECRET")
    SHOPIFY_SCOPES: str = "read_products,write_products,read_script_tags,write_script_tags"
    
    # ════════════════════════════════════════════════════════════════════════
    # LOGGING
    # ════════════════════════════════════════════════════════════════════════
    
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    LOG_FORMAT: str = "json"  # or "text"
    
    # ════════════════════════════════════════════════════════════════════════
    # API
    # ════════════════════════════════════════════════════════════════════════
    
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_ENABLED: bool = Field(
        default=True,
        env="API_DOCS_ENABLED"
    )
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # ════════════════════════════════════════════════════════════════════════
    # FEATURE FLAGS
    # ════════════════════════════════════════════════════════════════════════
    
    FEATURE_VISUAL_EDITOR: bool = True
    FEATURE_ANALYTICS_EXPORT: bool = True
    FEATURE_WEBHOOK_VERIFICATION: bool = True
    FEATURE_SIMPLE_INSTALLATION: bool = True  # ✅ NUEVO
    
    # ════════════════════════════════════════════════════════════════════════
    # FILE UPLOAD
    # ════════════════════════════════════════════════════════════════════════
    
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".png", ".gif", ".webp"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def _parse_cors_origins() -> List[str]:
    """Parse CORS origins from environment variable"""
    cors_env = os.getenv("CORS_ORIGINS", "")
    
    if not cors_env:
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "development":
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000"
            ]
        
        elif environment == "staging":
            return [
                "https://staging.samplit.com",
                "https://staging-app.samplit.com"
            ]
        
        else:
            # Production: MUST be set explicitly
            return []
    
    # Parse comma-separated list
    origins = [origin.strip() for origin in cors_env.split(",")]
    origins = [o for o in origins if o]
    
    return origins


# ════════════════════════════════════════════════════════════════════════════
# SETTINGS INSTANCE
# ════════════════════════════════════════════════════════════════════════════

_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance (singleton)"""
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings


# ════════════════════════════════════════════════════════════════════════════
# EXAMPLE .env FILE
# ════════════════════════════════════════════════════════════════════════════

"""
Example .env file for production:

# Environment
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM_ENCRYPTION_KEY=your-encryption-key-here
JWT_SECRET=your-jwt-secret-here

# CORS - Specific domains only
CORS_ORIGINS=https://app.samplit.com,https://samplit.com,https://www.samplit.com

# ✅ CDN & API URLs
CDN_URL=https://cdn.samplit.com
API_BASE_URL=https://api.samplit.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis (optional but recommended)
REDIS_URL=redis://user:pass@host:6379/0

# Integrations
WORDPRESS_OAUTH_CLIENT_ID=your-client-id
WORDPRESS_OAUTH_CLIENT_SECRET=your-client-secret
WORDPRESS_OAUTH_REDIRECT_URI=https://app.samplit.com/integrations/wordpress/callback

SHOPIFY_API_KEY=your-api-key
SHOPIFY_API_SECRET=your-api-secret

# Logging
LOG_LEVEL=INFO

# API
API_DOCS_ENABLED=false  # Disable in production for security
"""

"""
Example .env file for development:

# Environment
ENVIRONMENT=development
DEBUG=true

# Security
SECRET_KEY=dev-secret-key-not-for-production
ALGORITHM_ENCRYPTION_KEY=dev-encryption-key
JWT_SECRET=dev-jwt-secret

# CORS - Localhost for development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ✅ CDN & API URLs (local)
CDN_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://localhost:5432/samplit_dev

# Redis (optional in dev)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG

# API
API_DOCS_ENABLED=true
"""
