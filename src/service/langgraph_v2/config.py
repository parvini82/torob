"""
Configuration settings for LangGraph v2 scenarios.

This module contains all configuration constants and settings
for the modular workflow system.
"""

# Model configurations (using same as original)
VISION_MODEL = "google/gemini-flash-1.5"
TRANSLATE_MODEL = "anthropic/claude-3.5-sonnet"
GENERAL_MODEL = "anthropic/claude-3.5-sonnet"

# Node execution settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
LOG_LEVEL = "INFO"

# Workflow settings
DEFAULT_STATE_KEYS = [
    "execution_id",
    "step_count",
    "image_url",
    "errors"
]

# Prompts and templates
CAPTION_PROMPT_TEMPLATE = """
You are an expert image analyst specialized in creating detailed, descriptive captions for product images.

Analyze the given image and create a comprehensive caption that describes:
- The main product or item shown
- Visual characteristics (colors, shapes, textures)
- Notable features or details
- Context or setting if relevant

Keep the caption factual, detailed, and suitable for further analysis.
Respond with only the caption text, no additional formatting or explanation.
"""

TAG_FROM_CAPTION_PROMPT_TEMPLATE = """
You are an expert at extracting structured product information from descriptive text.

Given the following product description, extract relevant product tags and attributes.
Focus on identifying:
- Product type and category
- Colors and visual properties
- Materials and textures
- Style and design features
- Any other relevant product attributes

Product Description:
{caption}

Return the analysis as a structured JSON object with English values only.
Use concise, standardized terms for all values.

Example output format:
{{
  "entities": [
    {{"name": "product_type", "values": ["dress"]}},
    {{"name": "color", "values": ["red", "blue"]}},
    {{"name": "material", "values": ["cotton"]}},
    {{"name": "style", "values": ["casual"]}}
  ]
}}

IMPORTANT: Respond with valid JSON only.
"""

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
{{
  "entities": [
    {{"name": "product_type", "values": ["t-shirt"]}},
    {{"name": "color", "values": ["blue", "white"]}},
    {{"name": "material", "values": ["cotton"]}},
    {{"name": "pattern", "values": ["solid"]}},
    {{"name": "sleeve_type", "values": ["short-sleeve"]}}
  ]
}}

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
{tags_json}

Output only the translated JSON object with Persian keys and values. 
Do not include any explanatory text, markdown formatting, or comments.
"""

REFINEMENT_PROMPT_TEMPLATE = """
You are an expert product analyst tasked with refining and improving product tag extraction results.

You have been provided with:
1. An original product image
2. Previously extracted tags from the image

Your task is to:
- Review the existing tags for accuracy and completeness
- Add any missing important details you can identify from the image
- Remove or correct any inaccurate tags
- Ensure consistency in naming and formatting
- Improve the overall quality of the tag extraction

Previous tags:
{previous_tags}

Please analyze the image again and provide refined, improved tags using the same JSON structure.
Focus on accuracy, completeness, and consistency.

Return the refined analysis as a structured JSON object with English values only.

IMPORTANT: Respond with valid JSON only.
"""