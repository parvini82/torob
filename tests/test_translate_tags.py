"""Tests for the translate_tags node.

These tests verify the tag translation functionality and
Persian language processing without making actual API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.service.workflow.translate_tags import (
    build_translation_prompt,
    translate_tags_node,
)


def test_build_translation_prompt_structure():
    """build_translation_prompt should return comprehensive translation instructions."""
    entities = [
        {"name": "product_type", "values": ["t-shirt"]},
        {"name": "color", "values": ["blue", "red"]},
    ]

    prompt = build_translation_prompt(entities)

    # Verify key components are present
    assert "translate" in prompt.lower() or "ترجمه" in prompt
    assert "persian" in prompt.lower() or "فارسی" in prompt
    assert "JSON" in prompt
    assert "t-shirt" in prompt
    assert "blue" in prompt


def test_build_translation_prompt_handles_empty_entities():
    """build_translation_prompt should handle empty entities gracefully."""
    prompt = build_translation_prompt([])

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "translate" in prompt.lower() or "ترجمه" in prompt


@patch("src.service.workflow.translate_tags.OpenRouterClient")
def test_translate_tags_node_success(mock_client_class):
    """translate_tags_node should translate English entities to Persian."""
    # Setup mock client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock translation response
    mock_client.call_json.return_value = {
        "json": {
            "entities": [
                {"name": "نوع_محصول", "values": ["تی‌شرت"]},
                {"name": "رنگ", "values": ["آبی"]},
            ]
        },
        "text": None,
    }

    # Test input state
    state = {
        "image_url": "https://example.com/image.jpg",
        "image_tags_en": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
    }

    result = translate_tags_node(state)

    # Verify output structure
    assert "translated_tags" in result
    assert result["translated_tags"]["entities"][0]["name"] == "نوع_محصول"
    assert result["translated_tags"]["entities"][0]["values"] == ["تی‌شرت"]

    # Verify client was called
    mock_client.call_json.assert_called_once()


def test_translate_tags_node_missing_english_tags():
    """translate_tags_node should handle missing English tags."""
    state = {"image_url": "https://example.com/image.jpg"}

    with pytest.raises(ValueError, match="image_tags_en.*missing"):
        translate_tags_node(state)


@patch("src.service.workflow.translate_tags.OpenRouterClient")
def test_translate_tags_node_empty_entities(mock_client_class):
    """translate_tags_node should handle empty entities list."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.call_json.return_value = {"json": {"entities": []}, "text": None}

    state = {"image_url": "test", "image_tags_en": {"entities": []}}

    result = translate_tags_node(state)

    assert result["translated_tags"]["entities"] == []


@patch("src.service.workflow.translate_tags.OpenRouterClient")
def test_translate_tags_node_preserves_state(mock_client_class):
    """translate_tags_node should preserve existing state fields."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.call_json.return_value = {"json": {"entities": []}, "text": None}

    state = {
        "image_url": "test",
        "image_tags_en": {"entities": []},
        "existing_field": "should_be_kept",
        "raw_response": "original_response",
    }

    result = translate_tags_node(state)

    # Verify existing fields are preserved
    assert result["existing_field"] == "should_be_kept"
    assert result["raw_response"] == "original_response"
    assert "translated_tags" in result
