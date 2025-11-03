from typing import Any, Dict

from .config import VISION_MODEL
from .model_client import (
    MetisClient,  # Using MetisClient instead of OpenRouterClient
    make_image_part,
    make_text_part,
)


def build_prompt() -> str:
    return (
        "You are an expert visual Named Entity Recognition (NER) model specialized "
        "in analyzing apparel and fashion product images.\n\n"
        "Your task is to analyze the given product image and extract all relevant "
        "entities that describe the item. Focus on identifying:\n"
        "- Product type (e.g., shirt, dress, pants, shoes, bag)\n"
        "- Colors (primary and secondary colors visible)\n"
        "- Materials/fabric (e.g., cotton, leather, denim, silk)\n"
        "- Patterns (e.g., solid, striped, floral, checkered)\n"
        "- Style features (e.g., collar type, sleeve length, fit)\n"
        "- Brand information (if clearly visible)\n"
        "- Size indicators (if visible on tags or labels)\n"
        "- Special features (e.g., pockets, buttons, zippers)\n\n"
        "Return the analysis as a structured JSON object with English values only. "
        "Use concise, standardized terms for entity values.\n\n"
        "Example output format:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "product_type", "values": ["t-shirt"]},\n'
        '    {"name": "color", "values": ["blue", "white"]},\n'
        '    {"name": "material", "values": ["cotton"]},\n'
        '    {"name": "pattern", "values": ["solid"]},\n'
        '    {"name": "sleeve_type", "values": ["short-sleeve"]}\n'
        '    {"name": "gender", "values": ["male"]}\n'
        "  ]\n"
        "}\n\n"
        "IMPORTANT: Respond with valid JSON only. Do not include any explanatory "
        "text, markdown formatting, or additional commentary."
    )


def image_to_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    image_url = state.get("image_url")
    if not image_url:
        raise ValueError("image_to_tags_node: 'image_url' is missing in state")

    client = MetisClient()  # Changed to MetisClient
    prompt = build_prompt()

    messages = [
        {
            "role": "user",
            "content": [
                make_text_part(prompt),
                make_image_part(image_url),
            ],
        }
    ]

    result = client.call_json(model=VISION_MODEL, messages=messages)
    image_tags_en = result["json"] or {}

    return {
        **state,
        "image_tags_en": image_tags_en,
        "raw_response": result.get("text"),
    }