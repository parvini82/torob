from flask import Flask, jsonify, request
import json
from langgraph_service import run_langgraph

app = Flask(__name__)


@app.route("/generate-tags", methods=["POST"], strict_slashes=False)
def generate_tags():
    """
    Endpoint to extract apparel attributes (Persian JSON) from an image.
    Request body:
        {
            "image_url": "<URL or base64 string>"
        }
    Response:
        {
            "image_url": "<input>",
            "tags_fa": { ... translated JSON ... }
        }
    """
    data = request.get_json(silent=True)
    if data is None and request.data:
        try:
            data = json.loads(request.data)
        except Exception:
            data = None
    if not data or "image_url" not in data:
        return jsonify({"error": "image_url is required"}), 400

    image_url = data["image_url"]

    try:
        # Run LangGraph pipeline
        tags_fa = run_langgraph(image_url)
        return jsonify({"image_url": image_url, "tags_fa": tags_fa}), 200
    except Exception as e:
        # Return detailed error message
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Run Flask app in debug mode
    app.run(host="0.0.0.0", port=5000, debug=True)
