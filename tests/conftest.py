"""Pytest configuration and shared fixtures for the Torob project tests.

This file provides common fixtures and utilities used across the test suite,
including a FastAPI test client and environment configuration loader.
"""

import os

import pytest
from fastapi.testclient import TestClient

from src.controller.api_controller import app


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load environment variables for tests.

    Ensures required environment variables are set for the test session.
    Sensitive values are read from the environment; defaults are provided for
    non-sensitive configuration used by tests.
    """
    os.environ.setdefault("SERVER_HOST", "127.0.0.1")
    os.environ.setdefault("SERVER_PORT", "8001")
    os.environ.setdefault("APP_NAME", "Torob API - Test")
    os.environ.setdefault("APP_VERSION", "test")
    os.environ.setdefault("DEBUG_MODE", "true")


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a FastAPI test client for API endpoint testing."""
    return TestClient(app)
