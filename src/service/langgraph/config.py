import os

from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))

OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_TITLE: str = os.getenv("OPENROUTER_SITE_TITLE", "")

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
TRANSLATE_MODEL: str = os.getenv("TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free")
