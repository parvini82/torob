"""Translation node for converting English tags to Persian.

This module handles the second stage of the LangGraph pipeline where English
product tags and entities are translated to Persian using AI language models.
It maintains the original JSON structure while translating both keys and values.
"""

from typing import Dict, Any, Optional
import json

from .model_client import OpenRouterClient, make_text_part
from .config import TRANSLATE_MODEL


class TranslationError(Exception):
    """Custom exception for translation-related errors."""
    pass


def build_translation_prompt(tags_en: Dict[str, Any]) -> str:
    """Build a comprehensive prompt for translating English tags to Persian.
    
    Creates a detailed prompt that instructs the AI model to translate
    product entities and attributes from English to Persian while maintaining
    the original JSON structure and semantic meaning.
    
    Args:
        tags_en: English tags and entities to be translated
        
    Returns:
        str: Complete translation prompt for the AI model
    """
    # Convert the input to JSON string for inclusion in prompt
    json_input = json.dumps(tags_en, ensure_ascii=False, indent=2)
    
    return (
        "You are a professional translator specialized in e-commerce and apparel products. "
        "Your expertise includes Persian/Farsi translation of fashion and product terminology.\n\n"
        
        "Task: Translate the following JSON object from English to Persian (Farsi). "
        "Translate both entity names (keys) and their values while maintaining "
        "the exact JSON structure.\n\n"
        
        "Translation Guidelines:\n"
        "- Maintain the original JSON structure exactly\n"
        "- Translate entity names to appropriate Persian equivalents\n"
        "- Translate all values to natural Persian terms\n"
        "- Use standard Persian terminology for clothing and fashion items\n"
        "- Preserve arrays and nested structures\n"
        "- Ensure the output is valid JSON\n\n"
        
        "Common translations for reference:\n"
        "- color → رنگ\n"
        "- material → جنس\n"
        "- product_type → نوع کلی\n"
        "- pattern → طرح\n"
        "- size → اندازه\n"
        "- brand → برند\n"
        "- style → سبک\n\n"
        
        f"Input JSON:\n{json_input}\n\n"
        
        "Output only the translated JSON object with Persian keys and values. "
        "Do not include any explanatory text, markdown formatting, or comments."
    )


def validate_translation_input(state: Dict[str, Any]) -> None:
    """Validate input state for translation processing.
    
    Args:
        state: Current workflow state
        
    Raises:
        TranslationError: If required input is missing or invalid
    """
    if not isinstance(state, dict):
        raise TranslationError("State must be a dictionary")
    
    image_tags_en = state.get("image_tags_en")
    if image_tags_en is None:
        raise TranslationError("'image_tags_en' is required but missing in state")
    
    if not isinstance(image_tags_en, dict):
        raise TranslationError("'image_tags_en' must be a dictionary")
    
    # Check if there's actually content to translate
    if not image_tags_en:
        raise TranslationError("'image_tags_en' is empty - nothing to translate")


def process_translation_result(result: Dict[str, Any], 
                             original_tags: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate translation result.
    
    Args:
        result: Raw result from the AI translation model
        original_tags: Original English tags for fallback
        
    Returns:
        Dict[str, Any]: Processed Persian tags
        
    Raises:
        TranslationError: If result processing fails critically
    """
    try:
        # Extract translated JSON from model response
        translated_tags = result.get("json", {})
        
        # Validate result structure
        if not isinstance(translated_tags, dict):
            # Fallback: return original structure with indication of translation failure
            return {
                "translation_error": "Invalid translation result format",
                "fallback_tags": original_tags
            }
        
        # If translation is empty, provide fallback
        if not translated_tags:
            return {
                "translation_warning": "Empty translation result",
                "fallback_tags": original_tags
            }
        
        # Validate that entities structure is maintained if it exists
        if "entities" in original_tags:
            if "entities" not in translated_tags:
                # Try to find Persian equivalent of entities key
                persian_entities_key = None
                for key in translated_tags.keys():
                    if "موجودیت" in key or "entity" in key.lower() or "entities" in key.lower():
                        persian_entities_key = key
                        break
                
                if persian_entities_key:
                    # Rename to standard Persian key
                    translated_tags["entities"] = translated_tags.pop(persian_entities_key)
                else:
                    # Add warning about missing entities
                    translated_tags["translation_warning"] = "Entities structure may be incomplete"
        
        return translated_tags
        
    except Exception as e:
        # Non-critical error: return fallback with error info
        return {
            "translation_error": str(e),
            "fallback_tags": original_tags,
            "error_type": type(e).__name__
        }


def translate_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for translating English tags to Persian.
    
    This function represents the second processing stage in the workflow,
    where English product tags are translated to Persian while maintaining
    the original structure and semantic meaning.
    
    Args:
        state: Current workflow state containing English tags
        
    Returns:
        Dict[str, Any]: Updated state with Persian translations
        
    Raises:
        TranslationError: If translation fails critically
    
    State Input:
        - image_tags_en (dict): English tags and entities to translate
        
    State Output:
        - image_tags_fa (dict): Translated Persian tags and entities
        - translation_raw (str): Raw model response for debugging
        - translation_metadata (dict): Processing metadata
    """
    try:
        # Validate input state
        validate_translation_input(state)
        
        # Extract English tags from state
        image_tags_en = state["image_tags_en"]
        
        # Initialize the OpenRouter client
        client = OpenRouterClient()
        
        # Build translation prompt
        prompt = build_translation_prompt(image_tags_en)
        
        # Prepare messages for the AI model
        messages = [
            {
                "role": "user",
                "content": [make_text_part(prompt)],
            }
        ]
        
        # Call the AI model for translation
        result = client.call_json(model=TRANSLATE_MODEL, messages=messages)
        
        # Process and validate the translation result
        image_tags_fa = process_translation_result(result, image_tags_en)
        
        # Prepare translation metadata
        translation_metadata = {
            "model_used": TRANSLATE_MODEL,
            "prompt_length": len(prompt),
            "translation_success": "translation_error" not in image_tags_fa,
            "has_raw_response": bool(result.get("text")),
            "parsing_success": result.get("parsing_success", False),
            "original_entities_count": len(image_tags_en.get("entities", [])),
            "translated_entities_count": len(image_tags_fa.get("entities", []))
        }
        
        # Update and return state
        return {
            **state,
            "image_tags_fa": image_tags_fa,
            "translation_raw": result.get("text", ""),
            "translation_metadata": translation_metadata
        }
        
    except Exception as e:
        # Handle errors gracefully by updating state with error information
        error_message = str(e)
        
        # Create fallback translation (copy of English with error marker)
        fallback_translation = {
            "translation_error": error_message,
            "fallback_used": True,
            "original_tags": state.get("image_tags_en", {})
        }
        
        # Create error state update
        error_state = {
            **state,
            "image_tags_fa": fallback_translation,
            "translation_raw": "",
            "translation_metadata": {
                "model_used": TRANSLATE_MODEL,
                "translation_success": False,
                "error_message": error_message,
                "error_type": type(e).__name__,
                "fallback_used": True
            }
        }
        
        # For critical errors, re-raise; for others, continue with fallback
        if isinstance(e, TranslationError):
            # Log error but continue with fallback
            print(f"Translation warning: {error_message}")
            return error_state
        else:
            # Re-raise unexpected errors
            raise TranslationError(
                f"Translation node failed: {error_message}"
            ) from e


# Backward compatibility alias
build_prompt = build_translation_prompt
