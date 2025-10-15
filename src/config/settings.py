import os

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen2.5-vl-72b-instruct:free")

if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in environment")
