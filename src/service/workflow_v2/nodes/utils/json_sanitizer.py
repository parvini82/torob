"""
Enhanced JSON sanitization utilities for LLM responses.
"""

import json
import re
import logging
from typing import Dict, Any, Union, Tuple

def sanitize_json_response(response_text: str) -> Union[Dict[str, Any], list]:
    """
    Enhanced sanitize and parse JSON from model responses.
    Handles more robust LLM JSON formatting issues.
    """
    logger = logging.getLogger(__name__)
    if not response_text or not isinstance(response_text, str):
        raise json.JSONDecodeError("Empty or invalid response_text", "", 0)

    # Log the raw response for debugging
    logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")

    # Enhanced normalization steps
    text = _comprehensive_normalize(response_text)

    # Try direct parsing first (for well-formed responses)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.debug("Direct parsing failed, applying progressive sanitization")

    # Progressive sanitization with better error tracking
    steps = [
        _extract_json_payload_enhanced,
        _fix_pseudo_json_syntax,
        _fix_trailing_commas,
        _fix_missing_commas_between_objects,
        _fix_newlines_in_strings,
        _fix_unescaped_quotes_robust,
        _balance_brackets_smart
    ]

    current = text
    for i, step in enumerate(steps):
        try:
            result = json.loads(current)
            logger.debug(f"Successfully parsed after step {i}: {step.__name__}")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Step {i} ({step.__name__}) failed: {e}")
            current = step(current)

    # Final attempt with detailed error info
    try:
        return json.loads(current)
    except json.JSONDecodeError as e:
        logger.error(f"All sanitization steps failed. Final error: {e}")
        logger.error(f"Problem area: {current[max(0, e.pos-50):e.pos+50]}")
        raise

def _comprehensive_normalize(text: str) -> str:
    """Enhanced normalization for various LLM output formats."""
    # Strip BOM and normalize Unicode
    text = text.lstrip("\ufeff").strip()

    # Normalize various quote types
    replacements = [
        (""", '"'), (""", '"'), ("'", "'"), ("'", "'"),
        ("'", "'"), ("'", "'")  # Additional smart quotes
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text

def _extract_json_payload_enhanced(text: str) -> str:
    """Enhanced JSON extraction with better boundary detection."""
    # Remove code blocks and XML-style tags
    text = re.sub(r"```")
    text = re.sub(r"```", "", text).strip()
    text = re.sub(r"<output[^>]*>|</output>", "", text, flags=re.IGNORECASE).strip()

    # Find JSON boundaries with better heuristics
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested object
        r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'  # Nested array
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            # Return the longest match (likely the main JSON)
            return max(matches, key=len).strip()

    # Fallback to simple boundary detection
    obj_start, obj_end = text.find("{"), text.rfind("}")
    arr_start, arr_end = text.find("["), text.rfind("]")

    if obj_start != -1 and obj_end > obj_start:
        return text[obj_start:obj_end + 1].strip()
    elif arr_start != -1 and arr_end > arr_start:
        return text[arr_start:arr_end + 1].strip()

    return text.strip()

def _fix_pseudo_json_syntax(text: str) -> str:
    """Fix Python-like dictionary syntax to valid JSON."""
    # Convert Python None/True/False to JSON null/true/false
    text = re.sub(r'\bNone\b', 'null', text)
    text = re.sub(r'\bTrue\b', 'true', text)
    text = re.sub(r'\bFalse\b', 'false', text)

    # Fix unquoted keys (common in LLM outputs)
    text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)

    # Fix single-quoted strings to double-quoted
    # Be careful not to affect apostrophes inside already double-quoted strings
    text = re.sub(r"(?<![\\\"])'([^']*?)'(?=\s*[,}\]:])", r'"\1"', text)

    return text

def _fix_unescaped_quotes_robust(text: str) -> str:
    """More robust handling of unescaped quotes in strings."""
    # Pattern for finding string values that might contain unescaped quotes
    def fix_string_quotes(match):
        key_part = match.group(1)
        value_part = match.group(2)
        # Escape internal quotes in the value
        value_part = value_part.replace('"', '\\"')
        return f'{key_part}"{value_part}"'

    # Fix quotes in string values
    text = re.sub(r'(:\s*")([^"]*?"[^"]*?)(")', fix_string_quotes, text)

    return text

def _balance_brackets_smart(text: str) -> str:
    """Smart bracket balancing with context awareness."""
    def count_unescaped(char, s):
        """Count unescaped occurrences of character."""
        count = 0
        escaped = False
        for c in s:
            if escaped:
                escaped = False
                continue
            if c == '\\':
                escaped = True
            elif c == char:
                count += 1
        return count

    # Check and fix braces
    open_braces = count_unescaped('{', text)
    close_braces = count_unescaped('}', text)

    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)

    # Check and fix brackets
    open_brackets = count_unescaped('[', text)
    close_brackets = count_unescaped(']', text)

    if open_brackets > close_brackets:
        text += ']' * (open_brackets - close_brackets)

    return text

# Keep existing helper functions but enhance them
def _fix_trailing_commas(s: str) -> str:
    """Enhanced trailing comma removal."""
    # Remove trailing commas before closing brackets/braces
    s = re.sub(r',\s*([}\]])', r'\1', s)
    # Also handle trailing commas at end of lines
    s = re.sub(r',\s*\n\s*([}\]])', r'\n\1', s)
    return s

def _fix_missing_commas_between_objects(s: str) -> str:
    """Enhanced comma insertion between JSON elements."""
    patterns = [
        (r'}\s*{', '}, {'),           # Adjacent objects
        (r']\s*{', '], {'),           # Array followed by object
        (r'}\s*"', '}, "'),           # Object followed by string
        (r']\s*"', '], "'),           # Array followed by string
        (r'"\s*{(?=\s*")', '", {'),   # String followed by object
        (r'"\s*\[(?=\s*")', '", ['),  # String followed by array
    ]

    for pattern, replacement in patterns:
        s = re.sub(pattern, replacement, s)

    return s

def _fix_newlines_in_strings(s: str) -> str:
    """Enhanced newline handling in JSON strings."""
    # Replace problematic newlines in string values
    s = re.sub(r'"\s*\n\s*"', '" "', s)  # Broken string continuation
    s = re.sub(r':\s*"\s*\n\s*([^"]*?)\s*\n\s*"', r': "\1"', s)  # Multi-line string values
    return s
