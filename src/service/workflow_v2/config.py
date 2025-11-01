"""
Configuration settings for LangGraph v2 scenarios.

This module contains all configuration constants and settings
for the modular workflow system.
"""
"""
Configuration management for Workflow v2.
Enhanced with multi-provider model client support.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()

@dataclass
class ModelConfig:
    """Configuration for model client."""
    provider: str = "openrouter"
    api_key: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    default_model: str = "qwen/qwen2.5-vl-32b-instruct:free"

    @classmethod
    def from_env(cls) -> 'ModelConfig':
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv("API_PROVIDER", "openrouter"),
            api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("METIS_API_KEY") or os.getenv("TOGETHER_API_KEY"),
            timeout=int(os.getenv("API_TIMEOUT", "60")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
            default_model=os.getenv("DEFAULT_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
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



# Node execution settings
# DEFAULT_TIMEOUT = 30  # seconds
# MAX_RETRIES = 3
# LOG_LEVEL = "INFO"

# Workflow settings
# DEFAULT_STATE_KEYS = ["execution_id", "step_count", "image_url", "errors"]



# Alternative model options for fallback
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



