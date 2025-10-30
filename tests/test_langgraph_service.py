"""Tests for the LangGraph service module.

These tests mock model client calls to verify workflow behavior,
node integration, and error handling without making external API requests.
"""

from unittest.mock import patch

import pytest

from src.service.workflow.langgraph_service import (
    _compile_workflow,
    run_langgraph_on_bytes,
    run_langgraph_on_url,
)


@pytest.fixture()
def mock_workflow_result():
    """Provide a mock workflow result for testing."""
    return {
        "image_url": "https://example.com/image.jpg",
        "image_tags_en": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
        "final_output": {
            "entities": [
                {"name": "نوع_محصول", "values": ["تی‌شرت"]},
                {"name": "رنگ", "values": ["آبی"]},
            ]
        },
    }


def test_compile_workflow():
    """Workflow should compile without errors and have expected structure."""
    workflow = _compile_workflow()
    assert workflow is not None
    # Verify the workflow can be invoked (basic structure test)
    assert hasattr(workflow, "invoke")


@patch("src.service.workflow.langgraph_service._workflow")
def test_run_langgraph_on_url_success(mock_workflow, mock_workflow_result):
    """run_langgraph_on_url should process URL and return formatted results."""
    mock_workflow.invoke.return_value = mock_workflow_result

    result = run_langgraph_on_url("https://example.com/image.jpg")

    assert isinstance(result, dict)
    assert "english" in result
    assert "persian" in result
    assert result["english"] == mock_workflow_result["image_tags_en"]
    assert result["persian"] == mock_workflow_result["final_output"]

    # Verify workflow was called with correct initial state
    mock_workflow.invoke.assert_called_once_with(
        {"image_url": "https://example.com/image.jpg"}
    )


@patch("src.service.workflow.langgraph_service._workflow")
def test_run_langgraph_on_bytes_success(mock_workflow, mock_workflow_result):
    """run_langgraph_on_bytes should process bytes and return formatted results."""
    mock_workflow.invoke.return_value = mock_workflow_result

    test_bytes = b"fake-image-data"
    result = run_langgraph_on_bytes(test_bytes)

    assert isinstance(result, dict)
    assert "english" in result
    assert "persian" in result
    assert result["english"] == mock_workflow_result["image_tags_en"]
    assert result["persian"] == mock_workflow_result["final_output"]

    # Verify workflow was called with base64 data URI
    call_args = mock_workflow.invoke.call_args[0][0]
    assert "image_url" in call_args
    assert call_args["image_url"].startswith("data:image/jpeg;base64,")


@patch("src.service.workflow.langgraph_service._workflow")
def test_run_langgraph_on_url_empty_results(mock_workflow):
    """Function should handle empty workflow results gracefully."""
    mock_workflow.invoke.return_value = {"image_url": "test"}

    result = run_langgraph_on_url("https://example.com/image.jpg")

    assert result["english"] == {}
    assert result["persian"] == {}


@patch("src.service.workflow.langgraph_service._workflow")
def test_run_langgraph_on_bytes_base64_encoding(mock_workflow):
    """Function should properly encode bytes to base64 data URI."""
    mock_workflow.invoke.return_value = {}

    test_bytes = b"test-data"
    run_langgraph_on_bytes(test_bytes)

    call_args = mock_workflow.invoke.call_args[0][0]
    expected_b64 = "dGVzdC1kYXRh"  # base64 of "test-data"
    expected_uri = f"data:image/jpeg;base64,{expected_b64}"

    assert call_args["image_url"] == expected_uri


def test_run_langgraph_on_url_validates_input():
    """Function should handle invalid URLs appropriately."""
    # Test with empty string - should not crash
    with patch("src.service.workflow.langgraph_service._workflow") as mock_workflow:
        mock_workflow.invoke.return_value = {}
        result = run_langgraph_on_url("")
        assert isinstance(result, dict)


def test_run_langgraph_on_bytes_validates_input():
    """Function should handle empty bytes appropriately."""
    # Test with empty bytes - should not crash
    with patch("src.service.workflow.langgraph_service._workflow") as mock_workflow:
        mock_workflow.invoke.return_value = {}
        result = run_langgraph_on_bytes(b"")
        assert isinstance(result, dict)
