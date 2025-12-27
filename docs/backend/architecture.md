# 🏗 Arquitectura del Backend

**Versión**: 1.0  
**Última actualización**: Diciembre 2024

---

## Overview

Samplit utiliza una arquitectura de capas (Clean Architecture) que separa claramente las responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION                           │
│    public_api/routers/ + public_api/models/                │
│    FastAPI endpoints, Pydantic DTOs                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION SERVICES                      │
│              orchestration/services/                        │
│    ExperimentService, AnalyticsService, AuditService       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA ACCESS                             │
│              data_access/repositories/                      │
│    ExperimentRepository, VariantRepository, etc.           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                         │
│        data_access/database.py + infrastructure/            │
│    DatabaseManager, CircuitBreaker, Logging                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       EXTERNAL                              │
│              PostgreSQL + Redis + S3                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes Principales

### 1. main.py (Entry Point)

Punto de entrada de la aplicación FastAPI. Responsable de:

- **Lifespan Management**: Inicialización y cierre de conexiones DB
- **Middleware Stack**:
  - CORS (Cross-Origin Resource Sharing)
  - TrustedHostMiddleware (seguridad)
  - GZipMiddleware (compresión)
  - Request timing headers
  - Security headers
- **Router Registration**: Monta todos los routers con sus prefijos
- **Exception Handlers**: Manejo global de errores
- **Static Files**: Sirve archivos estáticos del frontend

```python
# Estructura del lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.initialize()
    yield
    # Shutdown
    await db_manager.disconnect()
```

---

### 2. public_api/ (Capa de Presentación)

#### 2.1 Routers (`public_api/routers/`)

| Router | Prefix | Descripción |
|--------|--------|-------------|
| `auth.py` | `/auth` | Login, registro, JWT tokens |
| `experiments.py` | `/experiments` | CRUD de experimentos |
| `analytics.py` | `/analytics` | Análisis estadístico |
| `dashboard.py` | `/dashboard` | Métricas agregadas |
| `tracker.py` | `/tracker` | SDK tracking (assign/convert) |
| `funnels.py` | `/funnels` | Embudos de conversión |
| `audit.py` | `/audit` | Trail de auditoría |
| `installations.py` | `/installations` | Instalación de snippets |
| `visual_editor.py` | `/visual-editor` | Editor visual (proxy) |
| `integrations.py` | `/integrations` | OAuth externas |
| `subscriptions.py` | `/subscriptions` | Planes y billing |
| `simulator.py` | `/simulate` | Demo pública |

#### 2.2 Models (`public_api/models/`)

Modelos Pydantic v2 para validación y serialización:

| Archivo | Contenido |
|---------|-----------|
| `experiment_models.py` | `ExperimentCreate`, `ExperimentResponse`, etc. |
| `funnel_models.py` | `FunnelCreate`, `NodeCreateRequest`, etc. |
| `common.py` | Modelos base compartidos |
| `tracker.py` | `AssignRequest`, `ConvertRequest` |

#### 2.3 Dependencies (`public_api/dependencies.py`)

Inyección de dependencias:

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validar JWT y retornar usuario
    
async def get_experiment_service():
    # Crear e inyectar ExperimentService
```

#### 2.4 Middleware (`public_api/middleware/`)

- Rate limiting
- Request logging
- Error tracking

---

### 3. orchestration/ (Capa de Servicios)

#### 3.1 Services (`orchestration/services/`)

| Servicio | Responsabilidad |
|----------|-----------------|
| `ExperimentService` | CRUD experimentos, asignación de usuarios |
| `AnalyticsService` | Análisis Bayesiano, Monte Carlo |
| `AuditService` | Hash chain, trail de decisiones |
| `CacheService` | Cache en memoria/Redis |
| `FunnelService` | Lógica de embudos |
| `MetricsService` | Cálculo de métricas |
| `MultiElementService` | Experimentos multi-elemento |

**Ejemplo ExperimentService:**

```python
class ExperimentService:
    def __init__(self, db_pool, experiment_repo, variant_repo, ...):
        self.db_pool = db_pool
        self.experiment_repo = experiment_repo
        
    async def create_experiment(self, name, variants_data, user_id, ...):
        # Transacción atómica
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                exp = await self.experiment_repo.create(...)
                for v in variants_data:
                    await self.variant_repo.create(...)
        return exp
```

#### 3.2 Factories (`orchestration/factories/`)

Factory para crear servicios con todas sus dependencias.

---

### 4. data_access/ (Capa de Datos)

#### 4.1 DatabaseManager (`data_access/database.py`)

```python
class DatabaseManager:
    """
    Features:
    - Connection pooling (asyncpg)
    - Retry with exponential backoff
    - Circuit breaker pattern
    - Automatic reconnection
    """
    
    async def initialize(self, retries=3):
        for attempt in range(retries):
            try:
                self.pool = await asyncpg.create_pool(...)
                return
            except Exception:
                await asyncio.sleep(2 ** attempt)
```

#### 4.2 Repositories (`data_access/repositories/`)

| Repository | Entidad |
|------------|---------|
| `ExperimentRepository` | Experimentos |
| `VariantRepository` | Variantes |
| `AssignmentRepository` | Asignaciones |
| `FunnelRepository` | Embudos |
| `UserRepository` | Usuarios |

**Patrón Repository:**

```python
class ExperimentRepository:
    def __init__(self, pool):
        self.pool = pool
    
    async def get_by_id(self, exp_id: str) -> dict:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM experiments WHERE id = $1", exp_id
            )
    
    async def create(self, data: dict) -> dict:
        # INSERT INTO experiments...
```

---

### 5. engine/ (Motor de Optimización)

#### 5.1 Allocators (`engine/core/allocators/`)

| Allocator | Algoritmo |
|-----------|-----------|
| `bayesian.py` | Thompson Sampling (Beta distribution) |
| `sequential.py` | A/B Testing clásico (round-robin) |
| `_explore.py` | Estrategias de exploración |

**Thompson Sampling:**

```python
def select_variant(variants):
    """
    Para cada variante:
    1. alpha = successes + 1
    2. beta = failures + 1
    3. sample ~ Beta(alpha, beta)
    4. Seleccionar variante con mayor sample
    """
    samples = []
    for v in variants:
        sample = np.random.beta(v.alpha, v.beta)
        samples.append((v.id, sample))
    return max(samples, key=lambda x: x[1])
```

---

### 6. config/ (Configuración)

#### settings.py

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis (optional)
    REDIS_URL: Optional[str]
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
```

---

## Flujo de una Request

```
1. HTTP Request → FastAPI Router
2. Router → Dependency Injection (get_current_user, get_service)
3. Service → Repository → Database
4. Database → Repository → Service
5. Service → Pydantic Model → JSON Response
```

**Ejemplo: GET /api/v1/experiments/{id}**

```python
@router.get("/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
    service: ExperimentService = Depends(get_experiment_service)
):
    experiment = await service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    return ExperimentResponse(**experiment)
```

---

## Patrones de Diseño

### 1. Repository Pattern
Abstrae el acceso a datos detrás de una interfaz limpia.

### 2. Dependency Injection
FastAPI's `Depends()` para inyección automática.

### 3. Factory Pattern
`ServiceFactory` para crear servicios con dependencias complejas.

### 4. Circuit Breaker
Protege contra fallos en cascada con `CircuitBreaker` class.

### 5. Strategy Pattern
Diferentes allocators implementan la misma interfaz.

---

## Consideraciones de Seguridad

1. **JWT Tokens**: Autenticación stateless
2. **Password Hashing**: bcrypt
3. **RLS (Row Level Security)**: Usuarios solo ven sus datos
4. **Input Validation**: Pydantic v2 strict mode
5. **Error Obfuscation**: Códigos internos ocultos en producción
6. **CORS**: Orígenes permitidos configurables
7. **Rate Limiting**: Protección contra abuso

