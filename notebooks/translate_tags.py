from typing import Any, Dict

from model_client import OpenRouterClient, make_text_part

from config import TRANSLATE_MODEL


def build_translation_prompt(tags_en: Dict[str, Any]) -> str:
    """
    Build the translation prompt based on English tags.
    """
    return (
        "You are a professional translator specialized in e-commerce and apparel products.\n"
        "Translate the following JSON object from English to Persian, preserving the keys.\n"
        "Do not change the structure; only translate the values.\n"
        f"Input JSON:\n{tags_en}\n"
        "Output only the translated JSON object, without any extra explanation."
    )


def translate_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node:
    Input state: {'image_tags_en': dict}
    Output state: {'image_tags_fa': dict, 'translation_raw': str}
    """
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

    # Call translation model
    result = client.call_json(model=TRANSLATE_MODEL, messages=messages)
    image_tags_fa = result["json"] or {}
    print("\n🧩 [DEBUG] Image Node Output (EN):", image_tags_en)

    return {
        **state,
        "image_tags_fa": image_tags_fa,
        "translation_raw": result.get("text"),
    }
