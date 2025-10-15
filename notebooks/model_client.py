from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    REQUEST_TIMEOUT,
    OPENROUTER_SITE_URL,
    OPENROUTER_SITE_TITLE,
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
    # اختیاری برای رتبه‌بندی در OpenRouter
    if OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = OPENROUTER_SITE_URL
    if OPENROUTER_SITE_TITLE:
        headers["X-Title"] = OPENROUTER_SITE_TITLE
    return headers


def make_image_part(image_url_or_data_uri: str) -> Dict[str, str]:
    """
    OpenRouter multi-modal piece for images.
    """
    return {"type": "image_url", "image_url": image_url_or_data_uri}


def make_text_part(text: str) -> Dict[str, str]:
    return {"type": "text", "text": text}


def extract_json_from_text(text: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    extracts JSON from model's response
    """
    try:
        #if the response is only JSON
        return json.loads(text), None
    except Exception:
        pass

    # trying to find the biggest block
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        sliced = text[start:end]
        return json.loads(sliced), None
    except Exception:
        return None, text


class OpenRouterClient:
    """
    Thin wrapper روی endpoint chat/completions با:
    - retry ساده
    - timeout قابل پیکربندی
    - parsing محتوا
    """

    def __init__(self, base_url: str = OPENROUTER_BASE_URL, timeout: int = REQUEST_TIMEOUT):
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
        """
        فراخوانی ساده Chat Completions.
        - messages باید با فرمت OpenRouter باشد.
        - اگر response_format بدهید (مثلاً {"type": "json_object"}) سعی می‌کند خروجی JSON بگیرد.
        """
        headers = _auth_headers()
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if response_format is not None:
            # برخی مدل‌ها این پارامتر را پشتیبانی می‌کنند (مانند JSON mode)
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
                data = resp.json()
                # ساختار استاندارد OpenRouter
                content = data["choices"][0]["message"]["content"]
                return {
                    "raw": data,
                    "content": content,
                }
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    # backoff ساده
                    time.sleep(0.8 * (attempt + 1))
                else:
                    raise OpenRouterError(f"OpenRouter call failed: {e}") from e
        # نباید به اینجا برسیم
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
        """
        فراخوانی که تلاش می‌کند خروجی JSON بدهد.
        - ابتدا با response_format JSON تلاش می‌کنیم (اگر مدل پشتیبانی کند).
        - اگر نشد، تلاش به صورت آزاد و سپس parse با extract_json_from_text.
        """
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
