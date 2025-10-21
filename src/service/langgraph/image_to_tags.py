from typing import Any, Dict

from .config import VISION_MODEL
from .model_client import (
    OpenRouterClient,
    make_image_part,
    make_text_part,
)


def build_prompt() -> str:
    return (
        "You are an expert visual NER model specialized in apparel understanding.\n"
        "Analyze the given product image and extract key entities describing it.\n"
        "Return the result as a structured JSON with short English values.\n"
        "Example output:\n"
        "{"
        '"brand": "Nike", ...'
        "}\n"
        "Output strictly JSON only, with no explanations or extra text."
    )


def image_to_tags_node(state: Dict[str, Any]) -> Dict[str, Any]:
    image_url = state.get("image_url")
    if not image_url:
        raise ValueError("image_to_tags_node: 'image_url' is missing in state")

    client = OpenRouterClient()
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