"""Configuration settings for the LangGraph service.

This module manages configuration parameters specific to the LangGraph
image processing pipeline, including API endpoints, model selections,
and processing timeouts.
"""

import os
from typing import Optional


def get_env_int(key: str, default: int) -> int:
    """Get integer environment variable with validation.
    
    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        
    Returns:
        int: Environment variable value or default
    """
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_str(key: str, default: str = "", required: bool = False) -> str:
    """Get string environment variable with validation.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        required: Whether the variable is required
        
    Returns:
        str: Environment variable value or default
        
    Raises:
        ValueError: If required variable is not set
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value


# API Configuration
# OpenRouter API key for model access (required)
OPENROUTER_API_KEY: str = get_env_str("OPENROUTER_API_KEY", required=True)

# OpenRouter API base URL for chat completions
OPENROUTER_BASE_URL: str = get_env_str(
    "OPENROUTER_BASE_URL", 
    default="https://openrouter.ai/api/v1/chat/completions"
)

# Request timeout in seconds for API calls
REQUEST_TIMEOUT: int = get_env_int("REQUEST_TIMEOUT", default=60)

# Optional site metadata for OpenRouter analytics
OPENROUTER_SITE_URL: str = get_env_str("OPENROUTER_SITE_URL", default="")
OPENROUTER_SITE_TITLE: str = get_env_str("OPENROUTER_SITE_TITLE", default="Torob Image Analyzer")

# Model Configuration
# Vision model for image analysis and entity extraction
VISION_MODEL: str = get_env_str(
    "VISION_MODEL", 
    default="qwen/qwen2.5-vl-72b-instruct:free"
)

# Translation model for multilingual tag generation
TRANSLATE_MODEL: str = get_env_str(
    "TRANSLATE_MODEL", 
    default="qwen/qwen2.5-7b-instruct:free"
)

# Processing Configuration
# Maximum number of retries for failed API requests
MAX_RETRIES: int = get_env_int("MAX_RETRIES", default=3)

# Retry delay in seconds between failed requests
RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))

# Maximum image size in bytes (10MB default)
MAX_IMAGE_SIZE: int = get_env_int("MAX_IMAGE_SIZE", default=10 * 1024 * 1024)

# Supported image formats
SUPPORTED_IMAGE_FORMATS: frozenset = frozenset([
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
])


def validate_config() -> None:
    """Validate configuration settings.
    
    Raises:
        ValueError: If any configuration is invalid
    """
    # Validate API key
    if not OPENROUTER_API_KEY.strip():
        raise ValueError("OPENROUTER_API_KEY is required but not set")
    
    # Validate timeout
    if REQUEST_TIMEOUT <= 0:
        raise ValueError(f"REQUEST_TIMEOUT must be positive, got {REQUEST_TIMEOUT}")
    
    # Validate models
    if not VISION_MODEL or "/" not in VISION_MODEL:
        raise ValueError(f"Invalid VISION_MODEL format: {VISION_MODEL}")
    
    if not TRANSLATE_MODEL or "/" not in TRANSLATE_MODEL:
        raise ValueError(f"Invalid TRANSLATE_MODEL format: {TRANSLATE_MODEL}")
    
    # Validate retry settings
    if MAX_RETRIES < 0:
        raise ValueError(f"MAX_RETRIES must be non-negative, got {MAX_RETRIES}")
    
    if RETRY_DELAY < 0:
        raise ValueError(f"RETRY_DELAY must be non-negative, got {RETRY_DELAY}")


def get_config_summary() -> dict:
    """Get configuration summary (excluding sensitive data).
    
    Returns:
        dict: Configuration summary with sensitive values masked
    """
    return {
        "openrouter_base_url": OPENROUTER_BASE_URL,
        "request_timeout": REQUEST_TIMEOUT,
        "vision_model": VISION_MODEL,
        "translate_model": TRANSLATE_MODEL,
        "max_retries": MAX_RETRIES,
        "retry_delay": RETRY_DELAY,
        "max_image_size_mb": MAX_IMAGE_SIZE // (1024 * 1024),
        "api_key_configured": bool(OPENROUTER_API_KEY),
        "site_metadata": {
            "url": OPENROUTER_SITE_URL,
            "title": OPENROUTER_SITE_TITLE
        }
    }


# Validate configuration on module import
validate_config()
