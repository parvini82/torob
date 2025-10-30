"""
Caption generation node for creating descriptive text from images.

This node analyzes product images and generates detailed captions
that can be used for further processing or tag extraction.
"""

from typing import Any, Dict
from ..core.base_node import BaseNode
from ..config import CAPTION_PROMPT_TEMPLATE, VISION_MODEL


class CaptionGeneratorNode(BaseNode):
    """
    Node that generates descriptive captions from product images.

    Input state keys:
        - image_url: URL or data URI of the image to analyze

    Output state keys:
        - caption: Generated descriptive caption
        - caption_raw_response: Raw model response
    """

    def __init__(self, name: str = "caption_generator", config: Dict[str, Any] = None):
        """
        Initialize the caption generator node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.model = self.config.get("model", VISION_MODEL)
        self.custom_prompt = self.config.get("prompt", CAPTION_PROMPT_TEMPLATE)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate caption from image.

        Args:
            state: Current workflow state

        Returns:
            Updated state with generated caption
        """
        self.validate_inputs(state, ["image_url"])

        image_url = state["image_url"]
        self.log_execution(f"Generating caption for image")

        try:
            # Import here to avoid circular imports
            from ...workflow.model_client import (
                OpenRouterClient,
                make_image_part,
                make_text_part,
            )

            client = OpenRouterClient()

            messages = [
                {
                    "role": "user",
                    "content": [
                        make_text_part(self.custom_prompt),
                        make_image_part(image_url),
                    ],
                }
            ]

            result = client.call_text(model=self.model, messages=messages)
            caption = result.get("text", "").strip()

            self.log_execution(f"Generated caption: {caption[:50]}...")

            return {
                **state,
                "caption": caption,
                "caption_raw_response": result,
                "step_count": state.get("step_count", 0) + 1,
            }

        except Exception as e:
            self.log_execution(f"Error generating caption: {str(e)}", "error")
            return {
                **state,
                "caption": "",
                "caption_error": str(e),
                "step_count": state.get("step_count", 0) + 1,
            }
