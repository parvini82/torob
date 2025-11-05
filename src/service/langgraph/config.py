import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_TITLE: str = os.getenv("OPENROUTER_SITE_TITLE", "")

METIS_API_KEY: str = os.getenv("METIS_API_KEY", "")
METIS_BASE_URL: str = "https://api.metisai.ir/openai/v1/chat/completions"
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
METIS_SITE_URL: str = os.getenv("METIS_SITE_URL", "")
METIS_SITE_TITLE: str = os.getenv("METIS_SITE_TITLE", "")

# Model configurations for different modes
MODEL_CONFIG = {
    "fast": {
        "vision_model": "gpt-4o-mini",
        "translate_model": "gpt-4o-mini",
        "use_serpapi": False
    },
    "reasoning": {
        "vision_model": "gpt-4o",
        "translate_model": "gpt-4o",
        "use_serpapi": False
    },
    "advanced_reasoning": {
        "vision_model": "gpt-4o",
        "translate_model": "gpt-5",
        "use_serpapi": True
    }
}

def get_vision_model(mode: str = "fast") -> str:
    """Get vision model based on mode"""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["vision_model"]

def get_translate_model(mode: str = "fast") -> str:
    """Get translate model based on mode"""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["translate_model"]

def should_use_serpapi(mode: str = "fast") -> bool:
    """Check if serpapi should be used based on mode"""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["use_serpapi"]

# Backward compatibility - default to fast mode
VISION_MODEL: str = get_vision_model("fast")
TRANSLATE_MODEL: str = get_translate_model("fast")
