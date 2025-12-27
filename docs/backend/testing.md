# 🧪 Testing

**Versión**: 1.0  
**Nivel**: Beginner-friendly 🟢

---

## 🎯 Estrategia de Testing

Samplit usa una estrategia de testing en capas:

```
                    ┌───────────────────┐
                    │    E2E Tests      │  ← Playwright (browser)
                    │  (Pocos, lentos)  │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Integration Tests │  ← API endpoints
                    │   (Medianos)      │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │   Unit Tests      │  ← Funciones individuales
                    │ (Muchos, rápidos) │
                    └───────────────────┘
```

---

## 📁 Estructura

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartidos
├── test_auth.py             # Tests de autenticación
├── test_experiments.py      # Tests de experimentos
├── test_analytics.py        # Tests de analytics
├── test_blog.py             # Tests del blog
├── integration/
│   └── test_full_flow.py    # Flujo completo
└── unit/
    └── test_allocators.py   # Unit tests puros
```

---

## ⚙️ Configuración

### pytest.ini
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### conftest.py (fixtures)
```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    """Cliente HTTP para tests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(client):
    """Headers con token de autenticación."""
    # Login
    response = await client.post("/api/v1/auth/login", data={
        "username": "test@test.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

---

## 📝 Ejemplos de Tests

### Test de Autenticación
```python
# tests/test_auth.py

@pytest.mark.asyncio
async def test_register_user(client):
    """Test registro de usuario."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "nuevo@test.com",
        "password": "password123",
        "full_name": "Test User"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nuevo@test.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_success(client):
    """Test login exitoso."""
    response = await client.post("/api/v1/auth/login", data={
        "username": "test@test.com",
        "password": "testpass123"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Test de Experimentos
```python
# tests/test_experiments.py

@pytest.mark.asyncio
async def test_create_experiment(client, auth_headers):
    """Test crear experimento."""
    response = await client.post(
        "/api/v1/experiments",
        headers=auth_headers,
        json={
            "name": "Test Experiment",
            "variants": [
                {"name": "Control", "content": {}, "is_control": True},
                {"name": "Variant B", "content": {}}
            ]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Experiment"
    assert data["status"] == "draft"

@pytest.mark.asyncio
async def test_start_experiment(client, auth_headers, experiment_id):
    """Test iniciar experimento."""
    response = await client.patch(
        f"/api/v1/experiments/{experiment_id}/status",
        headers=auth_headers,
        json={"status": "active"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "active"
```

### Test de Analytics
```python
# tests/test_analytics.py

@pytest.mark.asyncio
async def test_bayesian_analysis(client, auth_headers, active_experiment_id):
    """Test análisis Bayesiano."""
    response = await client.get(
        f"/api/v1/analytics/experiment/{active_experiment_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "bayesian_analysis" in data
    assert "variants" in data["bayesian_analysis"]
    assert "recommendations" in data
```

---

## 🚀 Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_auth.py

# Con coverage
pytest --cov=. --cov-report=html

# Verbose
pytest -v

# Solo tests marcados
pytest -m "not slow"
```

---

## 📊 Coverage Goal

| Componente | Target | Actual |
|------------|--------|--------|
| Services | 80% | - |
| Repositories | 70% | - |
| Routers | 60% | - |
| Utils | 90% | - |

---

## 🔑 Tips para Tests

1. **Usa fixtures** para datos compartidos
2. **Aísla tests** - cada uno debe poder correr solo
3. **Mockea externos** - DB, Redis, APIs externas
4. **Nombra descriptivamente** - `test_create_experiment_with_invalid_data_returns_422`
5. **Prioriza unit tests** - son rápidos y confiables

