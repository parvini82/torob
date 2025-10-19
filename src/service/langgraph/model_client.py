"""OpenRouter API client for AI model interactions.

This module provides a robust client for communicating with OpenRouter's AI models,
handling authentication, request formatting, response parsing, and error recovery.
It supports both standard chat completions and JSON-structured responses.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    REQUEST_TIMEOUT,
    OPENROUTER_SITE_URL,
    OPENROUTER_SITE_TITLE,
    MAX_RETRIES,
    RETRY_DELAY,
)


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API related errors."""
    pass


class OpenRouterClient:
    """Client for interacting with OpenRouter AI models.
    
    This class provides methods for making chat completion requests to various
    AI models through the OpenRouter API, with support for retries, JSON parsing,
    and comprehensive error handling.
    """
    
    def __init__(self, base_url: str = OPENROUTER_BASE_URL, timeout: int = REQUEST_TIMEOUT):
        """Initialize the OpenRouter client.
        
        Args:
            base_url: OpenRouter API endpoint URL
            timeout: Request timeout in seconds
            
        Raises:
            OpenRouterError: If API key is not configured
        """
        if not OPENROUTER_API_KEY:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is required but not set in environment variables"
            )
        
        self.base_url = base_url
        self.timeout = timeout
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry strategy.
        
        Returns:
            requests.Session: Session with retry configuration
        """
        session = requests.Session()
        
        # Configure retry strategy for robustness
        retry_strategy = Retry(
            total=MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry
            backoff_factor=RETRY_DELAY,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication and metadata headers for API requests.
        
        Returns:
            Dict[str, str]: Complete headers for OpenRouter API
            
        Raises:
            OpenRouterError: If API key is not available
        """
        if not OPENROUTER_API_KEY:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is empty. Set it in your environment variables."
            )
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Torob-LangGraph/1.0"
        }
        
        # Add optional site metadata for OpenRouter analytics
        if OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = OPENROUTER_SITE_URL
        if OPENROUTER_SITE_TITLE:
            headers["X-Title"] = OPENROUTER_SITE_TITLE
        
        return headers
    
    def _build_payload(self,
                      model: str,
                      messages: List[Dict[str, Any]],
                      temperature: Optional[float] = None,
                      response_format: Optional[Dict[str, Any]] = None,
                      **kwargs) -> Dict[str, Any]:
        """Build the API request payload.
        
        Args:
            model: Model identifier to use
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 1.0)
            response_format: Response format specification
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Complete API request payload
        """
        payload = {
            "model": model,
            "messages": messages,
        }
        
        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature
        if response_format is not None:
            payload["response_format"] = response_format
        
        # Add any additional parameters
        payload.update(kwargs)
        
        return payload
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse and validate API response.
        
        Args:
            response: HTTP response from OpenRouter API
            
        Returns:
            Dict[str, Any]: Parsed response data
            
        Raises:
            OpenRouterError: If response is invalid or contains errors
        """
        # Check HTTP status
        if response.status_code != 200:
            error_text = response.text[:300] if response.text else "No error details"
            raise OpenRouterError(
                f"OpenRouter HTTP {response.status_code}: {error_text}"
            )
        
        try:
            # Parse JSON response
            data = response.json()
            
            # Validate response structure
            if "choices" not in data or not data["choices"]:
                raise OpenRouterError("Invalid response: missing choices")
            
            choice = data["choices"][0]
            if "message" not in choice or "content" not in choice["message"]:
                raise OpenRouterError("Invalid response: missing message content")
            
            content = choice["message"]["content"]
            
            return {
                "raw": data,
                "content": content,
                "usage": data.get("usage", {}),
                "model_used": data.get("model", "unknown")
            }
            
        except json.JSONDecodeError as e:
            raise OpenRouterError(f"Failed to parse JSON response: {e}") from e
        except KeyError as e:
            raise OpenRouterError(f"Unexpected response structure: missing {e}") from e
    
    def call_chat(self,
                  model: str,
                  messages: List[Dict[str, Any]],
                  *,
                  max_retries: int = MAX_RETRIES,
                  temperature: Optional[float] = None,
                  response_format: Optional[Dict[str, Any]] = None,
                  **kwargs) -> Dict[str, Any]:
        """Make a chat completion request to OpenRouter.
        
        Args:
            model: Model identifier (e.g., 'qwen/qwen2.5-vl-72b-instruct:free')
            messages: List of chat messages in OpenAI format
            max_retries: Maximum number of retry attempts
            temperature: Sampling temperature for response generation
            response_format: Response format specification
            **kwargs: Additional API parameters
            
        Returns:
            Dict[str, Any]: Response with content, usage, and metadata
            
        Raises:
            OpenRouterError: If request fails after all retries
        """
        headers = self._build_auth_headers()
        payload = self._build_payload(
            model, messages, temperature, response_format, **kwargs
        )
        
        last_error: Optional[Exception] = None
        
        # Retry loop with exponential backoff
        for attempt in range(max_retries + 1):
            try:
                response = self._session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                return self._parse_response(response)
                
            except Exception as e:
                last_error = e
                
                # Don't retry on the last attempt
                if attempt >= max_retries:
                    break
                
                # Calculate backoff delay
                delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)
        
        # All retries exhausted
        raise OpenRouterError(
            f"OpenRouter call failed after {max_retries + 1} attempts: {last_error}"
        ) from last_error
    
    def call_json(self,
                  model: str,
                  messages: List[Dict[str, Any]],
                  *,
                  max_retries: int = MAX_RETRIES,
                  temperature: Optional[float] = None,
                  enforce_json_mode: bool = True,
                  **kwargs) -> Dict[str, Any]:
        """Make a chat completion request expecting JSON response.
        
        Args:
            model: Model identifier
            messages: List of chat messages
            max_retries: Maximum retry attempts
            temperature: Sampling temperature
            enforce_json_mode: Whether to use JSON response format
            **kwargs: Additional API parameters
            
        Returns:
            Dict[str, Any]: Response with parsed JSON, fallback text, and metadata
        """
        # Configure JSON response format if requested
        response_format = {"type": "json_object"} if enforce_json_mode else None
        
        # Make the chat completion request
        response = self.call_chat(
            model,
            messages,
            max_retries=max_retries,
            temperature=temperature,
            response_format=response_format,
            **kwargs
        )
        
        # Extract and parse JSON from content
        content = response.get("content", "")
        parsed_json, fallback_text = extract_json_from_text(content)
        
        return {
            "json": parsed_json,
            "text": content if parsed_json is None else None,
            "raw": response.get("raw"),
            "fallback_raw_text": fallback_text,
            "usage": response.get("usage", {}),
            "model_used": response.get("model_used", "unknown"),
            "parsing_success": parsed_json is not None
        }


# Utility functions for message construction
def make_image_part(image_url_or_data_uri: str) -> Dict[str, str]:
    """Create an image message part for multimodal chat.
    
    Args:
        image_url_or_data_uri: URL or data URI of the image
        
    Returns:
        Dict[str, str]: Formatted image part for chat messages
    """
    return {
        "type": "image_url",
        "image_url": image_url_or_data_uri
    }


def make_text_part(text: str) -> Dict[str, str]:
    """Create a text message part for chat.
    
    Args:
        text: Text content
        
    Returns:
        Dict[str, str]: Formatted text part for chat messages
    """
    return {
        "type": "text",
        "text": text
    }


def extract_json_from_text(text: str) -> Tuple[Optional[dict], Optional[str]]:
    """Extract JSON object from text content with fallback parsing.
    
    This function attempts multiple strategies to extract valid JSON:
    1. Parse the entire text as JSON
    2. Find JSON boundaries and parse the substring
    
    Args:
        text: Text content that may contain JSON
        
    Returns:
        Tuple[Optional[dict], Optional[str]]: (parsed_json, fallback_text)
        - If JSON parsing succeeds: (json_dict, None)
        - If JSON parsing fails: (None, original_text)
    """
    if not text or not isinstance(text, str):
        return None, text
    
    # Strategy 1: Try parsing entire text as JSON
    try:
        return json.loads(text), None
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Strategy 2: Find JSON boundaries and parse substring
    try:
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_substring = text[start_idx:end_idx]
            parsed = json.loads(json_substring)
            return parsed, None
    except (json.JSONDecodeError, ValueError):
        pass
    
    # All parsing strategies failed
    return None, text


# Legacy function for backward compatibility
def _auth_headers() -> Dict[str, str]:
    """Legacy function for building auth headers (deprecated).
    
    Returns:
        Dict[str, str]: Authentication headers
        
    Note:
        This function is deprecated. Use OpenRouterClient._build_auth_headers() instead.
    """
    client = OpenRouterClient()
    return client._build_auth_headers()
