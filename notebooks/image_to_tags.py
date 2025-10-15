from typing import Dict, Any

from model_client import (
    OpenRouterClient,
    make_image_part,
    make_text_part,
)

from config import VISION_MODEL


def build_prompt() -> str:
    """
    prompt for NER
    """
    return (
        "You are an expert visual NER model specialized in apparel understanding.\n"
        "Analyze the given product image and extract key entities describing it.\n"
        "Return the result as a structured JSON with short English values.\n"
        "Example output:\n"
        "{"
        "\"brand\": \"Nike\", "
        "\"category\": \"Sneakers\", "
        "\"color\": \"White\", "
        "\"gender\": \"Men\", "
        "\"material\": \"Leather\""
        "}\n"
        "Output strictly JSON only, with no explanations or extra text."
    )


def image_to_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node:
    Input state: {'image_url': str}
    Output state: {'image_tags_en': dict, 'raw_response': str}
    """
    image_url = state.get("image_url")
    if not image_url:
        raise ValueError("image_to_tags_node: 'image_url' is missing in state")

    client = OpenRouterClient()
    prompt = build_prompt()

    # (text + image)
    messages = [
        {
            "role": "user",
            "content": [
                make_text_part(prompt),
                make_image_part(image_url),
            ],
        }
    ]

    # recalling the vision model
    result = client.call_json(model=VISION_MODEL, messages=messages)
    image_tags_en = result["json"] or {}
    print("\n🧩 [DEBUG] Image Node Output (EN):", image_tags_en)
    return {
        **state,
        "image_tags_en": image_tags_en,
        "raw_response": result.get("text"),
    }
