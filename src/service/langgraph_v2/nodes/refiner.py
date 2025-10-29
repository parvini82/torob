"""
Refiner node for iterative improvement of tag extraction results.

This node re-evaluates and refines previously extracted tags
using both the original image and previous results.
"""

from typing import Any, Dict
from ..core.base_node import BaseNode
from ..config import REFINEMENT_PROMPT_TEMPLATE, VISION_MODEL
import json


class RefinerNode(BaseNode):
    """
    Node that refines and improves previously extracted tags.

    Input state keys:
        - image_url: Original image URL
        - previous_tags: Previously extracted tags to refine

    Output state keys:
        - refined_tags: Improved tag extraction results
        - refinement_raw_response: Raw model response
        - refinement_summary: Summary of changes made
    """

    def __init__(self, name: str = "refiner", config: Dict[str, Any] = None):
        """
        Initialize the refiner node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.model = self.config.get("model", VISION_MODEL)
        self.prompt_template = self.config.get("prompt", REFINEMENT_PROMPT_TEMPLATE)
        self.max_iterations = self.config.get("max_iterations", 1)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine previously extracted tags using image analysis.

        Args:
            state: Current workflow state

        Returns:
            Updated state with refined tags
        """
        self.validate_inputs(state, ["image_url"])

        # Find previous tags to refine
        previous_tags = self._find_previous_tags(state)
        if not previous_tags:
            self.log_execution("No previous tags found to refine", "warning")
            return {
                **state,
                "refined_tags": {"entities": []},
                "refinement_error": "No previous tags found",
                "step_count": state.get("step_count", 0) + 1
            }

        image_url = state["image_url"]
        self.log_execution(f"Refining {len(previous_tags.get('entities', []))} entities")

        try:
            # Import here to avoid circular imports
            from ...langgraph.model_client import (
                OpenRouterClient,
                make_image_part,
                make_text_part
            )

            client = OpenRouterClient()

            # Format previous tags for prompt
            tags_json = json.dumps(previous_tags, ensure_ascii=False, indent=2)
            prompt = self.prompt_template.format(previous_tags=tags_json)

            messages = [
                {
                    "role": "user",
                    "content": [
                        make_text_part(prompt),
                        make_image_part(image_url)
                    ]
                }
            ]

            result = client.call_json(model=self.model, messages=messages)
            refined_tags = result.get("json", {})

            # Generate refinement summary
            summary = self._generate_refinement_summary(previous_tags, refined_tags)

            self.log_execution(f"Refinement completed: {summary['changes_detected']} changes")

            return {
                **state,
                "refined_tags": refined_tags,
                "refinement_raw_response": result,
                "refinement_summary": summary,
                "final_refined_tags": refined_tags,  # Alias for compatibility
                "step_count": state.get("step_count", 0) + 1
            }

        except Exception as e:
            self.log_execution(f"Error refining tags: {str(e)}", "error")
            return {
                **state,
                "refined_tags": previous_tags,  # Fallback to original
                "refinement_error": str(e),
                "step_count": state.get("step_count", 0) + 1
            }

    def _find_previous_tags(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find previous tags in state using flexible key matching."""
        possible_keys = [
            "previous_tags",
            "image_tags",
            "merged_tags",
            "tags_from_caption"
        ]

        for key in possible_keys:
            if key in state and state[key]:
                return state[key]

        return {}

    def _generate_refinement_summary(self, original: Dict, refined: Dict) -> Dict[str, Any]:
        """Generate summary of refinement changes."""
        orig_entities = {e["name"]: set(e["values"]) for e in original.get("entities", [])}
        ref_entities = {e["name"]: set(e["values"]) for e in refined.get("entities", [])}

        added_entities = set(ref_entities.keys()) - set(orig_entities.keys())
        removed_entities = set(orig_entities.keys()) - set(ref_entities.keys())

        modified_entities = []
        for name in set(orig_entities.keys()) & set(ref_entities.keys()):
            if orig_entities[name] != ref_entities[name]:
                modified_entities.append(name)

        return {
            "original_entity_count": len(orig_entities),
            "refined_entity_count": len(ref_entities),
            "added_entities": list(added_entities),
            "removed_entities": list(removed_entities),
            "modified_entities": modified_entities,
            "changes_detected": len(added_entities) + len(removed_entities) + len(modified_entities)
        }
