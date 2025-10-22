import base64
import json

import requests

from src.config.settings import API_KEY, MODEL


def prepare_image_input(image_bytes: bytes):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"}


def predict_tags(image_bytes: bytes):
    image_payload = prepare_image_input(image_bytes)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        You are a specialized Named Entity Recognition (NER) model trained to recognize attributes of apparel products from images.
                        Given the input image of a clothing item, your task is to identify and extract all relevant entities and output them in a structured JSON format.
                        Output your results as a JSON object
                        The response must be only in JSON format.
                        give me two outputs one in english one in persian
                        """,
                    },
                    image_payload,
                ],
            }
        ],
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload
    )

    if response.status_code == 200:
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            tags_json = json.loads(content[json_start:json_end])
        except Exception:
            tags_json = {"tags": ["parse_error"], "raw_output": data}
    else:
        raise Exception(f"Request failed with status code {response.status_code}")

    return tags_json
