"""
Multi-provider model client for LLM interactions.

Supports multiple AI providers with automatic endpoint selection,
retry logic, and JSON sanitization capabilities.
"""

import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .core.logger import get_workflow_logger
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))

OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_TITLE: str = os.getenv("OPENROUTER_SITE_TITLE", "")

METIS_API_KEY: str = os.getenv("METIS_API_KEY", "")
METIS_BASE_URL: str = os.getenv("METIS_BASE_URL", "")

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
TRANSLATE_MODEL: str = os.getenv(
    "TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free"
)

class Provider(Enum):
    """Supported AI providers."""
    OPENROUTER = "openrouter"
    METIS = "metis"
    TOGETHER = "together"
    OPENAI = "openai"


class ModelClientError(Exception):
    """Base exception for model client errors."""
    pass


class ProviderError(ModelClientError):
    """Provider-specific error."""

    def __init__(self, provider: str, message: str, response_code: Optional[int] = None):
        self.provider = provider
        self.response_code = response_code
        super().__init__(f"[{provider}] {message}")


class ModelClient:
    """
    Multi-provider client for LLM API interactions.

    Automatically selects the appropriate provider based on configuration
    and handles retries, rate limiting, and response parsing.
    """

    # Provider endpoints
    ENDPOINTS = {
        Provider.OPENROUTER: "https://openrouter.ai/api/v1",
        Provider.METIS: "https://api.metis.ai/v1",
        Provider.TOGETHER: "https://api.together.xyz/v1",
        Provider.OPENAI: "https://api.openai.com/v1"
    }

    # Provider-specific headers and auth
    AUTH_HEADERS = {
        Provider.OPENROUTER: lambda key: {"Authorization": f"Bearer {key}"},
        Provider.METIS: lambda key: {"Authorization": f"Bearer {key}"},
        Provider.TOGETHER: lambda key: {"Authorization": f"Bearer {key}"},
        Provider.OPENAI: lambda key: {"Authorization": f"Bearer {key}"}
    }

    def __init__(self,
                 provider: str = "openrouter",
                 api_key: Optional[str] = None,
                 timeout: int = 60,
                 max_retries: int = 3):
        """
        Initialize the model client.

        Args:
            provider: Provider name (openrouter, metis, together, openai)
            api_key: API key for the provider
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.logger = get_workflow_logger(f"{__name__}.ModelClient")

        # Validate and set provider
        try:
            self.provider = Provider(provider.lower())
        except ValueError:
            available = [p.value for p in Provider]
            raise ValueError(f"Unsupported provider: {provider}. Available: {available}")

        # Set API key
        if not api_key:
            # Try to get from environment or config
            api_key = self._get_api_key_from_env()

        if not api_key:
            raise ValueError(f"API key required for provider {provider}")

        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        # Setup HTTP session with retries
        self.session = self._create_session()

        self.logger.info(f"ModelClient initialized - Provider: {provider}, Timeout: {timeout}s")

    def call_json(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Call model and expect JSON response.

        Args:
            model: Model name/identifier
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Parsed JSON response

        Raises:
            ProviderError: If API call fails
            ModelClientError: If JSON parsing fails
        """
        self.logger.info(f"Making JSON call to {model} via {self.provider.value}")

        # Add JSON format instruction to system message if not present
        formatted_messages = self._ensure_json_format(messages)

        # Make API call
        response_text = self._make_api_call(model, formatted_messages, **kwargs)

        # Parse and sanitize JSON
        try:
            json_data = self._parse_and_sanitize_json(response_text)
            self.logger.info(f"Successfully parsed JSON response with {len(json_data)} keys")
            return json_data

        except Exception as e:
            self.logger.error(f"JSON parsing failed: {str(e)}")
            self.logger.debug(f"Raw response: {response_text[:500]}...")

            raise ModelClientError(f"Failed to parse JSON response: {str(e)}")

    def call_text(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Call model and expect plain text response.

        Args:
            model: Model name/identifier
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Plain text response

        Raises:
            ProviderError: If API call fails
        """
        self.logger.info(f"Making text call to {model} via {self.provider.value}")

        response_text = self._make_api_call(model, messages, **kwargs)

        self.logger.info(f"Successfully received text response ({len(response_text)} chars)")
        return response_text.strip()

    def _make_api_call(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Make the actual API call with retries.

        Args:
            model: Model name
            messages: Messages list
            **kwargs: Additional API parameters

        Returns:
            Response text content

        Raises:
            ProviderError: If all retry attempts fail
        """
        endpoint = self.ENDPOINTS[self.provider]
        url = f"{endpoint}/chat/completions"

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            **self.AUTH_HEADERS[self.provider](self.api_key)
        }

        # Prepare payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
        }

        # Add provider-specific parameters
        if self.provider == Provider.OPENROUTER:
            payload["top_p"] = kwargs.get("top_p", 1.0)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"API call attempt {attempt + 1}/{self.max_retries + 1}")

                response = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                # Handle different response codes
                if response.status_code == 200:
                    response_data = response.json()

                    # Extract content from response
                    if "choices" in response_data and response_data["choices"]:
                        content = response_data["choices"][0]["message"]["content"]
                        return content
                    else:
                        raise ProviderError(
                            self.provider.value,
                            "No choices in response",
                            response.status_code
                        )

                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue

                elif response.status_code in [500, 502, 503, 504]:  # Server errors
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Server error {response.status_code}, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                else:
                    # Client error or other
                    error_text = response.text
                    raise ProviderError(
                        self.provider.value,
                        f"API error {response.status_code}: {error_text}",
                        response.status_code
                    )

            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    break

        # All retries failed
        error_msg = f"All {self.max_retries + 1} attempts failed"
        if last_exception:
            error_msg += f": {str(last_exception)}"

        raise ProviderError(self.provider.value, error_msg)

    def _ensure_json_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure messages include JSON format instruction."""
        formatted_messages = messages.copy()

        # Check if there's already a JSON instruction
        has_json_instruction = any(
            "json" in msg.get("content", "").lower()
            for msg in formatted_messages
            if msg.get("role") == "system"
        )

        if not has_json_instruction:
            # Add JSON instruction to system message or create one
            json_instruction = "\n\nPlease respond with valid JSON format only."

            # Find system message
            system_msg_idx = None
            for i, msg in enumerate(formatted_messages):
                if msg.get("role") == "system":
                    system_msg_idx = i
                    break

            if system_msg_idx is not None:
                # Append to existing system message
                formatted_messages[system_msg_idx]["content"] += json_instruction
            else:
                # Create new system message
                formatted_messages.insert(0, {
                    "role": "system",
                    "content": f"You are a helpful assistant.{json_instruction}"
                })

        return formatted_messages

    def _parse_and_sanitize_json(self, text: str) -> Dict[str, Any]:
        """
        Parse and sanitize JSON from model response.

        Handles common JSON formatting issues from LLM responses.

        Args:
            text: Raw text response

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed after sanitization
        """
        # Extract JSON from response (handle markdown code blocks)
        json_text = self._extract_json_from_text(text)

        # Apply sanitization fixes
        sanitized = self._sanitize_json_string(json_text)

        try:
            return json.loads(sanitized)
        except json.JSONDecodeError as e:
            # Try additional fixes for common issues
            fixed = self._apply_aggressive_json_fixes(sanitized)
            return json.loads(fixed)

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON content from text, handling markdown blocks."""
        # Remove markdown code blocks
        # text = re.sub(r'```(?:json)?', '', text)
        # text = re.sub(r'```\s*\n?', '', text)

        # Remove markdown code block markers like ```json or ```
        text = re.sub(r'```(?:json)?', '', text)
        text = text.strip()


        # Find JSON object bounds
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]

        return text.strip()

    def _sanitize_json_string(self, json_str: str) -> str:
        """Apply common JSON sanitization fixes."""
        # Fix newlines in strings
        json_str = re.sub(r'\n\s*"', ' "', json_str)

        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        # Fix missing commas between objects
        json_str = re.sub(r'}\s*{', '}, {', json_str)
        json_str = re.sub(r']\s*{', '], {', json_str)
        json_str = re.sub(r'}\s*"', '}, "', json_str)

        return json_str

    def _apply_aggressive_json_fixes(self, json_str: str) -> str:
        """Apply more aggressive JSON fixes as last resort."""
        # Fix unescaped quotes in values
        json_str = re.sub(r':\s*"([^"]*)"([^",}\]]*)"', r': "\1\2"', json_str)

        # Fix missing quotes around keys
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)

        # Fix single quotes
        json_str = json_str.replace("'", '"')

        return json_str

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variables."""
        import os

        # Provider-specific environment variable names
        env_vars = {
            Provider.OPENROUTER: ["OPENROUTER_API_KEY", "OPENROUTER_KEY"],
            Provider.METIS: ["METIS_API_KEY", "METIS_KEY"],
            Provider.TOGETHER: ["TOGETHER_API_KEY", "TOGETHER_KEY"],
            Provider.OPENAI: ["OPENAI_API_KEY", "OPENAI_KEY"]
        }

        for var_name in env_vars.get(self.provider, []):
            api_key = os.getenv(var_name)
            if api_key:
                self.logger.debug(f"Found API key in environment variable: {var_name}")
                return api_key

        return None

    def test_connection(self, test_model: Optional[str] = None) -> bool:
        """
        Test the connection to the provider.

        Args:
            test_model: Optional model to test with

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use a simple test model if not specified
            model = test_model or self._get_default_test_model()

            test_messages = [
                {"role": "user", "content": "Say 'OK' if you can hear me."}
            ]

            response = self.call_text(model, test_messages, max_tokens=10)

            self.logger.info(f"Connection test successful: {response[:50]}")
            return True

        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def _get_default_test_model(self) -> str:
        """Get default model for connection testing."""
        defaults = {
            Provider.OPENROUTER: "qwen/qwen2.5-vl-32b-instruct:free",
            Provider.METIS: "gpt-3.5-turbo",
            Provider.TOGETHER: "meta-llama/Llama-2-7b-chat-hf",
            Provider.OPENAI: "gpt-3.5-turbo"
        }
        return defaults.get(self.provider, "gpt-3.5-turbo")

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current provider configuration.

        Returns:
            Provider information dictionary
        """
        return {
            "provider": self.provider.value,
            "endpoint": self.ENDPOINTS[self.provider],
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "has_api_key": bool(self.api_key)
        }


def create_model_client(provider: str = None, api_key: str = None) -> ModelClient:
    """
    Factory function to create a ModelClient instance.

    Args:
        provider: Provider name (will check env if None)
        api_key: API key (will check env if None)

    Returns:
        Configured ModelClient instance
    """
    import os

    # Get provider from environment if not specified
    if not provider:
        # provider = os.getenv("API_PROVIDER", "openrouter")
        provider = os.getenv("API_PROVIDER", "openrouter")
        api_key = os.getenv("OPENROUTER_API_KEY","")

    return ModelClient(provider=provider, api_key=api_key)
