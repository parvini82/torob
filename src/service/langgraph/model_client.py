from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_TITLE,
    OPENROUTER_SITE_URL,
    REQUEST_TIMEOUT,
)


class OpenRouterError(RuntimeError):
    pass


def _auth_headers() -> Dict[str, str]:
    if not OPENROUTER_API_KEY:
        raise OpenRouterError(
            "OPENROUTER_API_KEY is empty. Set it in your environment variables."
        )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_SITE_TITLE:
        headers["X-Title"] = OPENROUTER_SITE_TITLE
    return headers


def make_image_part(image_url_or_data_uri: str) -> Dict[str, str]:
    return {"type": "image_url", "image_url": image_url_or_data_uri}


def make_text_part(text: str) -> Dict[str, str]:
    return {"type": "text", "text": text}


def extract_json_from_text(text: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        return json.loads(text), None
    except Exception:
        pass
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        sliced = text[start:end]
        return json.loads(sliced), None
    except Exception:
        return None, text


class OpenRouterClient:
    def __init__(
        self, base_url: str = OPENROUTER_BASE_URL, timeout: int = REQUEST_TIMEOUT
    ):
        self.base_url = base_url
        self.timeout = timeout

    def call_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = _auth_headers()
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if response_format is not None:
            payload["response_format"] = response_format

        last_err: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    self.base_url, headers=headers, json=payload, timeout=self.timeout
                )
                if resp.status_code != 200:
                    raise OpenRouterError(
                        f"OpenRouter HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                try:
                    data = resp.json()
                except Exception:
                    raise OpenRouterError(
                        f"OpenRouter returned non-JSON response: {resp.text[:300]}"
                    )

                choices = data.get("choices")
                if not choices or not isinstance(choices, list):
                    api_error = data.get("error") or data
                    raise OpenRouterError(
                        f"OpenRouter response missing 'choices': {str(api_error)[:300]}"
                    )

                message = choices[0].get("message", {}) if choices else {}
                content = message.get("content", "")
                return {"raw": data, "content": content}
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    time.sleep(0.8 * (attempt + 1))
                else:
                    raise OpenRouterError(f"OpenRouter call failed: {e}") from e
        raise OpenRouterError(f"OpenRouter call failed: {last_err}")

    def call_json(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        enforce_json_mode: bool = True,
    ) -> Dict[str, Any]:
        response_format = {"type": "json_object"} if enforce_json_mode else None
        out = self.call_chat(
            model,
            messages,
            max_retries=max_retries,
            temperature=temperature,
            response_format=response_format,
        )
        content = out.get("content", "")
        obj, raw = extract_json_from_text(content)
        return {
            "json": obj,
            "text": None if obj is not None else content,
            "raw": out.get("raw"),
            "fallback_raw_text": raw,
        }
