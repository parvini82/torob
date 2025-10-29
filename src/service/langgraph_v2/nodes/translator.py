"""
Translation node for converting English tags to Persian.

This node handles translation of structured tag data from English
to Persian while maintaining the JSON structure.
"""

from typing import Any, Dict
import json
from ..core.base_node import BaseNode
from ..config import TRANSLATION_PROMPT_TEMPLATE, TRANSLATE_MODEL


class TranslatorNode(BaseNode):
    """
    Node that translates structured tags from English to Persian.

    Input state keys:
        - tags_to_translate: Tags in JSON format to translate
        OR
        - final_merged_tags: Merged tags to translate (fallback)

    Output state keys:
        - translated_tags: Persian translated tags
        - translation_raw_response: Raw translation response
    """

    def __init__(self, name: str = "translator", config: Dict[str, Any] = None):
        """
        Initialize the translator node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.model = self.config.get("model", TRANSLATE_MODEL)
        self.prompt_template = self.config.get("prompt", TRANSLATION_PROMPT_TEMPLATE)
        self.input_key = self.config.get("input_key", "tags_to_translate")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate tags from English to Persian.

        Args:
            state: Current workflow state

        Returns:
            Updated state with translated tags
        """
        # Try to find tags to translate with flexible key matching
        tags_to_translate = None
        source_key = None

        possible_keys = [
            self.input_key,
            "tags_to_translate",
            "final_merged_tags",
            "merged_tags",
            "image_tags",
            "tags_from_caption"
        ]

        for key in possible_keys:
            if key in state and state[key]:
                tags_to_translate = state[key]
                source_key = key
                break

        if not tags_to_translate:
            raise ValueError(f"{self.name}: No tags found to translate in keys: {list(state.keys())}")

        self.log_execution(f"Translating tags from key: {source_key}")

        try:
            # Import here to avoid circular imports
            from ...langgraph.model_client import OpenRouterClient, make_text_part

            client = OpenRouterClient()
            tags_json = json.dumps(tags_to_translate, ensure_ascii=False, indent=2)
            prompt = self.prompt_template.format(tags_json=tags_json)

            messages = [
                {
                    "role": "user",
                    "content": [make_text_part(prompt)]
                }
            ]

            result = client.call_json(model=self.model, messages=messages)
            translated_tags = result.get("json", {})

            entity_count = len(translated_tags.get("entities", []))
            self.log_execution(f"Translated {entity_count} tag entities to Persian")

            return {
                **state,
                "translated_tags": translated_tags,
                "translation_raw_response": result,
                "final_output": translated_tags,  # For compatibility
                "step_count": state.get("step_count", 0) + 1
            }

        except Exception as e:
            self.log_execution(f"Error translating tags: {str(e)}", "error")
            return {
                **state,
                "translated_tags": {},
                "translation_error": str(e),
                "step_count": state.get("step_count", 0) + 1
            }