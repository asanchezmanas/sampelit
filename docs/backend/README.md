# 📖 Documentación del Backend - Samplit

Documentación técnica completa de la arquitectura backend de la plataforma Samplit.

**Versión**: 1.0  
**Última actualización**: Diciembre 2024

---

## 📁 Estructura de Directorios

```
sampelit/
├── config/                 # Configuración de la aplicación
│   └── settings.py         # Variables de entorno y configuración
│
├── data_access/           # Capa de acceso a datos
│   ├── database.py        # Conexión PostgreSQL con asyncpg
│   └── repositories/      # Patrón Repository
│       ├── assignment_repository.py
│       ├── experiment_repository.py
│       ├── funnel_repository.py
│       ├── user_repository.py
│       └── variant_repository.py
│
├── database/              # Esquemas SQL
│   └── schema/
│       ├── schema_phase1_PRODUCTION_READY.sql
│       ├── schema_audit.sql
│       ├── schema_leads.sql
│       └── schema_integrations_PRODUCTION_READY.sql
│
├── engine/                # Motor de optimización
│   ├── core/
│   │   ├── allocators/    # Algoritmos de asignación
│   │   │   ├── bayesian.py    # Thompson Sampling
│   │   │   ├── sequential.py  # A/B clásico
│   │   │   └── _registry.py
│   │   └── math/          # Funciones matemáticas
│   └── state/             # Estado del experimento
│
├── infrastructure/        # Infraestructura transversal
│   ├── logging/           # Configuración de logs
│   └── monitoring/        # Métricas y monitoreo
│
├── integration/           # Integraciones externas
│   ├── email/             # Integración con emails
│   ├── proxy/             # Proxy para Visual Editor
│   └── web/               # Integraciones web
│       ├── shopify/       # OAuth Shopify
│       └── wordpress/     # OAuth WordPress
│
├── orchestration/         # Lógica de negocio
│   ├── factories/         # Factory pattern
│   ├── interfaces/        # Interfaces abstractas
│   └── services/          # Servicios de aplicación
│       ├── analytics_service.py
│       ├── audit_service.py
│       ├── cache_service.py
│       ├── experiment_service.py
│       ├── funnel_service.py
│       ├── metrics_service.py
│       └── multi_element_service.py
│
├── public_api/            # API REST (FastAPI)
│   ├── dependencies.py    # Inyección de dependencias
│   ├── errors.py          # Manejo de errores
│   ├── middleware/        # Middlewares HTTP
│   ├── models/            # Modelos Pydantic (DTOs)
│   └── routers/           # Endpoints API
│       ├── analytics.py
│       ├── auth.py
│       ├── dashboard.py
│       ├── experiments.py
│       ├── funnels.py
│       ├── tracker.py
│       └── ... (20+ routers)
│
├── utils/                 # Utilidades
│   └── file_exporters.py  # Exportación CSV/Excel
│
├── scripts/               # Scripts de mantenimiento
│   ├── seed_demo_v1.py
│   ├── migrate_*.py
│   └── benchmark_cache.py
│
├── tests/                 # Tests automatizados
│   ├── conftest.py
│   ├── test_*.py
│   └── integration/
│
└── main.py               # Entry point de la aplicación
```

---

## 📚 Documentos Detallados

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura General](./architecture.md) | Overview de la arquitectura y patrones |
| [Configuración](./configuration.md) | Variables de entorno y settings |
| [Base de Datos](./database.md) | Esquema, índices y optimizaciones |
| [Repositorios](./repositories.md) | Capa de acceso a datos |
| [Servicios](./services.md) | Lógica de negocio |
| [API Reference](./api_reference.md) | Endpoints REST completos |
| [Motor de Optimización](./engine.md) | Algoritmos Bayesianos |
| [Integraciones](./integrations.md) | Shopify, WordPress, etc. |
| [Scripts](./scripts.md) | Scripts de mantenimiento |
| [Testing](./testing.md) | Estrategia de pruebas |

---

## 🔧 Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **Framework** | FastAPI | 0.100+ |
| **Python** | CPython | 3.9+ |
| **Base de Datos** | PostgreSQL | 13+ |
| **Driver DB** | asyncpg | 0.27+ |
| **Cache** | Redis (opcional) | 7.0+ |
| **Validación** | Pydantic | v2 |
| **Auth** | JWT (PyJWT) | - |

---

## 🚀 Quick Start

```bash
# 1. Clonar repositorio
git clone https://github.com/yourusername/sampelit.git
cd sampelit

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Iniciar servidor
python main.py
```

La API estará disponible en `http://localhost:8000`  
Documentación Swagger: `http://localhost:8000/docs`

---

## 📐 Principios de Arquitectura

1. **Clean Architecture**: Separación clara de capas (API → Services → Repositories → DB)
2. **Dependency Injection**: Via FastAPI `Depends()`
3. **Repository Pattern**: Abstracción de acceso a datos
4. **Factory Pattern**: Creación de servicios complejos
5. **Circuit Breaker**: Resiliencia en conexiones a DB
6. **Async/Await**: Todo el stack es asíncrono

