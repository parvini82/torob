from typing import Dict, Any
from .model_client import OpenRouterClient, make_text_part
from .config import TRANSLATE_MODEL


def build_translation_prompt(tags_en: Dict[str, Any]) -> str:
    return (
        "You are a professional translator specialized in e-commerce and apparel products. "
        "Your expertise includes Persian/Farsi translation of fashion and product terminology.\n\n"
        
        "Task: Translate the following JSON object from English to Persian (Farsi). "
        "Translate both entity names (keys) and their values while maintaining "
        "the exact JSON structure.\n\n"
        
        "Translation Guidelines:\n"
        "- Maintain the original JSON structure exactly\n"
        "- Translate entity names to appropriate Persian equivalents\n"
        "- Translate all values to natural Persian terms\n"
        "- Use standard Persian terminology for clothing and fashion items\n"
        "- Preserve arrays and nested structures\n"
        "- Ensure the output is valid JSON\n\n"
        
        "Common translations for reference:\n"
        "- color → رنگ\n"
        "- material → جنس\n"
        "- product_type → نوع کلی\n"
        "- pattern → طرح\n"
        "- size → اندازه\n"
        "- brand → برند\n"
        "- style → سبک\n\n"
        
        f"Input JSON:\n{tags_en}\n\n"
        
        "Output only the translated JSON object with Persian keys and values. "
        "Do not include any explanatory text, markdown formatting, or comments."
    )


def translate_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    image_tags_en = state.get("image_tags_en")
    if not image_tags_en:
        raise ValueError("translate_tags_node: 'image_tags_en' is missing in state")

    client = OpenRouterClient()
    prompt = build_translation_prompt(image_tags_en)

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

