from flask import Flask, request, jsonify
from config import API_KEY, MODEL
import requests
import base64
import json

app = Flask(__name__)


def prepare_image_input(image_path_or_url):
    if image_path_or_url.startswith("http"):
        return {"type": "image_url", "image_url": image_path_or_url}
    else:
        with open(image_path_or_url, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"}


def get_tags_from_model(image_path_or_url):
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
                        "text": (
                            """
                                    You are a specialized Named Entity Recognition (NER) model trained to recognize attributes of apparel products from images.

                                    Given the input image of a clothing item, your task is to identify and extract all relevant entities  and output them in a structured JSON format.

                                    Output your results as a JSON object

                                    The response must be **only** in JSON format. Do not add any extra explanation or text outside of the JSON.\
                                    give me two outputs one in english one in persian
                                    """
                        ),
                    },
                    prepare_image_input(image_path_or_url)
                ],
            }
        ],
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            tags_json = json.loads(content[json_start:json_end])
        except Exception as e:
            tags_json = {"tags": ["parse_error"], "raw_output": data}
    else:
        raise Exception(f"Request failed with status code {response.status_code}")

    return tags_json


@app.route('/generate-tags/', methods=['POST'])
def generate_tags():
    data = request.get_json()

    if not data or 'image_url' not in data:
        return jsonify({"error": "image_url is required"}), 400

    image_url = data['image_url']

    try:
        tags = get_tags_from_model(image_url)
        return jsonify({
            "image_url": image_url,
            "tags": tags
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
