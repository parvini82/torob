"""Tests for the LangGraph image processing pipeline.

These tests mock model client calls to verify pipeline behavior, node integration,
and error handling without making external API requests.
"""

from unittest.mock import patch

import pytest

from src.service.langgraph.langgraph_service import (
    ImageProcessingPipeline,
    run_langgraph_on_bytes,
    run_langgraph_on_url,
)


@pytest.fixture()
def pipeline() -> ImageProcessingPipeline:
    """Provide a fresh pipeline instance for each test."""
    return ImageProcessingPipeline()


@patch("src.service.langgraph.model_client.OpenRouterClient.call_json")
def test_pipeline_process_image_url(mock_call_json, pipeline: ImageProcessingPipeline):
    """Pipeline should process image URL and return formatted results."""
    # Mock model client response for image_to_tags
    mock_call_json.return_value = {
        "json": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
        "text": "{...}",
    }

    result = pipeline.process_image_url("https://example.com/image.jpg")
    assert "english" in result and isinstance(result["english"], dict)
    assert "persian" in result and isinstance(result["persian"], dict)
    assert "metadata" in result and result["metadata"]["processing_success"] in [
        True,
        False,
    ]


@patch("src.service.langgraph.model_client.OpenRouterClient.call_json")
def test_run_langgraph_on_url_legacy(mock_call_json):
    """Legacy function should return results in expected shape."""
    mock_call_json.return_value = {"json": {"entities": []}, "text": "{}"}
    out = run_langgraph_on_url("https://example.com/x.png")
    assert set(out.keys()) == {"english", "persian"}


def test_pipeline_validates_input(pipeline: ImageProcessingPipeline):
    """Invalid inputs should raise errors."""
    with pytest.raises(Exception):
        pipeline.process_image_url("")
    with pytest.raises(Exception):
        pipeline.process_image_bytes(b"")


@patch("src.service.langgraph.model_client.OpenRouterClient.call_json")
def test_run_langgraph_on_bytes_legacy(mock_call_json):
    """Legacy bytes function should process base64 data URI."""
    mock_call_json.return_value = {"json": {"entities": []}, "text": "{}"}
    data = b"fake-binary-image"
    out = run_langgraph_on_bytes(data)
    assert set(out.keys()) == {"english", "persian"}
