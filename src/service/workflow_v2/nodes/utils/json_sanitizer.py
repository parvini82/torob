"""
JSON sanitization utilities for node responses.
"""

import json
import re
import logging
from typing import Dict, Any, Union


def sanitize_json_response(response_text: str) -> Union[Dict[str, Any], list]:
    """
    Sanitize and parse JSON from model responses.

    Handles common LLM JSON formatting issues safely and progressively.
    Returns either a dict (object) or a list (array) depending on payload.

    Raises:
        json.JSONDecodeError if parsing fails after all steps.
    """
    logger = logging.getLogger(__name__)
    if not response_text or not isinstance(response_text, str):
        raise json.JSONDecodeError("Empty or invalid response_text", "", 0)

    # 0) Normalize Unicode quotes and strip BOM if present
    text = _normalize_unicode_and_bom(response_text)

    # 1) Extract the most likely JSON payload (object or array) from any surrounding text/markdown
    text = _extract_json_payload(text)

    # 2) Progressive sanitization & parsing attempts
    steps = [
        _fix_trailing_commas,
        _fix_missing_commas_between_objects,
        _fix_newlines_in_strings,
        _fix_unescaped_inner_double_quotes,
        _fix_single_quoted_keys_and_values,  # careful, limited to proper contexts
        _balance_brackets,                   # close one missing '}' or ']' if clearly unbalanced
    ]

    current = text
    for step in steps:
        try:
            return json.loads(current)
        except json.JSONDecodeError:
            current = step(current)
            logger.debug(f"Applied sanitization step: {step.__name__}")

    # Final parse attempt
    try:
        return json.loads(current)
    except json.JSONDecodeError as e:
        snippet = current[:400].replace("\n", " ")
        logger.error(f"Failed to parse JSON after sanitization: {e}")
        logger.debug(f"Final sanitized text head: {snippet}...")
        raise


# ------------------------ Helpers ------------------------

def _normalize_unicode_and_bom(text: str) -> str:
    """Normalize BOM and typographic quotes to plain ASCII quotes."""
    # Strip BOM
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")

    # Replace typographic quotes “ ” ‘ ’ with normal quotes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    return text


def _extract_json_payload(text: str) -> str:
    """
    Extract the JSON payload from surrounding text or markdown fences.
    Supports both object `{...}` and array `[...]` top-level payloads.
    Prefers the first well-formed boundary found.
    """
    # Remove markdown code fences like ```json ... ``` or ```
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```", "", text).strip()

    # Try object boundaries
    obj_start = text.find("{")
    obj_end = text.rfind("}")

    # Try array boundaries
    arr_start = text.find("[")
    arr_end = text.rfind("]")

    candidates = []
    if obj_start != -1 and obj_end > obj_start:
        candidates.append(text[obj_start:obj_end + 1])
    if arr_start != -1 and arr_end > arr_start:
        candidates.append(text[arr_start:arr_end + 1])

    if not candidates:
        return text.strip()

    # Prefer the longest candidate (often the real payload)
    candidate = max(candidates, key=len).strip()
    return candidate


def _fix_trailing_commas(s: str) -> str:
    """Remove trailing commas before closing brackets/braces."""
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s


def _fix_missing_commas_between_objects(s: str) -> str:
    """
    Add missing commas between adjacent JSON elements.
    This is conservative to avoid injecting commas inside strings.
    """
    # } {  -> }, {
    s = re.sub(r"}\s*{", r"}, {", s)
    # ] {  -> ], {
    s = re.sub(r"]\s*{", r"], {", s)
    # } "  -> }, "
    s = re.sub(r"}\s*\"", r"}, \"", s)
    # ] "  -> ], "
    s = re.sub(r"]\s*\"", r"], \"", s)
    return s


def _fix_newlines_in_strings(s: str) -> str:
    """
    Replace raw newlines that often appear inside string values right
    before the closing quote. This reduces broken strings.
    """
    # Replace newline + spaces before a closing quote with a single space
    s = re.sub(r"\n\s*\"", r" \"", s)
    # Collapse multiple newlines into single space
    s = re.sub(r"\s*\n\s*", " ", s)
    return s


def _fix_unescaped_inner_double_quotes(s: str) -> str:
    """
    Attempt to escape stray unescaped double quotes inside JSON string values.
    Conservative approach: only target quotes between known delimiters like ': " ... " , or ': " ... " }'
    """
    # Pattern: colon -> space -> opening quote -> some chars without proper closing -> stray quote -> continue
    # This is intentionally limited; many cases are already fixed by other steps.
    s = re.sub(r'(:\s*")([^"]*?)(")([^,\}\]]*\s*[,}\]])', r'\1\2\3\4', s)
    return s


def _fix_single_quoted_keys_and_values(s: str) -> str:
    """
    Replace single-quoted keys/values with double-quoted equivalents ONLY when they form JSON delimiters,
    not apostrophes inside already double-quoted strings (e.g., "women's" must remain intact).
    """
    # Keys:  'key':  ->  "key":
    s = re.sub(r"(?<![\\\w])'([A-Za-z0-9_\- ]+)'\s*:", r'"\1":', s)

    # Values: : 'value'  ->  : "value"
    s = re.sub(r':\s*\'([^\'"]*)\'', r': "\1"', s)
    return s


def _balance_brackets(s: str) -> str:
    """
    If braces/brackets are clearly unbalanced by 1, try to fix by appending the missing closer.
    Avoids aggressive changes.
    """
    def _balance(chars_open: str, chars_close: str, text: str) -> str:
        open_count = text.count(chars_open)
        close_count = text.count(chars_close)
        if open_count - close_count == 1:
            return text + chars_close
        return text

    s = _balance("{", "}", s)
    s = _balance("[", "]", s)
    return s
