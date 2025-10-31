"""
JSON sanitization utilities for node responses.
"""

import json
import re
import logging
from typing import Dict, Any, Union


def sanitize_json_response(response_text: str) -> Dict[str, Any]:
    """
    Sanitize and parse JSON from model responses.

    Handles common formatting issues in LLM JSON outputs.

    Args:
        response_text: Raw text response from model

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed after sanitization
    """
    logger = logging.getLogger(__name__)

    # Extract JSON from markdown code blocks
    cleaned_text = _extract_json_from_markdown(response_text)

    # Apply progressive sanitization
    sanitization_steps = [
        _fix_trailing_commas,
        _fix_newlines_in_strings,
        _fix_missing_commas,
        _fix_unescaped_quotes,
        _fix_single_quotes
    ]

    current_text = cleaned_text

    for step_func in sanitization_steps:
        try:
            # Try parsing at each step
            return json.loads(current_text)
        except json.JSONDecodeError:
            # Apply next sanitization step
            current_text = step_func(current_text)
            logger.debug(f"Applied sanitization step: {step_func.__name__}")

    # Final attempt
    try:
        return json.loads(current_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON after all sanitization steps: {str(e)}")
        logger.debug(f"Final sanitized text: {current_text[:200]}...")
        raise


def _extract_json_from_markdown(text: str) -> str:
    """Extract JSON content from markdown code blocks."""

    # Remove markdown code blocks
    # text = re.sub(r'```(?:json)?', '', text)
    # text = re.sub(r'```\s*\n?', '', text)

    # Remove markdown code block markers like ```json or ```
    text = re.sub(r'```(?:json)?', '', text)
    text = text.strip()


    # Find JSON object boundaries
    start_idx = text.find('{')
    end_idx = text.rfind('}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]

    return text.strip()


def _fix_trailing_commas(json_str: str) -> str:
    """Remove trailing commas before closing brackets."""
    # Fix trailing commas before }
    json_str = re.sub(r',\s*}', '}', json_str)
    # Fix trailing commas before ]
    json_str = re.sub(r',\s*]', ']', json_str)
    return json_str


def _fix_newlines_in_strings(json_str: str) -> str:
    """Fix problematic newlines within string values."""
    # Replace newlines followed by quotes (common LLM issue)
    json_str = re.sub(r'\n\s*"', ' "', json_str)
    return json_str


def _fix_missing_commas(json_str: str) -> str:
    """Add missing commas between JSON elements."""
    # Add commas between objects
    json_str = re.sub(r'}\s*{', '}, {', json_str)
    # Add commas between object and array
    json_str = re.sub(r']\s*{', '], {', json_str)
    # Add commas between object and string
    json_str = re.sub(r'}\s*"', '}, "', json_str)
    return json_str


def _fix_unescaped_quotes(json_str: str) -> str:
    """Fix unescaped quotes within string values."""
    # This is a simplified fix - more complex scenarios may need custom handling
    json_str = re.sub(r':\s*"([^"]*)"([^",}\]]*)"', r': "\1\2"', json_str)
    return json_str


def _fix_single_quotes(json_str: str) -> str:
    """Replace single quotes with double quotes."""
    # Replace single quotes around keys and values
    json_str = json_str.replace("'", '"')
    return json_str
