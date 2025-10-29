from typing import Any, Dict

from .config import TRANSLATE_MODEL
from .model_client import OpenRouterClient, make_text_part


def build_translation_prompt(data: Dict[str, Any]) -> str:
    print(data)
    return (
        "You are a product-content expert for apparel e-commerce.\n"
        "You will receive two inputs:\n"
        "1) `image_tags_en`: JSON tags extracted by a vision model (English)\n"
        "2) `serpapi_results`: Raw Google Reverse Image Search results (JSON)\n\n"
        "Your job is to CONSOLIDATE these into a refined understanding of the product and then OUTPUT ONLY the Persian JSON.\n\n"
        "Instructions:\n"
        "- Start from `image_tags_en` as the primary (visual) source.\n"
        "- Use `serpapi_results` to confirm or add missing obvious facts when multiple titles/snippets agree.\n"
        "- Resolve conflicts conservatively: prefer visual evidence; if uncertain, omit rather than guess.\n"
        "- Keep the schema/keys consistent with `image_tags_en` where possible (product attributes only).\n"
        "- Remove marketplace noise (seller names, prices, shipping, emojis, marketing fluff).\n"
        "- Translate FINAL refined tags to Persian with natural retail wording.\n"
        "- Output ONLY valid JSON with Persian keys AND Persian values. No extra text.\n\n"
        "Input payload follows as JSON. Parse and proceed:\n\n"
        f"{data}\n\n"
        "Output (Persian JSON only):"
        "Example output format:\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "", "values": ["","",...]},\n'
        "  ]\n"
        "}\n\n"
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