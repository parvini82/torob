"""Tests for the OpenRouter model client.

These tests mock HTTP requests to verify client behavior,
error handling, JSON parsing, and retry logic without making real API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.service.langgraph.model_client import (
    OpenRouterClient,
    OpenRouterError,
    extract_json_from_text,
    make_image_part,
    make_text_part,
    _auth_headers,
)


@pytest.fixture()
def client():
    """Provide an OpenRouterClient instance for testing."""
    return OpenRouterClient()


def _make_mock_response(status_code: int = 200, content: str = "test"):
    """Create a mock HTTP response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = f"Error response: {content}"
    mock_resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return mock_resp


def test_make_image_part():
    """make_image_part should return proper image message part."""
    result = make_image_part("https://example.com/image.jpg")
    expected = {"type": "image_url", "image_url": "https://example.com/image.jpg"}
    assert result == expected


def test_make_text_part():
    """make_text_part should return proper text message part."""
    result = make_text_part("Hello world")
    expected = {"type": "text", "text": "Hello world"}
    assert result == expected


def test_extract_json_from_text_valid_json():
    """extract_json_from_text should parse valid JSON correctly."""
    json_obj, error = extract_json_from_text('{"key": "value"}')
    assert json_obj == {"key": "value"}
    assert error is None


def test_extract_json_from_text_embedded_json():
    """extract_json_from_text should extract JSON from text with surrounding content."""
    text = 'Here is some JSON: {"entities": []} and more text'
    json_obj, error = extract_json_from_text(text)
    assert json_obj == {"entities": []}
    assert error is None


def test_extract_json_from_text_invalid_json():
    """extract_json_from_text should return error for invalid JSON."""
    json_obj, error = extract_json_from_text("not json at all")
    assert json_obj is None
    assert error == "not json at all"


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
def test_auth_headers_with_api_key():
    """_auth_headers should return proper headers when API key is set."""
    headers = _auth_headers()
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"


@patch.dict("os.environ", {"OPENROUTER_API_KEY": ""})
def test_auth_headers_without_api_key():
    """_auth_headers should raise error when API key is missing."""
    with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY is empty"):
        _auth_headers()


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_chat_success(mock_auth, mock_post, client):
    """call_chat should return parsed response on success."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    mock_post.return_value = _make_mock_response(200, "Hello response")

    result = client.call_chat("test-model", [{"role": "user", "content": "Hello"}])

    assert result["content"] == "Hello response"
    assert "raw" in result
    mock_post.assert_called_once()


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_chat_http_error(mock_auth, mock_post, client):
    """call_chat should raise OpenRouterError on HTTP error."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    mock_post.return_value = _make_mock_response(500, "Server error")

    with pytest.raises(OpenRouterError, match="OpenRouter HTTP 500"):
        client.call_chat("test-model", [])


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_json_success(mock_auth, mock_post, client):
    """call_json should return parsed JSON response."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    json_content = json.dumps({"entities": []})
    mock_post.return_value = _make_mock_response(200, json_content)

    result = client.call_json("test-model", [{"role": "user", "content": "Test"}])

    assert result["json"] == {"entities": []}
    assert result["text"] is None


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_json_invalid_json(mock_auth, mock_post, client):
    """call_json should handle invalid JSON gracefully."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    mock_post.return_value = _make_mock_response(200, "not valid json")

    result = client.call_json("test-model", [])

    assert result["json"] is None
    assert result["text"] == "not valid json"


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_chat_with_retries(mock_auth, mock_post, client):
    """call_chat should retry on network errors."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    # First call fails, second succeeds
    mock_post.side_effect = [
        Exception("Network error"),
        _make_mock_response(200, "Success"),
    ]

    result = client.call_chat("test-model", [], max_retries=1)

    assert result["content"] == "Success"
    assert mock_post.call_count == 2


@patch("requests.post")
@patch("src.service.langgraph.model_client._auth_headers")
def test_call_json_with_temperature(mock_auth, mock_post, client):
    """call_json should pass temperature parameter correctly."""
    mock_auth.return_value = {"Authorization": "Bearer test"}
    mock_post.return_value = _make_mock_response(200, '{"test": true}')

    client.call_json("test-model", [], temperature=0.7)

    # Check that temperature was included in the payload
    call_args = mock_post.call_args
    payload = call_args[1]["json"]  # kwargs -> json
    assert payload["temperature"] == 0.7
