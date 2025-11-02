import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------------------------------------------------
# OpenRouter configuration
# -------------------------------------------------------------------------
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "").strip()
OPENROUTER_SITE_TITLE: str = os.getenv("OPENROUTER_SITE_TITLE", "").strip()

# -------------------------------------------------------------------------
# Model configuration per mode
# -------------------------------------------------------------------------
MODEL_CONFIG = {
    "fast": {
        "vision_model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "translate_model": "tngtech/deepseek-r1t2-chimera:free",
        "use_serpapi": True,
    },
    "reasoning": {
        "vision_model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "translate_model": "tngtech/deepseek-r1t2-chimera:free",
        "use_serpapi": False,
    },
    "advanced_reasoning": {
        "vision_model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "translate_model": "tngtech/deepseek-r1t2-chimera:free",
        "use_serpapi": True,
    },
}

# -------------------------------------------------------------------------
# Accessor functions
# -------------------------------------------------------------------------
def get_vision_model(mode: str = "fast") -> str:
    """Return the vision model for the specified mode."""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["vision_model"]

def get_translate_model(mode: str = "fast") -> str:
    """Return the translation model for the specified mode."""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["translate_model"]

def should_use_serpapi(mode: str = "fast") -> bool:
    """Return True if SerpAPI should be used for the specified mode."""
    return MODEL_CONFIG.get(mode, MODEL_CONFIG["fast"])["use_serpapi"]

# -------------------------------------------------------------------------
# Default fallbacks (for backward compatibility)
# -------------------------------------------------------------------------
VISION_MODEL: str = get_vision_model("fast")
TRANSLATE_MODEL: str = get_translate_model("fast")
