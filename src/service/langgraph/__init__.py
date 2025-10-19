"""LangGraph service module for AI-powered image processing pipeline.

This module provides a complete workflow for processing product images through
multiple AI models to extract and translate product attributes and tags.

The pipeline consists of three main stages:
1. Image Analysis: Extract entities and attributes from product images
2. Translation: Convert English results to Persian/Farsi
3. Result Merging: Consolidate and format final output

Example:
    from src.service.langgraph import run_langgraph_on_url
    
    result = run_langgraph_on_url("https://example.com/product.jpg")
    print(result["persian"]["entities"])
"""

from .langgraph_service import (
    ImageProcessingPipeline,
    run_langgraph_on_url,
    run_langgraph_on_bytes,
    LangGraphError
)
from .model_client import (
    OpenRouterClient,
    OpenRouterError,
    make_image_part,
    make_text_part,
    extract_json_from_text
)
from .config import (
    VISION_MODEL,
    TRANSLATE_MODEL,
    get_config_summary
)

__all__ = [
    # Main pipeline interface
    "ImageProcessingPipeline",
    "run_langgraph_on_url",
    "run_langgraph_on_bytes",
    "LangGraphError",
    
    # Model client utilities
    "OpenRouterClient",
    "OpenRouterError",
    "make_image_part",
    "make_text_part",
    "extract_json_from_text",
    
    # Configuration
    "VISION_MODEL",
    "TRANSLATE_MODEL",
    "get_config_summary"
]
