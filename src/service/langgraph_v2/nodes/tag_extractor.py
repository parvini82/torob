"""
Tag extraction node for extracting structured tags from text captions.

This node processes descriptive text and extracts structured
product information in JSON format.
"""

from typing import Any, Dict
from ..core.base_node import BaseNode
from ..config import TAG_FROM_CAPTION_PROMPT_TEMPLATE, GENERAL_MODEL


class TagExtractorNode(BaseNode):
    """
    Node that extracts structured tags from text captions.

    Input state keys:
        - caption: Text caption to analyze

    Output state keys:
        - tags_from_caption: Extracted tags in JSON format
        - tag_extraction_raw: Raw model response
    """

    def __init__(self, name: str = "tag_extractor", config: Dict[str, Any] = None):
        """
        Initialize the tag extractor node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.model = self.config.get("model", GENERAL_MODEL)
        self.prompt_template = self.config.get("prompt", TAG_FROM_CAPTION_PROMPT_TEMPLATE)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags from caption text.

        Args:
            state: Current workflow state

        Returns:
            Updated state with extracted tags
        """
        self.validate_inputs(state, ["caption"])

        caption = state["caption"]
        self.log_execution(f"Extracting tags from caption: {caption[:30]}...")

        try:
            # Import here to avoid circular imports
            from ...langgraph.model_client import OpenRouterClient, make_text_part

            client = OpenRouterClient()
            prompt = self.prompt_template.format(caption=caption)

            messages = [
                {
                    "role": "user",
                    "content": [make_text_part(prompt)]
                }
            ]

            result = client.call_json(model=self.model, messages=messages)
            tags = result.get("json", {})

            self.log_execution(f"Extracted {len(tags.get('entities', []))} tag entities")

            return {
                **state,
                "tags_from_caption": tags,
                "tag_extraction_raw": result,
                "step_count": state.get("step_count", 0) + 1
            }

        except Exception as e:
            self.log_execution(f"Error extracting tags: {str(e)}", "error")
            return {
                **state,
                "tags_from_caption": {},
                "tag_extraction_error": str(e),
                "step_count": state.get("step_count", 0) + 1
            }