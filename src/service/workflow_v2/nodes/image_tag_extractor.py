"""
Image tag extraction node for direct tag extraction from images.

This node directly analyzes product images to extract structured
product information without intermediate caption generation.
"""

from typing import Any, Dict
from ..core.base_node import BaseNode
from ..config import IMAGE_TAG_PROMPT_TEMPLATE, VISION_MODEL


class ImageTagExtractorNode(BaseNode):
    """
    Node that extracts structured tags directly from product images.

    Input state keys:
        - image_url: URL or data URI of the image to analyze

    Output state keys:
        - image_tags: Extracted tags in JSON format
        - image_tag_raw_response: Raw model response
    """

    def __init__(
        self, name: str = "image_tag_extractor", config: Dict[str, Any] = None
    ):
        """
        Initialize the image tag extractor node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.model = self.config.get("model", VISION_MODEL)
        self.custom_prompt = self.config.get("prompt", IMAGE_TAG_PROMPT_TEMPLATE)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags directly from image.

        Args:
            state: Current workflow state

        Returns:
            Updated state with extracted tags
        """
        self.validate_inputs(state, ["image_url"])

        image_url = state["image_url"]
        self.log_execution(f"Extracting tags directly from image")

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

            result = client.call_json(model=self.model, messages=messages)
            tags = result.get("json", {})

            entity_count = len(tags.get("entities", []))
            self.log_execution(f"Extracted {entity_count} tag entities from image")

            return {
                **state,
                "image_tags": tags,
                "image_tag_raw_response": result,
                "step_count": state.get("step_count", 0) + 1,
            }

        except Exception as e:
            self.log_execution(f"Error extracting image tags: {str(e)}", "error")
            return {
                **state,
                "image_tags": {},
                "image_tag_error": str(e),
                "step_count": state.get("step_count", 0) + 1,
            }
