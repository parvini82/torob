from typing import Any, Dict

from .config import TRANSLATE_MODEL
from .model_client import OpenRouterClient, make_text_part


def build_translation_prompt(data: Dict[str, Any]) -> str:
    return (
        "You are a product understanding and translation model specialized in fashion and apparel.\n\n"
        "Inputs:\n"
        "- image_tags_en: structured English tags from a vision model (product_type, color, material, style, etc.)\n"
        "- serper_results: Persian search titles/snippets about the same image.\n\n"
        "Goal:\n"
        "Use both inputs to produce a refined Persian JSON description of the product.\n"
        "Infer what the product is mainly from VLM tags, and learn how Persian speakers actually refer to it from Serper titles.\n\n"
        "Rules:\n"
        "1. Identify the product type using VLM tags as the main evidence.\n"
        "2. Analyze the Persian titles to detect common or cultural terms used for this product.\n"
        "3. Output only a clean Persian JSON object.\n\n"
        f"{data}\n\n"
        "Example output format:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "", "values": ["","",...]},\n'
        "  ]\n"
        "}\n\n"
        "Output (Persian JSON only):"
    )

def translate_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    image_tags_en = state.get("image_tags_en")
    serpapi_results = state.get("serpapi_results", {})

    if not image_tags_en:
        raise ValueError("translate_tags_node: 'image_tags_en' is missing in state")

    client = OpenRouterClient()
    combined_input = {
        "image_tags_en": image_tags_en,
        "serpapi_results": serpapi_results,
    }
    prompt = build_translation_prompt(combined_input)

    messages = [
        {
            "role": "user",
            "content": [make_text_part(prompt)],
        }
    ]

    result = client.call_json(model=TRANSLATE_MODEL, messages=messages)
    image_tags_fa = result["json"] or {}

    return {
        **state,
        "image_tags_fa": image_tags_fa,
        "translation_raw": result.get("text"),
    }