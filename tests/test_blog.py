import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestBlog:
    """Blog endpoint tests"""
    
    def test_list_posts(self):
        """Test blog post listing"""
        response = client.get("/api/v1/blog")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_list_posts_pagination(self):
        """Test blog pagination"""
        response = client.get("/api/v1/blog?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5
    
    def test_get_post_by_slug(self):
        """Test getting single post"""
        response = client.get("/api/v1/blog/copy-testing-guide")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "content" in data
        assert data["metadata"]["slug"] == "copy-testing-guide"
    
    def test_get_nonexistent_post(self):
        """Test 404 for missing post"""
        response = client.get("/api/v1/blog/nonexistent-slug-12345")
        assert response.status_code == 404
    
    def test_filter_by_category(self):
        """Test category filtering"""
        response = client.get("/api/v1/blog?category=ab-testing-fundamentals")
        assert response.status_code == 200
        data = response.json()
        # All returned items should be in the specified category
        for item in data["items"]:
            assert item["category"] == "ab-testing-fundamentals"
    
    def test_filter_by_invalid_category(self):
        """Test filtering by nonexistent category returns empty"""
        response = client.get("/api/v1/blog?category=nonexistent-category")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
    
    def test_post_metadata_structure(self):
        """Test post metadata has required fields"""
        response = client.get("/api/v1/blog/copy-testing-guide")
        assert response.status_code == 200
        metadata = response.json()["metadata"]
        
        required_fields = ["title", "slug", "category", "author", "date", "excerpt", "keywords"]
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
    
    def test_post_content_is_html(self):
        """Test post content is rendered as HTML"""
        response = client.get("/api/v1/blog/copy-testing-guide")
        assert response.status_code == 200
        content = response.json()["content"]
        
        # Should contain HTML tags
        assert "<h1>" in content or "<h2>" in content
        assert "<p>" in content
