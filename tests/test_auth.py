import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_register_success(self):
        """Test user registration with valid data"""
        response = client.post("/api/v1/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["success"] is True
    
    def test_register_invalid_email(self):
        """Test registration fails with invalid email"""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "Pass123!",
            "full_name": "Test User"
        })
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self):
        """Test registration fails with weak password"""
        response = client.post("/api/v1/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "weak",
            "full_name": "Test User"
        })
        # Should fail validation or return error
        assert response.status_code in [400, 422]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        email = f"login_{uuid.uuid4()}@example.com"
        password = "LoginPass123!"
        
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Login User"
        })
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
    
    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """Test login fails with missing fields"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com"
            # Missing password
        })
        assert response.status_code == 422
