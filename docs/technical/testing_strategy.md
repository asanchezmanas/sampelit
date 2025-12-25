# Testing Guide - Samplit Application

Complete testing strategy and implementation guide for all application components.

---

## Testing Stack

### Backend Testing
- **Framework**: `pytest` 5.0+
- **Async Support**: `pytest-asyncio`
- **HTTP Mocking**: `httpx` (TestClient)
- **Database**: `pytest-postgresql` or in-memory SQLite
- **Coverage**: `pytest-cov`

### Frontend Testing
- **Unit Tests**: Jest (if needed)
- **E2E Tests**: Playwright or Cypress
- **Manual Testing**: Browser DevTools

---

## 1. Backend Unit Tests

### Authentication Tests
**File**: `tests/test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuth:
    def test_register_success(self):
        """Test user registration with valid data"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        assert response.status_code == 200
        assert "token" in response.json()
    
    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email"""
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass123!",
            "full_name": "User One"
        })
        
        # Duplicate attempt
        response = client.post("/api/v1/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass456!",
            "full_name": "User Two"
        })
        assert response.status_code == 400
    
    def test_login_success(self):
        """Test login with valid credentials"""
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "password": "Pass123!",
            "full_name": "Login User"
        })
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "Pass123!"
        })
        assert response.status_code == 200
        assert "token" in response.json()
    
    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
```

### Experiment Tests
**File**: `tests/test_experiments.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_token():
    """Get authentication token for tests"""
    response = client.post("/api/v1/auth/register", json={
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "Pass123!",
        "full_name": "Test User"
    })
    return response.json()["token"]

class TestExperiments:
    def test_create_experiment(self, auth_token):
        """Test experiment creation"""
        response = client.post(
            "/api/v1/experiments",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Homepage Test",
                "url": "https://example.com",
                "elements": [
                    {
                        "name": "Headline",
                        "selector": {"type": "css", "selector": "h1"},
                        "element_type": "text",
                        "original_content": {"text": "Original"},
                        "variants": [
                            {"text": "Variant A"},
                            {"text": "Variant B"}
                        ]
                    }
                ]
            }
        )
        assert response.status_code == 200
        assert "id" in response.json()
    
    def test_list_experiments(self, auth_token):
        """Test listing user's experiments"""
        response = client.get(
            "/api/v1/experiments",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "items" in response.json()
    
    def test_get_experiment_unauthorized(self):
        """Test accessing experiment without auth fails"""
        response = client.get("/api/v1/experiments/some-id")
        assert response.status_code == 401
```

### Analytics Tests
**File**: `tests/test_analytics.py`

```python
import pytest
from orchestration.services.analytics_service import AnalyticsService

class TestAnalyticsService:
    @pytest.mark.asyncio
    async def test_bayesian_analysis(self):
        """Test Bayesian analysis with sample data"""
        service = AnalyticsService()
        
        variants = [
            {
                'id': 'var-1',
                'name': 'Control',
                'total_allocations': 1000,
                'total_conversions': 100
            },
            {
                'id': 'var-2',
                'name': 'Variant A',
                'total_allocations': 1000,
                'total_conversions': 120
            }
        ]
        
        result = await service.analyze_experiment('test-exp', variants)
        
        assert result['variant_count'] == 2
        assert result['total_allocations'] == 2000
        assert 'bayesian_analysis' in result
        assert 'winner' in result['bayesian_analysis']
    
    def test_confidence_interval(self):
        """Test Wilson confidence interval calculation"""
        service = AnalyticsService()
        
        lower, upper = service._calculate_confidence_interval(
            conversions=100,
            allocations=1000,
            confidence=0.95
        )
        
        assert 0 <= lower <= upper <= 1
        assert lower < 0.1  # 100/1000 = 0.1
        assert upper > 0.1
```

### Audit Trail Tests
**File**: `tests/test_audit.py`

```python
import pytest
from orchestration.services.audit_service import AuditService
from datetime import datetime, timezone
import uuid

class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_decision(self, db_manager):
        """Test decision logging"""
        service = AuditService(db_manager)
        
        audit_id = await service.log_decision(
            experiment_id=uuid.uuid4(),
            visitor_id="visitor_123",
            selected_variant_id=uuid.uuid4(),
            assignment_id=uuid.uuid4(),
            segment_key="default"
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_conversion(self, db_manager):
        """Test conversion logging"""
        service = AuditService(db_manager)
        
        # Log decision first
        assignment_id = uuid.uuid4()
        await service.log_decision(
            experiment_id=uuid.uuid4(),
            visitor_id="visitor_123",
            selected_variant_id=uuid.uuid4(),
            assignment_id=assignment_id
        )
        
        # Log conversion
        result = await service.log_conversion(
            assignment_id=assignment_id,
            conversion_value=49.99
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_chain_integrity(self, db_manager):
        """Test hash chain integrity verification"""
        service = AuditService(db_manager)
        experiment_id = uuid.uuid4()
        
        # Create chain of decisions
        for i in range(5):
            await service.log_decision(
                experiment_id=experiment_id,
                visitor_id=f"visitor_{i}",
                selected_variant_id=uuid.uuid4(),
                assignment_id=uuid.uuid4()
            )
        
        # Verify integrity
        result = await service.verify_chain_integrity(experiment_id)
        
        assert result['is_valid'] is True
        assert result['total_checked'] == 5
```

### Blog Tests
**File**: `tests/test_blog.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestBlog:
    def test_list_posts(self):
        """Test blog post listing"""
        response = client.get("/api/v1/blog")
        assert response.status_code == 200
        assert "items" in response.json()
    
    def test_get_post_by_slug(self):
        """Test getting single post"""
        response = client.get("/api/v1/blog/copy-testing-guide")
        assert response.status_code == 200
        assert "metadata" in response.json()
        assert "content" in response.json()
    
    def test_get_nonexistent_post(self):
        """Test 404 for missing post"""
        response = client.get("/api/v1/blog/nonexistent-slug")
        assert response.status_code == 404
    
    def test_filter_by_category(self):
        """Test category filtering"""
        response = client.get("/api/v1/blog?category=ab-testing-fundamentals")
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["category"] == "ab-testing-fundamentals"
```

---

## 2. Integration Tests

### End-to-End Experiment Flow
**File**: `tests/integration/test_experiment_flow.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

class TestExperimentFlow:
    def test_complete_experiment_lifecycle(self):
        """Test full experiment creation → allocation → conversion flow"""
        
        # 1. Register user
        register_response = client.post("/api/v1/auth/register", json={
            "email": f"flow_{uuid.uuid4()}@example.com",
            "password": "Pass123!",
            "full_name": "Flow Test"
        })
        token = register_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create experiment
        exp_response = client.post("/api/v1/experiments", headers=headers, json={
            "name": "Integration Test",
            "url": "https://example.com",
            "elements": [{
                "name": "CTA",
                "selector": {"type": "css", "selector": ".cta"},
                "element_type": "text",
                "original_content": {"text": "Sign Up"},
                "variants": [{"text": "Get Started"}, {"text": "Try Free"}]
            }]
        })
        exp_id = exp_response.json()["id"]
        
        # 3. Start experiment
        client.patch(f"/api/v1/experiments/{exp_id}/status", 
                    headers=headers, 
                    json={"status": "running"})
        
        # 4. Allocate visitor
        allocation_response = client.post("/api/v1/tracker/allocate", json={
            "experiment_id": exp_id,
            "visitor_id": "test_visitor_123"
        })
        assignment = allocation_response.json()
        
        # 5. Record conversion
        conversion_response = client.post("/api/v1/tracker/convert", json={
            "assignment_id": assignment["assignment_id"],
            "value": 49.99
        })
        
        # 6. Get analytics
        analytics_response = client.get(
            f"/api/v1/analytics/experiment/{exp_id}",
            headers=headers
        )
        
        # Assertions
        assert exp_response.status_code == 200
        assert allocation_response.status_code == 200
        assert conversion_response.status_code == 200
        assert analytics_response.status_code == 200
        assert analytics_response.json()["total_conversions"] >= 1
```

---

## 3. Frontend E2E Tests

### Playwright Tests
**File**: `tests/e2e/test_visual_editor.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Visual Editor', () => {
  test('should load and proxy URL', async ({ page }) => {
    await page.goto('http://localhost:8000/static/visual-editor.html');
    
    // Enter URL
    await page.fill('input[placeholder*="URL"]', 'https://example.com');
    await page.click('button:has-text("Load")');
    
    // Wait for iframe
    await page.waitForSelector('iframe');
    
    // Verify iframe loaded
    const iframe = page.frameLocator('iframe');
    await expect(iframe.locator('body')).toBeVisible();
  });
  
  test('should select element and create variant', async ({ page }) => {
    await page.goto('http://localhost:8000/static/visual-editor.html');
    
    // Load page
    await page.fill('input[placeholder*="URL"]', 'https://example.com');
    await page.click('button:has-text("Load")');
    await page.waitForSelector('iframe');
    
    // Click element in iframe
    const iframe = page.frameLocator('iframe');
    await iframe.locator('h1').first().click();
    
    // Verify element selected
    await expect(page.locator('text=Selected Element')).toBeVisible();
    
    // Add variant
    await page.click('button:has-text("Add Variant")');
    await page.fill('input[placeholder*="variant text"]', 'New Headline');
    
    // Save experiment
    await page.fill('input[placeholder*="experiment name"]', 'E2E Test');
    await page.click('button:has-text("Save Experiment")');
    
    // Verify success
    await expect(page.locator('text=Experiment saved')).toBeVisible();
  });
});

test.describe('Blog', () => {
  test('should list blog posts', async ({ page }) => {
    await page.goto('http://localhost:8000/static/blog.html');
    
    // Wait for posts to load
    await page.waitForSelector('article');
    
    // Verify at least one post
    const posts = await page.locator('article').count();
    expect(posts).toBeGreaterThan(0);
  });
  
  test('should open blog post', async ({ page }) => {
    await page.goto('http://localhost:8000/static/blog.html');
    
    // Click first article
    await page.click('article a:has-text("Read article")');
    
    // Verify post page loaded
    await expect(page).toHaveURL(/blog-post\.html\?slug=/);
    await expect(page.locator('h1')).toBeVisible();
  });
});
```

---

## 4. Performance Tests

### Load Testing
**File**: `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class SamplitUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "Pass123!"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_experiments(self):
        """List experiments (most common action)"""
        self.client.get("/api/v1/experiments", headers=self.headers)
    
    @task(1)
    def get_analytics(self):
        """Get experiment analytics"""
        self.client.get("/api/v1/analytics/experiment/test-id", headers=self.headers)
    
    @task(2)
    def allocate_visitor(self):
        """Allocate visitor (high traffic endpoint)"""
        self.client.post("/api/v1/tracker/allocate", json={
            "experiment_id": "test-exp",
            "visitor_id": f"visitor_{self.environment.runner.user_count}"
        })
```

Run with: `locust -f tests/performance/locustfile.py --host=http://localhost:8000`

---

## 5. Database Tests

### Migration Tests
**File**: `tests/test_migrations.py`

```python
import pytest
from data_access.database import DatabaseManager

class TestMigrations:
    @pytest.mark.asyncio
    async def test_schema_audit_exists(self, db_manager):
        """Test audit trail table exists"""
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'algorithm_audit_trail'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_chain_function_exists(self, db_manager):
        """Test stored procedure exists"""
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_proc 
                    WHERE proname = 'verify_audit_chain'
                )
            """)
            assert result is True
```

---

## 6. Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
```

### conftest.py
```python
import pytest
import asyncio
from data_access.database import DatabaseManager

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_manager():
    """Provide database manager for tests"""
    db = DatabaseManager()
    await db.initialize()
    yield db
    await db.close()

@pytest.fixture
def clean_database(db_manager):
    """Clean database between tests"""
    async def _clean():
        async with db_manager.pool.acquire() as conn:
            await conn.execute("TRUNCATE experiments, users CASCADE")
    
    asyncio.run(_clean())
    yield
    asyncio.run(_clean())
```

---

## 7. Running Tests

### Install Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov httpx playwright locust
playwright install
```

### Run All Tests
```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=public_api --cov=orchestration --cov-report=html

# Integration tests only
pytest tests/integration/ -v

# E2E tests
playwright test

# Performance tests
locust -f tests/performance/locustfile.py
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 8. Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Auth | 90%+ |
| Experiments | 85%+ |
| Analytics | 80%+ |
| Audit Trail | 95%+ |
| Blog | 70%+ |
| Overall | 80%+ |
