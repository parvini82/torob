"""
Caption generation node for image analysis.

Generates descriptive captions for images using vision-language models.
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class CaptionGeneratorNode(BaseNode):
    """
    Node that generates descriptive captions for images.

    Takes an image URL/data and produces a detailed textual description
    that can be used by downstream nodes for further analysis.
    """

    def __init__(self, model: str = "qwen/qwen2.5-vl-32b-instruct:free"):
        """
        Initialize the caption generator node.

        Args:
            model: Model to use for caption generation
        """
        super().__init__("CaptionGenerator")
        self.model = model
        self.client = None  # Will be initialized on first use

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a caption for the provided image.

        Args:
            state: Workflow state containing image_url

        Returns:
            Updated state with caption information
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
        self.logger.info(f"Generating caption for image using model: {model_to_use}")

        try:
            # Prepare messages for vision model
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please provide a detailed caption for this image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]

            # Generate caption
            caption_text = self.client.call_text(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 500),
                temperature=config.get("temperature", 0.7)
            )

            # Create caption result
            caption_result = {
                "text": caption_text,
                "model_used": model_to_use,
                "word_count": len(caption_text.split()),
                "generated_by": self.node_name
            }

            # Update state
            updated_state = state.copy()
            updated_state["caption"] = caption_result

            self.logger.info(f"Generated caption with {caption_result['word_count']} words")
            self.logger.debug(f"Caption preview: {caption_text[:100]}...")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during caption generation: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during caption generation: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for caption generation."""
        return """You are an expert image analyst. Generate detailed, accurate captions for images.

Your caption should:
1. Describe the main subject(s) and their key characteristics
2. Include relevant context, setting, and environment
3. Mention important visual elements, colors, and composition
4. Be factual and objective, avoiding speculation
5. Be comprehensive but concise (aim for 2-4 sentences)

Focus on details that would be useful for product categorization, search, and understanding."""
