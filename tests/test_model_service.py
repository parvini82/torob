"""Tests for the standalone model service functions.

These tests mock HTTP requests to verify the legacy model service behavior,
request building, and error handling without making external API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.service.model_service import (
    predict_tags,
    prepare_image_input,
)


def test_prepare_image_input_creates_data_uri():
    """prepare_image_input should create proper base64 data URI."""
    test_bytes = b"test-image-data"

    result = prepare_image_input(test_bytes)

    assert result["type"] == "image_url"
    assert result["image_url"].startswith("data:image/jpeg;base64,")

    # Verify base64 encoding
    import base64

    expected_b64 = base64.b64encode(test_bytes).decode("utf-8")
    expected_uri = f"data:image/jpeg;base64,{expected_b64}"
    assert result["image_url"] == expected_uri


def test_prepare_image_input_handles_empty_bytes():
    """prepare_image_input should handle empty bytes."""
    result = prepare_image_input(b"")
    assert result["type"] == "image_url"
    assert result["image_url"] == "data:image/jpeg;base64,"


@patch("requests.post")
def test_predict_tags_success(mock_post):
    """predict_tags should return parsed JSON on successful API call."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"english": {"entities": []}, "persian": {"entities": []}}'
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    result = predict_tags(b"fake-image-bytes")

    assert isinstance(result, dict)
    assert "english" in result
    assert "persian" in result

    # Verify API call was made correctly
    mock_post.assert_called_once()
    call_args = mock_post.call_args

    # Check URL
    assert "openrouter.ai/api/v1/chat/completions" in call_args[0][0]

    # Check headers
    headers = call_args[1]["headers"]
    assert "Authorization" in headers
    assert "Content-Type" in headers

    # Check payload structure
    payload = call_args[1]["json"]
    assert "model" in payload
    assert "messages" in payload
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"
    assert len(payload["messages"][0]["content"]) == 2  # text + image


@patch("requests.post")
def test_predict_tags_json_extraction(mock_post):
    """predict_tags should extract JSON from response content correctly."""
    # Response with JSON embedded in text
    content_with_json = 'Here is the result: {"tags": ["extracted"]} and more text'

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": content_with_json}}]
    }
    mock_post.return_value = mock_response

    result = predict_tags(b"test-bytes")

    assert result["tags"] == ["extracted"]


@patch("requests.post")
def test_predict_tags_json_parse_error(mock_post):
    """predict_tags should handle JSON parse errors gracefully."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "not valid json content"}}]
    }
    mock_post.return_value = mock_response

    result = predict_tags(b"test-bytes")

    assert "tags" in result
    assert result["tags"] == ["parse_error"]
    assert "raw_output" in result


@patch("requests.post")
def test_predict_tags_http_error(mock_post):
    """predict_tags should raise exception on HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    with pytest.raises(Exception, match="Request failed with status code 500"):
        predict_tags(b"test-bytes")


@patch("requests.post")
def test_predict_tags_request_structure(mock_post):
    """predict_tags should build request with correct structure."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"result": "ok"}'}}]
    }
    mock_post.return_value = mock_response

    test_bytes = b"image-data"
    predict_tags(test_bytes)

    # Verify request payload structure
    call_args = mock_post.call_args
    payload = call_args[1]["json"]

    assert "model" in payload
    assert "messages" in payload

    message = payload["messages"][0]
    assert message["role"] == "user"
    assert len(message["content"]) == 2

    # Check text content
    text_part = message["content"][0]
    assert text_part["type"] == "text"
    assert "Named Entity Recognition" in text_part["text"] or "NER" in text_part["text"]

    # Check image content
    image_part = message["content"][1]
    assert image_part["type"] == "image_url"
    assert image_part["image_url"].startswith("data:image/jpeg;base64,")


@patch("requests.post")
def test_predict_tags_uses_config_values(mock_post):
    """predict_tags should use values from configuration."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"test": "value"}'}}]
    }
    mock_post.return_value = mock_response

    with (
        patch("src.service.model_service.API_KEY", "test-api-key"),
        patch("src.service.model_service.MODEL", "test-model"),
    ):

        predict_tags(b"test")

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        payload = call_args[1]["json"]

        assert headers["Authorization"] == "Bearer test-api-key"
        assert payload["model"] == "test-model"
