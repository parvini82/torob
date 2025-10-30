"""Tests for the merge_results node.

These tests verify the final result merging and formatting
functionality in the LangGraph workflow.
"""

from src.service.workflow.merge_results import merge_results_node


def test_merge_results_node_success():
    """merge_results_node should combine English and Persian results."""
    state = {
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
    }

    result = merge_results_node(state)

    # Verify final output is set to Persian results
    assert "final_output" in result
    assert result["final_output"] == state["translated_tags"]

    # Verify original state is preserved
    assert result["image_url"] == state["image_url"]
    assert result["image_tags_en"] == state["image_tags_en"]
    assert result["translated_tags"] == state["translated_tags"]


def test_merge_results_node_missing_translated_tags():
    """merge_results_node should handle missing translated_tags gracefully."""
    state = {"image_url": "test", "image_tags_en": {"entities": []}}

    result = merge_results_node(state)

    # Should set final_output to empty dict when translated_tags missing
    assert result["final_output"] == {}


def test_merge_results_node_empty_translated_tags():
    """merge_results_node should handle empty translated_tags."""
    state = {
        "image_url": "test",
        "image_tags_en": {"entities": []},
        "translated_tags": {"entities": []},
    }

    result = merge_results_node(state)

    assert result["final_output"]["entities"] == []


def test_merge_results_node_preserves_metadata():
    """merge_results_node should preserve any existing metadata."""
    state = {
        "image_url": "test",
        "image_tags_en": {"entities": []},
        "translated_tags": {"entities": []},
        "raw_response": "original response",
        "processing_time": 1.23,
        "model_used": "test-model",
    }

    result = merge_results_node(state)

    # Verify metadata preservation
    assert result["raw_response"] == "original response"
    assert result["processing_time"] == 1.23
    assert result["model_used"] == "test-model"
    assert "final_output" in result
