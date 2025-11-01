"""
Configuration settings for LangGraph v2 scenarios.

This module contains all configuration constants and settings
for the modular workflow system.
"""
"""
Configuration management for Workflow v2.
Enhanced with multi-provider model client support and centralized model management.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Centralized Model Configuration Dictionary
# Load all models from environment variables with fallback to defaults
MODELS = {
    "vision": os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free"),
    "translate": os.getenv("TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free"),
    "refine": os.getenv("REFINE_MODEL", "qwen/qwen2.5-vl-32b-instruct:free"),
    "conversation": os.getenv("CONVERSATION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free"),
    "merger": os.getenv("MERGER_MODEL", "tngtech/deepseek-r1t2-chimera:free"),
    "tag": os.getenv("TAG_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free"),
    "general": os.getenv("GENERAL_MODEL", "qwen/qwen2.5-vl-32b-instruct:free"),
    "default": os.getenv("DEFAULT_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
}

@dataclass
class ModelConfig:
    """Configuration for model client."""
    provider: str = "openrouter"
    api_key: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    default_model: str = MODELS["default"]

    @classmethod
    def from_env(cls) -> 'ModelConfig':
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv("API_PROVIDER", "openrouter"),
            api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("METIS_API_KEY") or os.getenv("TOGETHER_API_KEY"),
            timeout=int(os.getenv("API_TIMEOUT", "60")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
            default_model=MODELS["default"]
        )

@dataclass
class WorkflowConfig:
    """Main workflow configuration."""
    model: ModelConfig
    logging_level: str = "INFO"
    enable_file_logging: bool = False

    @classmethod
    def from_env(cls) -> 'WorkflowConfig':
        """Create configuration from environment variables."""
        return cls(
            model=ModelConfig.from_env(),
            logging_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
        )

def get_config() -> WorkflowConfig:
    """Get the current workflow configuration."""
    return WorkflowConfig.from_env()

def get_model(model_type: str) -> str:
    """
    Get model name for specific type from centralized configuration.

    Args:
        model_type: Type of model needed (vision, translate, tag, etc.)

    Returns:
        Model name string from environment configuration

    Raises:
        KeyError: If model_type is not configured
    """
    if model_type not in MODELS:
        available_types = ", ".join(MODELS.keys())
        raise KeyError(f"Model type '{model_type}' not found. Available types: {available_types}")

    return MODELS[model_type]

# Alternative model options for fallback (keeping existing structure)
VISION_MODEL_ALTERNATIVES = [
    "qwen/qwen2.5-vl-72b-instruct:free",
    "qwen/qwen2.5-vl-32b-instruct:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "allenai/molmo-7b-d:free"
]

TRANSLATE_MODEL_ALTERNATIVES = [
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free"
]

GENERAL_MODEL_ALTERNATIVES = [
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-chat:free",
    "nvidia/llama-3.1-nemotron-70b-instruct:free"
]
