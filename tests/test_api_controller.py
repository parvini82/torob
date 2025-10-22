"""Tests for the FastAPI API controller endpoints.

These tests verify the health check, root endpoint, and tag generation endpoint
behavior, including input validation and error handling.
"""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Health endpoint should return service status and metadata."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "service" in data and isinstance(data["service"], str)
    assert "version" in data and isinstance(data["version"], str)


def test_root_endpoint(client: TestClient):
    """Root endpoint should return API info and endpoints."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("service")
    assert "endpoints" in data and isinstance(data["endpoints"], dict)
    assert set(["health", "generate_tags", "docs", "metrics"]).issubset(
        data["endpoints"].keys()
    )


def test_generate_tags_requires_image_url(client: TestClient):
    """generate-tags should validate presence of image_url."""
    resp = client.post("/generate-tags", json={})
    assert resp.status_code == 400
    data = resp.json()
    assert "image_url" in data.get("detail", "")


def test_generate_tags_validates_url_format(client: TestClient):
    """generate-tags should validate image_url format."""
    resp = client.post("/generate-tags", json={"image_url": "not-a-url"})
    assert resp.status_code == 400
    data = resp.json()
    assert "valid HTTP/HTTPS URL" in data.get("detail", "")
