"""
Unified Model Client - Supports both OpenRouter and Metis APIs

Features:
- OpenRouter API integration
- Metis API integration (wrapper format)
- Runtime provider switching
- Rate limiting and exponential backoff
- JSON extraction with fallback strategies
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Literal
from enum import Enum

import requests

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_TITLE,
    OPENROUTER_SITE_URL,
    METIS_API_KEY,
    METIS_BASE_URL,
    REQUEST_TIMEOUT,
)


class APIProvider(Enum):
    """Supported API providers."""
    OPENROUTER = "openrouter"
    METIS = "metis"


class ModelClientError(RuntimeError):
    """Base exception for model client errors."""
    pass


class OpenRouterError(ModelClientError):
    """OpenRouter-specific errors."""
    pass


class MetisError(ModelClientError):
    """Metis-specific errors."""
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_image_part(image_url_or_data_uri: str) -> Dict[str, str]:
    """Create image part for multi-modal messages."""
    return {"type": "image_url", "image_url": image_url_or_data_uri}


def make_text_part(text: str) -> Dict[str, str]:
    """Create text part for multi-modal messages."""
    return {"type": "text", "text": text}


def extract_json_from_text(text: str) -> Tuple[Optional[dict], Optional[str]]:
    """Extract JSON object from text, trying multiple strategies."""
    # Strategy 1: Direct JSON parsing
    try:
        return json.loads(text), None
    except Exception:
        pass

    # Strategy 2: Find and extract JSON object
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        sliced = text[start:end]
        return json.loads(sliced), None
    except Exception:
        return None, text


# ============================================================================
# OPENROUTER CLIENT
# ============================================================================

class OpenRouterClient:
    """Client for OpenRouter API."""

    def __init__(
        self,
        base_url: str = OPENROUTER_BASE_URL,
        timeout: int = REQUEST_TIMEOUT
    ):
        """Initialize OpenRouter client."""
        self.base_url = base_url
        self.timeout = timeout
        self.provider = APIProvider.OPENROUTER

    def _auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for OpenRouter."""
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

    def call_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call OpenRouter chat API."""
        headers = self._auth_headers()
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
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                if resp.status_code != 200:
                    raise OpenRouterError(
                        f"OpenRouter HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "raw": data,
                    "content": content,
                }
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
        """Call OpenRouter chat API and extract JSON response."""
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


# ============================================================================
# METIS CLIENT (Fixed for Wrapper API)
# ============================================================================

class MetisClient:
    """Client for Metis API (Wrapper format)."""

    def __init__(
        self,
        base_url: str = METIS_BASE_URL,
        timeout: int = REQUEST_TIMEOUT
    ):
        """Initialize Metis client."""
        self.base_url = base_url
        self.timeout = timeout
        self.provider = APIProvider.METIS

    def _auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Metis."""
        if not METIS_API_KEY:
            raise MetisError(
                "METIS_API_KEY is empty. Set it in your environment variables."
            )

        headers = {
            "Authorization": f"Bearer {METIS_API_KEY}",
            "Content-Type": "application/json",
        }
        return headers

    def call_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call Metis chat API using wrapper format.

        Metis API expects the model name as a URL parameter in the wrapper format.
        See: https://docs.metisai.ir/api/wrapper
        """
        headers = self._auth_headers()

        # Metis wrapper format: append model name to base URL
        # Format: {METIS_BASE_URL}/{model_name}
        url = self.base_url

        payload = {
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
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                if resp.status_code != 200:
                    raise MetisError(
                        f"Metis HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "raw": data,
                    "content": content,
                }
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    time.sleep(0.8 * (attempt + 1))
                else:
                    raise MetisError(f"Metis call failed: {e}") from e
        raise MetisError(f"Metis call failed: {last_err}")

    def call_json(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        enforce_json_mode: bool = True,
    ) -> Dict[str, Any]:
        """Call Metis chat API and extract JSON response."""
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


# ============================================================================
# UNIFIED MODEL CLIENT FACTORY
# ============================================================================

class UnifiedModelClient:
    """Unified client that supports both OpenRouter and Metis APIs."""

    def __init__(self, provider: Literal["openrouter", "metis"] = "openrouter"):
        """Initialize unified client with specified provider.

        Args:
            provider: "openrouter" or "metis"
        """
        if provider not in ["openrouter", "metis"]:
            raise ValueError(f"Unknown provider: {provider}. Use 'openrouter' or 'metis'")

        self.provider_name = provider

        if provider == "openrouter":
            self.client = OpenRouterClient()
        elif provider == "metis":
            self.client = MetisClient()

    def call_chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call chat API using selected provider."""
        return self.client.call_chat(
            model,
            messages,
            max_retries=max_retries,
            temperature=temperature,
            response_format=response_format,
        )

    def call_json(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        max_retries: int = 2,
        temperature: Optional[float] = None,
        enforce_json_mode: bool = True,
    ) -> Dict[str, Any]:
        """Call chat API and extract JSON using selected provider."""
        return self.client.call_json(
            model,
            messages,
            max_retries=max_retries,
            temperature=temperature,
            enforce_json_mode=enforce_json_mode,
        )

    def switch_provider(self, provider: Literal["openrouter", "metis"]) -> None:
        """Switch to a different API provider."""
        if provider not in ["openrouter", "metis"]:
            raise ValueError(f"Unknown provider: {provider}. Use 'openrouter' or 'metis'")

        self.provider_name = provider

        if provider == "openrouter":
            self.client = OpenRouterClient()
        elif provider == "metis":
            self.client = MetisClient()

    def get_current_provider(self) -> str:
        """Get name of current provider."""
        return self.provider_name


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_model_client(provider: Literal["openrouter", "metis"] = "openrouter") -> UnifiedModelClient:
    """Get a unified model client with specified provider."""
    return UnifiedModelClient(provider)