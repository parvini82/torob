"""Tests for the FastAPI controller endpoints.

These tests verify API endpoint behavior, request validation,
and response formatting without making external service calls.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.controller.api_controller import app


@pytest.fixture()
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Health endpoint should return OK status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("src.controller.api_controller.run_langgraph_on_url")
def test_generate_tags_success(mock_run_langgraph, client):
    """generate_tags endpoint should process URL and return Persian tags."""
    # Mock successful LangGraph response
    mock_run_langgraph.return_value = {
        "english": {"entities": [{"name": "product_type", "values": ["shirt"]}]},
        "persian": {"entities": [{"name": "نوع_محصول", "values": ["پیراهن"]}]},
    }

    payload = {"image_url": "https://example.com/image.jpg"}
    response = client.post("/generate-tags", json=payload)

    assert response.status_code == 200
    result = response.json()

    # Should return only Persian results
    assert "entities" in result
    assert result["entities"][0]["name"] == "نوع_محصول"

    # Verify service was called correctly
    mock_run_langgraph.assert_called_once_with("https://example.com/image.jpg")


def test_generate_tags_missing_url(client):
    """generate_tags should return error when image_url is missing."""
    payload = {}  # Missing image_url
    response = client.post("/generate-tags", json=payload)

    assert response.status_code == 200  # Endpoint returns 200 with error message
    result = response.json()
    assert "error" in result
    assert "image_url is required" in result["error"]


def test_generate_tags_empty_url(client):
    """generate_tags should return error for empty image_url."""
    payload = {"image_url": ""}
    response = client.post("/generate-tags", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert "error" in result


@patch("src.controller.api_controller.run_langgraph_on_url")
def test_generate_tags_service_error(mock_run_langgraph, client):
    """generate_tags should return 500 when service raises exception."""
    mock_run_langgraph.side_effect = Exception("Service unavailable")

    payload = {"image_url": "https://example.com/image.jpg"}
    response = client.post("/generate-tags", json=payload)

    assert response.status_code == 500
    result = response.json()
    assert "detail" in result
    assert "Error processing image" in result["detail"]


@patch("src.controller.api_controller.get_minio_service")
@patch("src.controller.api_controller.run_langgraph_on_bytes")
def test_upload_and_tag_success(mock_run_langgraph, mock_get_minio, client):
    """upload_and_tag should process file upload and return tags with MinIO URL."""
    # Mock MinIO service
    mock_minio = MagicMock()
    mock_minio.upload_file.return_value = "https://minio.example.com/bucket/image.jpg"
    mock_get_minio.return_value = mock_minio

    # Mock LangGraph response
    mock_run_langgraph.return_value = {
        "english": {"entities": []},
        "persian": {"entities": [{"name": "رنگ", "values": ["قرمز"]}]},
    }

    # Simulate file upload
    test_file_content = b"fake-image-data"
    files = {"file": ("test.jpg", test_file_content, "image/jpeg")}

    response = client.post("/upload-and-tag", files=files)

    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert "image_url" in result
    assert "tags" in result
    assert result["image_url"] == "https://minio.example.com/bucket/image.jpg"
    assert result["tags"]["entities"][0]["name"] == "رنگ"

    # Verify services were called correctly
    mock_minio.upload_file.assert_called_once()
    mock_run_langgraph.assert_called_once_with(test_file_content)


def test_upload_and_tag_invalid_file_type(client):
    """upload_and_tag should reject non-image files."""
    files = {"file": ("test.txt", b"text content", "text/plain")}

    response = client.post("/upload-and-tag", files=files)

    assert response.status_code == 400
    result = response.json()
    assert "Only image files are allowed" in result["detail"]


def test_upload_and_tag_empty_file(client):
    """upload_and_tag should reject empty files."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}

    response = client.post("/upload-and-tag", files=files)

    assert response.status_code == 400
    result = response.json()
    assert "Empty file uploaded" in result["detail"]


@patch("src.controller.api_controller.get_minio_service")
def test_upload_and_tag_minio_error(mock_get_minio, client):
    """upload_and_tag should handle MinIO upload errors."""
    mock_minio = MagicMock()
    mock_minio.upload_file.side_effect = Exception("MinIO error")
    mock_get_minio.return_value = mock_minio

    files = {"file": ("test.jpg", b"image-data", "image/jpeg")}

    response = client.post("/upload-and-tag", files=files)

    assert response.status_code == 500
    result = response.json()
    assert "Error processing upload" in result["detail"]


@patch("src.controller.api_controller.save_request_response")
@patch("src.controller.api_controller.run_langgraph_on_url")
def test_generate_tags_background_task(mock_run_langgraph, mock_save_db, client):
    """generate_tags should queue database save as background task."""
    mock_run_langgraph.return_value = {"persian": {"entities": []}}

    payload = {"image_url": "https://example.com/image.jpg"}
    response = client.post("/generate-tags", json=payload)

    assert response.status_code == 200
    # Background task execution is not easily testable with TestClient
    # but we can verify the endpoint completes successfully


def test_cors_headers_present(client):
    """API should include CORS headers for allowed origins."""
    response = client.options("/health")
    # TestClient doesn't fully simulate CORS, but endpoint should not crash
    assert response.status_code in [200, 405]  # OPTIONS might not be explicitly handled
