"""Tests for the image_to_tags node.

These tests verify the image analysis node behavior, prompt generation,
and error handling without making actual model calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.service.langgraph.image_to_tags import (
    build_prompt,
    image_to_tags_node,
)


def test_build_prompt_contains_key_instructions():
    """build_prompt should return comprehensive NER instructions."""
    prompt = build_prompt()

    # Verify key instruction components are present
    assert "Named Entity Recognition" in prompt or "NER" in prompt
    assert "apparel" in prompt or "fashion" in prompt
    assert "JSON" in prompt
    assert "entities" in prompt

    # Check for specific entity types mentioned
    assert "product_type" in prompt
    assert "color" in prompt
    assert "material" in prompt


def test_build_prompt_includes_example_format():
    """build_prompt should include example JSON format."""
    prompt = build_prompt()

    assert "Example output format" in prompt or "example" in prompt.lower()
    assert '{"entities":' in prompt or '"entities"' in prompt
    assert '"name":' in prompt and '"values":' in prompt


@patch("src.service.langgraph.image_to_tags.OpenRouterClient")
def test_image_to_tags_node_success(mock_client_class):
    """image_to_tags_node should process image URL and return enhanced state."""
    # Setup mock client
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock successful response
    mock_client.call_json.return_value = {
        "json": {
            "entities": [
                {"name": "product_type", "values": ["t-shirt"]},
                {"name": "color", "values": ["blue"]},
            ]
        },
        "text": "raw model response text",
    }

    # Test input state
    state = {"image_url": "https://example.com/image.jpg"}

    result = image_to_tags_node(state)

    # Verify output structure
    assert "image_url" in result
    assert "image_tags_en" in result
    assert "raw_response" in result

    # Verify data preservation and enhancement
    assert result["image_url"] == state["image_url"]
    assert result["image_tags_en"]["entities"][0]["name"] == "product_type"
    assert result["raw_response"] == "raw model response text"

    # Verify client was called correctly
    mock_client.call_json.assert_called_once()
    call_args = mock_client.call_json.call_args
    assert call_args[1]["model"] is not None  # VISION_MODEL should be passed
    assert len(call_args[1]["messages"]) == 1
    assert call_args[1]["messages"][0]["role"] == "user"


def test_image_to_tags_node_missing_image_url():
    """image_to_tags_node should raise ValueError when image_url is missing."""
    state = {}  # Missing image_url

    with pytest.raises(ValueError, match="image_url.*missing"):
        image_to_tags_node(state)


def test_image_to_tags_node_empty_image_url():
    """image_to_tags_node should raise ValueError for empty image_url."""
    state = {"image_url": ""}

    with pytest.raises(ValueError, match="image_url.*missing"):
        image_to_tags_node(state)


@patch("src.service.langgraph.image_to_tags.OpenRouterClient")
def test_image_to_tags_node_handles_null_json(mock_client_class):
    """image_to_tags_node should handle null JSON response gracefully."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock response with null JSON
    mock_client.call_json.return_value = {"json": None, "text": "failed to parse"}

    state = {"image_url": "https://example.com/image.jpg"}
    result = image_to_tags_node(state)

    assert result["image_tags_en"] == {}
    assert result["raw_response"] == "failed to parse"


@patch("src.service.langgraph.image_to_tags.OpenRouterClient")
def test_image_to_tags_node_preserves_existing_state(mock_client_class):
    """image_to_tags_node should preserve existing state while adding new fields."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.call_json.return_value = {"json": {}, "text": ""}

    # State with existing data
    state = {
        "image_url": "https://example.com/image.jpg",
        "existing_field": "should_be_preserved",
        "another_field": 42,
    }

    result = image_to_tags_node(state)

    # Verify existing fields are preserved
    assert result["existing_field"] == "should_be_preserved"
    assert result["another_field"] == 42

    # Verify new fields are added
    assert "image_tags_en" in result
    assert "raw_response" in result


@patch("src.service.langgraph.image_to_tags.make_text_part")
@patch("src.service.langgraph.image_to_tags.make_image_part")
@patch("src.service.langgraph.image_to_tags.OpenRouterClient")
def test_image_to_tags_node_message_structure(
    mock_client_class, mock_make_image, mock_make_text
):
    """image_to_tags_node should construct messages with correct parts."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.call_json.return_value = {"json": {}, "text": ""}

    mock_make_text.return_value = {"type": "text", "text": "prompt"}
    mock_make_image.return_value = {"type": "image_url", "image_url": "test_url"}

    state = {"image_url": "https://example.com/test.jpg"}

    image_to_tags_node(state)

    # Verify helper functions were called
    mock_make_text.assert_called_once()
    mock_make_image.assert_called_once_with("https://example.com/test.jpg")

    # Verify message structure
    call_args = mock_client.call_json.call_args[1]["messages"]
    message = call_args[0]
    assert message["role"] == "user"
    assert len(message["content"]) == 2  # text + image parts
