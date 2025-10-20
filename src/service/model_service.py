"""Model service for AI-powered image analysis and tag generation.

This module provides the core functionality for interacting with AI models
to analyze product images and generate relevant tags and attributes.
It handles image encoding, API communication, and response parsing.
"""

import base64
import json
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.settings import API_KEY, MODEL, DEBUG_MODE


class ModelServiceError(Exception):
    """Custom exception for model service related errors."""
    pass


class ImageProcessor:
    """Handles image processing and AI model interactions.
    
    This class encapsulates all functionality related to preparing images
    for AI analysis and communicating with external AI APIs.
    """
    
    def __init__(self, api_key: str = API_KEY, model: str = MODEL):
        """Initialize the image processor.
        
        Args:
            api_key: API key for the AI service
            model: Model identifier to use for processing
            
        Raises:
            ModelServiceError: If API key or model is invalid
        """
        if not api_key:
            raise ModelServiceError("API key is required for model service")
        if not model:
            raise ModelServiceError("Model identifier is required")
            
        self.api_key = api_key
        self.model = model
        self.api_base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Configure requests session with retry strategy
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry strategy.
        
        Returns:
            requests.Session: Configured session with retry logic
        """
        session = requests.Session()
        
        # Define retry strategy for robust API communication
        retry_strategy = Retry(
            total=3,                          # Maximum number of retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry
            backoff_factor=1,                 # Wait time between retries
            raise_on_status=False            # Don't raise on HTTP errors
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def prepare_image_input(self, image_bytes: bytes) -> Dict[str, str]:
        """Prepare image data for API consumption.
        
        Converts raw image bytes to base64 encoded format suitable
        for transmission to the AI API.
        
        Args:
            image_bytes: Raw image data as bytes
            
        Returns:
            Dict[str, str]: Formatted image payload for API
            
        Raises:
            ModelServiceError: If image encoding fails
        """
        try:
            # Encode image to base64
            b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
            
            # Create API-compatible image payload
            image_payload = {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{b64_encoded}"
            }
            
            return image_payload
            
        except Exception as e:
            raise ModelServiceError(f"Failed to encode image: {str(e)}") from e
    
    def _build_prompt(self) -> str:
        """Build the system prompt for entity recognition.
        
        Returns:
            str: Complete system prompt for the AI model
        """
        return """
        You are a specialized Named Entity Recognition (NER) model trained to 
        recognize attributes of apparel products from images.
        
        Given the input image of a clothing item, your task is to identify and 
        extract all relevant entities and output them in a structured JSON format.
        
        Your analysis should include:
        - Product type (e.g., shirt, pants, dress, shoes)
        - Material/fabric (e.g., cotton, polyester, leather)
        - Color(s) (primary and secondary colors)
        - Pattern (e.g., solid, striped, floral)
        - Style/design features (e.g., collar type, sleeve length)
        - Size indicators (if visible)
        - Brand (if visible)
        
        The response must be in JSON format with two language outputs:
        1. English version with entity names and values in English
        2. Persian version with entity names and values in Persian
        
        Output format:
        {
            "english": {
                "entities": [
                    {"name": "color", "values": ["blue"]},
                    {"name": "material", "values": ["cotton"]}
                ]
            },
            "persian": {
                "entities": [
                    {"name": "رنگ", "values": ["آبی"]},
                    {"name": "جنس", "values": ["پنبه"]}
                ]
            }
        }
        
        Only respond with valid JSON. Do not include any explanatory text.
        """
    
    def _prepare_api_payload(self, image_payload: Dict[str, str]) -> Dict[str, Any]:
        """Prepare the complete API request payload.
        
        Args:
            image_payload: Formatted image data
            
        Returns:
            Dict[str, Any]: Complete API request payload
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self._build_prompt()
                        },
                        image_payload
                    ],
                }
            ],
            "max_tokens": 1000,        # Limit response length
            "temperature": 0.1,       # Low temperature for consistent results
        }
    
    def _parse_api_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate API response.
        
        Args:
            response_data: Raw API response data
            
        Returns:
            Dict[str, Any]: Parsed and validated response
            
        Raises:
            ModelServiceError: If response parsing fails
        """
        try:
            # Extract content from API response
            content = response_data["choices"][0]["message"]["content"]
            
            # Find JSON boundaries in the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ModelServiceError("No valid JSON found in API response")
            
            # Extract and parse JSON
            json_content = content[json_start:json_end]
            parsed_result = json.loads(json_content)
            
            # Validate response structure
            if not isinstance(parsed_result, dict):
                raise ModelServiceError("API response is not a valid JSON object")
            
            return parsed_result
            
        except json.JSONDecodeError as e:
            # Fallback: return structured error response
            return {
                "error": "json_parse_error",
                "message": f"Failed to parse JSON: {str(e)}",
                "raw_content": response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        except (KeyError, IndexError) as e:
            raise ModelServiceError(f"Invalid API response structure: {str(e)}") from e
    
    def predict_tags(self, image_bytes: bytes) -> Dict[str, Any]:
        """Generate tags and attributes for a product image.
        
        Main method that orchestrates the entire image analysis pipeline:
        1. Prepare image data
        2. Send request to AI API
        3. Parse and validate response
        
        Args:
            image_bytes: Raw image data as bytes
            
        Returns:
            Dict[str, Any]: Generated tags and attributes in multiple languages
            
        Raises:
            ModelServiceError: If any step in the pipeline fails
        """
        try:
            # Step 1: Prepare image for API
            image_payload = self.prepare_image_input(image_bytes)
            
            # Step 2: Prepare complete API request
            api_payload = self._prepare_api_payload(image_payload)
            
            # Step 3: Set up request headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Torob-ImageAnalyzer/1.0"
            }
            
            # Step 4: Make API request
            response = self.session.post(
                self.api_base_url,
                headers=headers,
                json=api_payload,
                timeout=30  # 30 second timeout
            )
            
            # Step 5: Handle HTTP errors
            if response.status_code != 200:
                error_detail = f"API request failed with status {response.status_code}"
                if response.text:
                    error_detail += f": {response.text[:200]}"  # Limit error message length
                raise ModelServiceError(error_detail)
            
            # Step 6: Parse response
            response_data = response.json()
            try:
                parsed_result = self._parse_api_response(response_data)
            except ModelServiceError as e:
                # If the model does not have JSON output, return error dict instead of exception
                return {
                    "error": "json_parse_error",
                    "message": str(e),
                    "_metadata": {"parse_failed": True}
                }            
            parsed_result = self._parse_api_response(response_data)
            
            # Step 7: Add metadata to response
            parsed_result["_metadata"] = {
                "model_used": self.model,
                "api_status": "success",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
            return parsed_result
            
        except requests.exceptions.RequestException as e:
            raise ModelServiceError(f"Network error during API request: {str(e)}") from e
        except Exception as e:
            if isinstance(e, ModelServiceError):
                raise
            raise ModelServiceError(f"Unexpected error during image processing: {str(e)}") from e

# Global instance for backward compatibility
_default_processor = None


def get_processor() -> ImageProcessor:
    """Get or create the default image processor instance.
    
    Returns:
        ImageProcessor: Default processor instance
    """
    global _default_processor
    if _default_processor is None:
        _default_processor = ImageProcessor()
    return _default_processor


# Backward compatibility functions
def prepare_image_input(image_bytes: bytes) -> Dict[str, str]:
    """Backward compatibility function for image preparation.
    
    Args:
        image_bytes: Raw image data
        
    Returns:
        Dict[str, str]: Prepared image payload
    """
    processor = get_processor()
    return processor.prepare_image_input(image_bytes)


def predict_tags(image_bytes: bytes) -> Dict[str, Any]:
    """Backward compatibility function for tag prediction.
    
    Args:
        image_bytes: Raw image data
        
    Returns:
        Dict[str, Any]: Generated tags and attributes
    """
    processor = get_processor()
    return processor.predict_tags(image_bytes)
