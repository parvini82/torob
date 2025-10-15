from typing import Dict, Any
from .model_client import OpenRouterClient, make_text_part
from .config import TRANSLATE_MODEL


def build_translation_prompt(tags_en: Dict[str, Any]) -> str:
    return (
        "You are a professional translator specialized in e-commerce and apparel products.\n"
        "Translate the following JSON object from English to Persian.\n"
        "Do not change the structure;\n"
        f"Input JSON:\n{tags_en}\n"
        "Output only the translated JSON object, without any extra explanation."
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


