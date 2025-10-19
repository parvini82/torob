"""Image analysis and tag extraction node for the LangGraph pipeline.

This module handles the initial stage of image processing where product images
are analyzed by AI vision models to extract relevant entities and attributes.
It serves as the first node in the LangGraph workflow pipeline.
"""

from typing import Any, Dict, Optional
from .config import VISION_MODEL
from .model_client import (
    OpenRouterClient,
    make_image_part,
    make_text_part,
)


class ImageAnalysisError(Exception):
    """Custom exception for image analysis errors."""
    pass


def build_image_analysis_prompt() -> str:
    """Build the system prompt for image analysis and entity extraction.
    
    Creates a comprehensive prompt that guides the AI model to analyze
    product images and extract relevant entities in a structured format.
    
    Returns:
        str: Complete system prompt for image analysis
    """
    return (
        "You are an expert visual Named Entity Recognition (NER) model specialized "
        "in analyzing apparel and fashion product images.\n\n"
        
        "Your task is to analyze the given product image and extract all relevant "
        "entities that describe the item. Focus on identifying:\n"
        "- Product type (e.g., shirt, dress, pants, shoes, bag)\n"
        "- Colors (primary and secondary colors visible)\n"
        "- Materials/fabric (e.g., cotton, leather, denim, silk)\n"
        "- Patterns (e.g., solid, striped, floral, checkered)\n"
        "- Style features (e.g., collar type, sleeve length, fit)\n"
        "- Brand information (if clearly visible)\n"
        "- Size indicators (if visible on tags or labels)\n"
        "- Special features (e.g., pockets, buttons, zippers)\n\n"
        
        "Return the analysis as a structured JSON object with English values only. "
        "Use concise, standardized terms for entity values.\n\n"
        
        "Example output format:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "product_type", "values": ["t-shirt"]},\n'
        '    {"name": "color", "values": ["blue", "white"]},\n'
        '    {"name": "material", "values": ["cotton"]},\n'
        '    {"name": "pattern", "values": ["solid"]},\n'
        '    {"name": "sleeve_type", "values": ["short-sleeve"]}\n'
        "  ]\n"
        "}\n\n"
        
        "IMPORTANT: Respond with valid JSON only. Do not include any explanatory "
        "text, markdown formatting, or additional commentary."
    )


def validate_image_analysis_input(state: Dict[str, Any]) -> None:
    """Validate input state for image analysis.
    
    Args:
        state: Current workflow state
        
    Raises:
        ImageAnalysisError: If required input is missing or invalid
    """
    if not isinstance(state, dict):
        raise ImageAnalysisError("State must be a dictionary")
    
    image_url = state.get("image_url")
    if not image_url:
        raise ImageAnalysisError("'image_url' is required but missing in state")
    
    if not isinstance(image_url, str):
        raise ImageAnalysisError("'image_url' must be a string")
    
    # Basic URL validation
    if not (image_url.startswith(("http://", "https://", "data:"))):
        raise ImageAnalysisError(
            "'image_url' must be a valid HTTP/HTTPS URL or data URI"
        )


def process_image_analysis_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate the image analysis result.
    
    Args:
        result: Raw result from the AI model
        
    Returns:
        Dict[str, Any]: Processed and validated entities
        
    Raises:
        ImageAnalysisError: If result processing fails
    """
    try:
        # Extract JSON result from model response
        extracted_entities = result.get("json", {})
        
        # Validate result structure
        if not isinstance(extracted_entities, dict):
            raise ImageAnalysisError(
                f"Expected dict result, got {type(extracted_entities)}"
            )
        
        # Ensure entities are in the expected format
        if "entities" in extracted_entities:
            entities_list = extracted_entities["entities"]
            if not isinstance(entities_list, list):
                raise ImageAnalysisError(
                    "'entities' field must be a list"
                )
            
            # Validate entity structure
            for i, entity in enumerate(entities_list):
                if not isinstance(entity, dict):
                    raise ImageAnalysisError(
                        f"Entity {i} must be a dictionary"
                    )
                if "name" not in entity or "values" not in entity:
                    raise ImageAnalysisError(
                        f"Entity {i} must have 'name' and 'values' fields"
                    )
                if not isinstance(entity["values"], list):
                    raise ImageAnalysisError(
                        f"Entity {i} 'values' must be a list"
                    )
        
        return extracted_entities
        
    except Exception as e:
        if isinstance(e, ImageAnalysisError):
            raise
        raise ImageAnalysisError(
            f"Failed to process image analysis result: {str(e)}"
        ) from e


def image_to_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for image analysis and tag extraction.
    
    This function represents the first processing stage in the workflow,
    where product images are analyzed to extract relevant entities and attributes.
    
    Args:
        state: Current workflow state containing image_url
        
    Returns:
        Dict[str, Any]: Updated state with extracted English tags
        
    Raises:
        ImageAnalysisError: If image analysis fails at any stage
    
    State Input:
        - image_url (str): URL or data URI of the image to analyze
        
    State Output:
        - image_tags_en (dict): Extracted entities in English
        - raw_response (str): Raw model response for debugging
        - analysis_metadata (dict): Processing metadata
    """
    try:
        # Validate input state
        validate_image_analysis_input(state)
        
        # Extract image URL from state
        image_url = state["image_url"]
        
        # Initialize the OpenRouter client
        client = OpenRouterClient()
        
        # Build analysis prompt
        prompt = build_image_analysis_prompt()
        
        # Prepare messages for the AI model
        messages = [
            {
                "role": "user",
                "content": [
                    make_text_part(prompt),
                    make_image_part(image_url),
                ],
            }
        ]
        
        # Call the AI model for image analysis
        result = client.call_json(model=VISION_MODEL, messages=messages)
        
        # Process and validate the result
        image_tags_en = process_image_analysis_result(result)
        
        # Prepare analysis metadata
        analysis_metadata = {
            "model_used": VISION_MODEL,
            "prompt_length": len(prompt),
            "analysis_success": True,
            "entities_extracted": len(image_tags_en.get("entities", [])),
            "has_raw_response": bool(result.get("text"))
        }
        
        # Update and return state
        return {
            **state,
            "image_tags_en": image_tags_en,
            "raw_response": result.get("text", ""),
            "analysis_metadata": analysis_metadata
        }
        
    except Exception as e:
        # Handle errors gracefully by updating state with error information
        error_message = str(e)
        
        # Create error state update
        error_state = {
            **state,
            "image_tags_en": {},  # Empty result on error
            "raw_response": "",
            "analysis_metadata": {
                "model_used": VISION_MODEL,
                "analysis_success": False,
                "error_message": error_message,
                "error_type": type(e).__name__
            }
        }
        
        # Re-raise as ImageAnalysisError for upstream handling
        if isinstance(e, ImageAnalysisError):
            raise
        raise ImageAnalysisError(
            f"Image analysis node failed: {error_message}"
        ) from e


# Backward compatibility alias
build_prompt = build_image_analysis_prompt
