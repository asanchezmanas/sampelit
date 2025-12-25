import pytest
import uuid

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_register_success(self, client):
        """Test user registration with valid data"""
        response = client.post("/api/v1/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        })
        if response.status_code != 200:
            print(f"DEBUG: Register Success failed: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["success"] is True
    
    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email"""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "Pass123!",
            "name": "Test User"
        })
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self, client):
        """Test registration fails with weak password"""
        response = client.post("/api/v1/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "weak",
            "name": "Test User"
        })
        # Should fail validation or return error
        assert response.status_code in [400, 422]
    
    def test_login_success(self, client):
        """Test login with valid credentials"""
        email = f"login_{uuid.uuid4()}@example.com"
        password = "LoginPass123!"
        
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": "Login User"
        })
        
        # Login
        response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code != 200:
            print(f"DEBUG: Login Success failed: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login fails with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        })
        if response.status_code != 401:
            print(f"Login Invalid Credentials failed: {response.status_code} - {response.text}")
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """Test login fails with missing fields"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com"
            # Missing password
        })
        assert response.status_code == 422
