import os
import requests
from typing import Any, Dict, List


def serpapi_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reverse image search via SerpAPI (Google Reverse Image).
    Cleans response: keeps only titles from image_results and organic_results.
    """

    image_url = state.get("image_url")

    # SerpAPI needs a publicly reachable URL, not a data URI.
    if not image_url or str(image_url).startswith("data:"):
        state["serpapi_results"] = {
            "status": "skipped",
            "reason": "image_url is not a public URL (data URI received)",
        }
        return state

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        state["serpapi_results"] = {
            "status": "failed",
            "error": "SERPAPI_API_KEY not set in environment",
        }
        return state

    params = {
        "engine": "google_reverse_image",
        "image_url": image_url,
        "api_key": api_key,
        "gl": "ir",   # country
        "hl": "fa",   # language
    }

    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extract only titles
        titles: List[str] = []

        for r in data.get("image_results", []):
            title = r.get("title")
            if title:
                # skip abadis/dictionary titles
                if "آبادیس" in title or "abadis" in title.lower():
                    continue
                titles.append(title)

        for r in data.get("organic_results", []):
            title = r.get("title")
            if title:
                # skip abadis/dictionary titles
                if "آبادیس" in title or "abadis" in title.lower():
                    continue
                titles.append(title)
        limited_titles = titles[:5]
        print(limited_titles)
        cleaned_text = "\n".join(limited_titles).strip()

        state["serpapi_results"] = {
            "status": "ok",
            "titles": cleaned_text,
            "count": len(titles),
        }

    except requests.RequestException as e:
        state["serpapi_results"] = {
            "status": "failed",
            "error": str(e),
        }

    return state
