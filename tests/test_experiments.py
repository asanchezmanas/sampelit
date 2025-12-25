import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

class TestExperiments:
    """Experiment endpoint tests"""
    
    def test_list_experiments_unauthorized(self):
        """Test listing experiments without auth fails"""
        response = client.get("/api/v1/experiments")
        assert response.status_code == 401
    
    def test_list_experiments_authorized(self, auth_headers):
        """Test listing experiments with auth"""
        response = client.get("/api/v1/experiments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_create_experiment_success(self, auth_headers):
        """Test experiment creation with valid data"""
        response = client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": f"Test Experiment {uuid.uuid4()}",
                "url": "https://example.com",
                "elements": [
                    {
                        "name": "Headline",
                        "selector": {"type": "css", "selector": "h1"},
                        "element_type": "text",
                        "original_content": {"text": "Original Headline"},
                        "variants": [
                            {"text": "Variant A"},
                            {"text": "Variant B"}
                        ]
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or ("data" in data and "id" in data["data"])
    
    def test_create_experiment_invalid_url(self, auth_headers):
        """Test experiment creation fails with invalid URL"""
        response = client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "Invalid URL Test",
                "url": "not-a-url",
                "elements": []
            }
        )
        assert response.status_code in [400, 422]
    
    def test_create_experiment_no_variants(self, auth_headers):
        """Test experiment creation fails without variants"""
        response = client.post(
            "/api/v1/experiments",
            headers=auth_headers,
            json={
                "name": "No Variants Test",
                "url": "https://example.com",
                "elements": [
                    {
                        "name": "Element",
                        "selector": {"type": "css", "selector": ".test"},
                        "element_type": "text",
                        "original_content": {"text": "Original"},
                        "variants": []  # Empty variants
                    }
                ]
            }
        )
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_get_experiment_unauthorized(self):
        """Test getting experiment without auth fails"""
        response = client.get("/api/v1/experiments/some-id")
        assert response.status_code == 401
    
    def test_get_nonexistent_experiment(self, auth_headers):
        """Test getting nonexistent experiment returns 404"""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/experiments/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
