"""
Caption generation node for image analysis.

Generates professional fashion product captions using specialized prompts
and configurable vision models with environment variable support.
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import CaptionPrompts
from ..config import get_model


class CaptionGeneratorNode(BaseNode):
    """
    Node that generates professional fashion product captions from images.

    Uses specialized fashion industry prompts to create detailed, commercial-grade
    captions that serve as perfect input for downstream tag extraction processes.
    Supports configurable vision models via environment variables.
    """

    def __init__(self, model: str = None):
        """
        Initialize the caption generator node.

        Args:
            model: Vision model to use. If None, uses VISION_MODEL from env
        """
        super().__init__("CaptionGenerator")
        self.model = model or get_model("vision")
        self.client = None  # Will be initialized on first use

        self.logger.info(f"Initialized with model: {self.model}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional fashion caption for the provided image.

        Uses specialized fashion industry prompts to analyze product images
        and generate comprehensive captions with commercial-grade detail.

        Args:
            state: Workflow state containing image_url

        Returns:
            Updated state with caption information

        Raises:
            ValueError: If image_url is missing from state
            ModelClientError: If vision model call fails
        """
        # Validate required inputs
        self.validate_required_keys(state, ["image_url"])

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        # Get image URL
        image_url = state["image_url"]
        self.logger.info(f"Generating professional fashion caption using model: {model_to_use}")

        try:
            # Prepare messages with specialized fashion prompt
            messages = [
                {
                    "role": "system",
                    "content": CaptionPrompts.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please provide a comprehensive professional fashion caption for this product image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]

            # Generate caption using fashion-specific prompt
            caption_text = self.client.call_text(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 800),  # Increased for detailed fashion descriptions
                temperature=config.get("temperature", 0.3)  # Lower for more consistent professional output
            )

            # Create structured caption result
            caption_result = {
                "text": caption_text.strip(),
                "model_used": model_to_use,
                "word_count": len(caption_text.split()),
                "generated_by": self.node_name,
                "prompt_type": "fashion_professional",
                "analysis_depth": "comprehensive"
            }

            # Update state with caption
            updated_state = state.copy()
            updated_state["caption"] = caption_result

            # Log generation statistics
            self.logger.info(f"Generated professional caption: {caption_result['word_count']} words")
            self.logger.debug(f"Caption preview: {caption_text[:150]}...")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Vision model error during caption generation: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during caption generation: {str(e)}")
            raise
