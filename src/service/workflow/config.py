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
METIS_BASE_URL: str = os.getenv("METIS_BASE_URL", "")

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
TRANSLATE_MODEL: str = os.getenv(
    "TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free"
)



IMAGE_TAG_PROMPT_TEMPLATE = """
You are an expert visual Named Entity Recognition (NER) model specialized 
in analyzing apparel and fashion product images.

Your task is to analyze the given product image and extract all relevant 
entities that describe the item. Focus on identifying:
- Product type (e.g., shirt, dress, pants, shoes, bag)
- Colors (primary and secondary colors visible)
- Materials/fabric (e.g., cotton, leather, denim, silk)
- Patterns (e.g., solid, striped, floral, checkered)
- Style features (e.g., collar type, sleeve length, fit)
- Brand information (if clearly visible)
- Size indicators (if visible on tags or labels)
- Special features (e.g., pockets, buttons, zippers)

Return the analysis as a structured JSON object with English values only. 
Use concise, standardized terms for entity values.

Example output format:
{
  "entities": [
    {"name": "product_type", "values": ["t-shirt"]},
    {"name": "color", "values": ["blue", "white"]},
    {"name": "material", "values": ["cotton"]},
    {"name": "pattern", "values": ["solid"]},
    {"name": "sleeve_type", "values": ["short-sleeve"]}
  ]
}

IMPORTANT: Respond with valid JSON only. Do not include any explanatory 
text, markdown formatting, or additional commentary.
"""

TRANSLATION_PROMPT_TEMPLATE = """
You are a professional translator specialized in e-commerce and apparel products. 
Your expertise includes Persian/Farsi translation of fashion and product terminology.

Task: Translate the following JSON object from English to Persian (Farsi). 
Translate both entity names (keys) and their values while maintaining 
the exact JSON structure.

Translation Guidelines:
- Maintain the original JSON structure exactly
- Translate entity names to appropriate Persian equivalents
- Translate all values to natural Persian terms
- Use standard Persian terminology for clothing and fashion items
- Preserve arrays and nested structures
- Ensure the output is valid JSON

Common translations for reference:
- color → رنگ
- material → جنس
- product_type → نوع کلی
- pattern → طرح
- size → اندازه
- brand → برند
- style → سبک

Input JSON:
{tags_en}"

Output only the translated JSON object with Persian keys and values. 
Do not include any explanatory text, markdown formatting, or comments.
"""
