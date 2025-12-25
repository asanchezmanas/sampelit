import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from main import app
import uuid

# ════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Provide FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def auth_token(client):
    """Get authentication token for tests"""
    email = f"test_{uuid.uuid4()}@example.com"
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test User"
    })
    if response.status_code == 200:
        return response.json()["token"]
    # If registration fails, try login
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "TestPass123!"
    })
    return response.json()["token"]

@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}
