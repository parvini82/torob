"""Application configuration settings module.

This module manages application-wide configuration settings including
API credentials, model configurations, and environment-specific parameters.
All settings are loaded from environment variables to ensure security
and deployment flexibility.
"""

import os
from typing import Optional


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


def get_env_variable(var_name: str, default: Optional[str] = None, required: bool = False) -> str:
    """Safely retrieve environment variable with validation.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if variable is not set
        required: Whether the variable is required (raises error if missing)
        
    Returns:
        str: The environment variable value
        
    Raises:
        ConfigurationError: If required variable is missing
    """
    value = os.environ.get(var_name, default)
    
    if required and not value:
        raise ConfigurationError(f"Required environment variable '{var_name}' is not set")
    
    return value or ""


# API Configuration
# OpenRouter API key for accessing language models
API_KEY = get_env_variable("OPENROUTER_API_KEY", required=True)

# Default model configuration for OpenRouter
# Uses Qwen 2.5 Vision Language model as default with free tier
MODEL = get_env_variable(
    "OPENROUTER_MODEL", 
    default="qwen/qwen2.5-vl-72b-instruct:free"
)

# Server Configuration
# Default server host (can be overridden via environment)
SERVER_HOST = get_env_variable("SERVER_HOST", default="0.0.0.0")

# Default server port (can be overridden via environment)
SERVER_PORT = int(get_env_variable("SERVER_PORT", default="8000"))

# Application Configuration
# Application name and version
APP_NAME = get_env_variable("APP_NAME", default="Torob API")
APP_VERSION = get_env_variable("APP_VERSION", default="1.0.0")

# Debug mode configuration (useful for development)
DEBUG_MODE = get_env_variable("DEBUG_MODE", default="false").lower() == "true"

# Logging Configuration
# Log level for application logging
LOG_LEVEL = get_env_variable("LOG_LEVEL", default="INFO")

# Log format configuration
LOG_FORMAT = get_env_variable(
    "LOG_FORMAT", 
    default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def validate_configuration() -> None:
    """Validate all configuration settings.
    
    Performs comprehensive validation of all configuration parameters
    to ensure the application can start successfully.
    
    Raises:
        ConfigurationError: If any configuration is invalid
    """
    # Validate API key is not empty
    if not API_KEY.strip():
        raise ConfigurationError("OPENROUTER_API_KEY cannot be empty")
    
    # Validate model name format
    if not MODEL or "/" not in MODEL:
        raise ConfigurationError(f"Invalid model format: {MODEL}")
    
    # Validate server port range
    if not (1 <= SERVER_PORT <= 65535):
        raise ConfigurationError(f"Invalid server port: {SERVER_PORT}")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL.upper() not in valid_log_levels:
        raise ConfigurationError(f"Invalid log level: {LOG_LEVEL}")


def get_configuration_summary() -> dict:
    """Get a summary of current configuration (excluding sensitive data).
    
    Returns:
        dict: Configuration summary with sensitive values masked
    """
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "model": MODEL,
        "server_host": SERVER_HOST,
        "server_port": SERVER_PORT,
        "debug_mode": DEBUG_MODE,
        "log_level": LOG_LEVEL,
        "api_key_configured": bool(API_KEY),  # Don't expose actual key
    }


# Perform initial configuration validation when module is imported
try:
    validate_configuration()
except ConfigurationError as e:
    # Re-raise with more context
    raise ConfigurationError(
        f"Configuration validation failed: {e}. "
        f"Please check your environment variables."
    ) from e
