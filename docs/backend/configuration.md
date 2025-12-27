# ⚙️ Configuración del Backend

**Versión**: 1.0  
**Última actualización**: Diciembre 2024

---

## Archivo de Configuración

La configuración se centraliza en `config/settings.py` usando Pydantic Settings para validación automática.

---

## Variables de Entorno

### Base de Datos

| Variable | Tipo | Requerido | Descripción |
|----------|------|-----------|-------------|
| `DATABASE_URL` | string | ✅ | URL de conexión PostgreSQL |

**Formato:**
```
postgresql://user:password@host:port/database
```

**Ejemplo:**
```bash
DATABASE_URL=postgresql://samplit:secret@localhost:5432/samplit
```

---

### Redis (Cache)

| Variable | Tipo | Requerido | Descripción |
|----------|------|-----------|-------------|
| `REDIS_URL` | string | ❌ | URL de conexión Redis |
| `REDIS_ENABLED` | bool | ❌ | Activar cache Redis |

**Comportamiento:**
- Si Redis no está disponible, el sistema usa cache en PostgreSQL
- Redis mejora el rendimiento en producción

```bash
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
```

---

### Seguridad

| Variable | Tipo | Requerido | Descripción |
|----------|------|-----------|-------------|
| `SECRET_KEY` | string | ✅ | Clave para firmar JWT (mínimo 32 caracteres) |
| `JWT_ALGORITHM` | string | ❌ | Algoritmo JWT (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | ❌ | Duración del token (default: 30) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | ❌ | Duración refresh token (default: 7) |

**Generar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### Aplicación

| Variable | Tipo | Requerido | Default | Descripción |
|----------|------|-----------|---------|-------------|
| `ENVIRONMENT` | enum | ❌ | development | development/staging/production |
| `DEBUG` | bool | ❌ | false | Modo debug |
| `LOG_LEVEL` | string | ❌ | INFO | DEBUG/INFO/WARNING/ERROR |
| `API_V1_PREFIX` | string | ❌ | /api/v1 | Prefijo de la API |
| `CORS_ORIGINS` | string | ❌ | * | Orígenes CORS (comma-separated) |

---

### Integraciones (Opcional)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `SHOPIFY_API_KEY` | string | OAuth Shopify |
| `SHOPIFY_API_SECRET` | string | OAuth Shopify |
| `WORDPRESS_CLIENT_ID` | string | OAuth WordPress |
| `WORDPRESS_CLIENT_SECRET` | string | OAuth WordPress |
| `STRIPE_SECRET_KEY` | string | Pagos con Stripe |
| `STRIPE_WEBHOOK_SECRET` | string | Webhooks Stripe |
| `SENDGRID_API_KEY` | string | Envío de emails |

---

## Archivos de Ejemplo

### .env.example

```bash
# ===========================
# DATABASE
# ===========================
DATABASE_URL=postgresql://samplit:password@localhost:5432/samplit

# ===========================
# REDIS (Optional)
# ===========================
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true

# ===========================
# SECURITY
# ===========================
SECRET_KEY=your-super-secret-key-at-least-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===========================
# APPLICATION
# ===========================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ===========================
# INTEGRATIONS (Optional)
# ===========================
# SHOPIFY_API_KEY=
# SHOPIFY_API_SECRET=
# STRIPE_SECRET_KEY=
# SENDGRID_API_KEY=
```

---

## Clase Settings

```python
# config/settings.py

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "*"
    
    # Validators
    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if v == "your-super-secret-key":
            raise ValueError("Change default SECRET_KEY in production")
        return v
    
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
```

---

## Helper Functions

```python
# Obtener instancia de settings
from config.settings import settings

# Helpers para ambiente
from config.settings import is_development, is_production, is_staging

if is_production():
    # Configuración específica de producción
    pass
```

---

## Validación al Iniciar

El sistema valida la configuración al importar el módulo:

```python
def validate_settings():
    """
    Validaciones críticas al inicio:
    1. SECRET_KEY no es el default
    2. DATABASE_URL es válida
    3. Variables requeridas están presentes
    """
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        if "localhost" in settings.DATABASE_URL:
            raise ValueError("Production cannot use localhost database")
```

---

## Configuración por Ambiente

### Development

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=<strong-production-key>
```

---

## Connection Pooling

La configuración del pool de conexiones:

```python
# data_access/database.py

pool = await asyncpg.create_pool(
    dsn=settings.DATABASE_URL,
    min_size=5,      # Conexiones mínimas
    max_size=20,     # Conexiones máximas
    max_inactive_connection_lifetime=300,  # 5 minutos
    command_timeout=60
)
```

