"""Pytest configuration and shared fixtures for the Torob project tests.

This file provides common fixtures and utilities used across the test suite,
including environment configuration and mock services for testing.
"""

import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.controller.api_controller import app


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables for tests.

    Ensures required environment variables are set for the test session.
    Sets up configuration needed for LangGraph services and API testing.
    """
    # API configuration
    os.environ.setdefault("SERVER_HOST", "127.0.0.1")
    os.environ.setdefault("SERVER_PORT", "8001")
    os.environ.setdefault("APP_NAME", "Torob API - Test")
    os.environ.setdefault("APP_VERSION", "test")
    os.environ.setdefault("DEBUG_MODE", "true")

    # LangGraph service configuration
    os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
    os.environ.setdefault(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
    )
    os.environ.setdefault("VISION_MODEL", "anthropic/claude-3-haiku")
    os.environ.setdefault("TRANSLATION_MODEL", "anthropic/claude-3-haiku")
    os.environ.setdefault("REQUEST_TIMEOUT", "30")

    # Database configuration (for tests)
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    # MinIO configuration (for tests)
    os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
    os.environ.setdefault("MINIO_ACCESS_KEY", "test-access-key")
    os.environ.setdefault("MINIO_SECRET_KEY", "test-secret-key")
    os.environ.setdefault("MINIO_BUCKET", "test-bucket")


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a FastAPI test client for API endpoint testing."""
    return TestClient(app)


@pytest.fixture()
def mock_openrouter_response():
    """Provide a mock OpenRouter API response for testing."""
    return {
        "json": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
        "text": None,
        "raw": {
            "choices": [
                {
                    "message": {
                        "content": '{"entities": [{"name": "product_type", "values": ["t-shirt"]}]}'
                    }
                }
            ]
        },
    }


@pytest.fixture()
def mock_langgraph_workflow_result():
    """Provide a mock LangGraph workflow result for testing."""
    return {
        "image_url": "https://example.com/image.jpg",
        "image_tags_en": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
        "translated_tags": {
            "entities": [
                {"name": "نوع_محصول", "values": ["تی‌شرت"]},
                {"name": "رنگ", "values": ["آبی"]},
            ]
        },
        "final_output": {
            "entities": [
                {"name": "نوع_محصول", "values": ["تی‌شرت"]},
                {"name": "رنگ", "values": ["آبی"]},
            ]
        },
    }


@pytest.fixture()
def sample_image_bytes():
    """Provide sample image bytes for testing."""
    return b"fake-image-binary-data-for-testing"


@pytest.fixture()
def mock_minio_service():
    """Provide a mock MinIO service for testing."""
    mock_service = MagicMock()
    mock_service.upload_file.return_value = (
        "https://minio.example.com/bucket/test-image.jpg"
    )
    return mock_service
