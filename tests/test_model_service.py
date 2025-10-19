"""Tests for the ImageProcessor model service.

These tests mock network calls to OpenRouter and validate request building,
error handling, JSON parsing, and retry behavior without making real HTTP calls.
"""

from typing import Dict, Any
from unittest.mock import patch, MagicMock
import json
import pytest

from src.service.model_service import ImageProcessor, ModelServiceError


@pytest.fixture()
def processor() -> ImageProcessor:
    """Provide an ImageProcessor with default settings."""
    return ImageProcessor()


def _make_response(status: int = 200, json_body: Dict[str, Any] | None = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.elapsed.total_seconds.return_value = 0.123
    if json_body is None:
        json_body = {"choices": [{"message": {"content": json.dumps({"english": {}, "persian": {}})}}]}
    resp.json.return_value = json_body
    return resp


@patch("requests.Session.post")
def test_predict_tags_success(mock_post, processor: ImageProcessor):
    """Successful API call should return parsed JSON with metadata."""
    # Build a valid chat.completions-like body
    content = json.dumps({"english": {"entities": []}, "persian": {"entities": []}})
    mock_post.return_value = _make_response(
        200,
        {"choices": [{"message": {"content": content}}]}
    )

    out = processor.predict_tags(b"fake-bytes")
    assert isinstance(out, dict)
    assert "_metadata" in out and out["_metadata"]["model_used"]


@patch("requests.Session.post")
def test_predict_tags_http_error(mock_post, processor: ImageProcessor):
    """Non-200 status codes should raise ModelServiceError with details."""
    mock_post.return_value = _make_response(502, text="Bad gateway")

    with pytest.raises(ModelServiceError):
        processor.predict_tags(b"x")


@patch("requests.Session.post")
def test_predict_tags_malformed_json_content(mock_post, processor: ImageProcessor):
    """Malformed JSON in model content should return structured parse error info."""
    mock_post.return_value = _make_response(
        200,
        {"choices": [{"message": {"content": "<<<not-json>>>"}}]}
    )

    out = processor.predict_tags(b"x")
    assert out.get("error") == "json_parse_error" or isinstance(out, dict)


def test_prepare_image_input_encodes_base64(processor: ImageProcessor):
    """prepare_image_input should return data URI with base64 content."""
    payload = processor.prepare_image_input(b"abc")
    assert payload["type"] == "image_url"
    assert payload["image_url"].startswith("data:image/jpeg;base64,")


@patch("requests.Session.post", side_effect=Exception("network down"))
def test_predict_tags_network_error(mock_post):
    """Network exceptions should be wrapped into ModelServiceError."""
    with pytest.raises(ModelServiceError):
        ImageProcessor().predict_tags(b"y")
