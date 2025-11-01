"""
Refiner node for improving fashion extraction quality.

Analyzes and refines fashion product extraction results to improve accuracy,
remove noise, enhance commercial relevance, and optimize for e-commerce usage.
"""

from typing import Dict, Any, List

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import RefinementPrompts
from ..config import get_model


class RefinerNode(BaseNode):
    """
    Node that refines and improves fashion extraction results.

    Takes existing extraction results and applies quality assurance improvements,
    commercial optimization, noise reduction, and fashion industry compliance
    to maximize e-commerce value and search accuracy.
    """

    def __init__(self, model: str = None):
        """
        Initialize the refiner node.

        Args:
            model: Refinement model to use. If None, uses REFINE_MODEL from env
        """
        super().__init__("Refiner")
        self.model = model or get_model("refiner")
        self.client = None

        self.logger.info(f"Initialized fashion refiner with model: {self.model}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine fashion extraction results in the state.

        Applies systematic quality assurance and commercial optimization to
        fashion extraction results using specialized merchandising expertise
        and industry best practices.

        Args:
            state: Workflow state containing extraction results

        Returns:
            Updated state with refined fashion results

        Raises:
            ModelClientError: If refinement model call fails
        """
        # Find content to refine
        refinable_content = self._find_refinable_fashion_content(state)

        if not refinable_content:
            self.logger.warning("No refinable fashion content found in state")
            return state

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Refining fashion content using model: {model_to_use}")
        self.logger.info(f"Input entities: {len(refinable_content.get('entities', []))}")

        try:
            # Refine the fashion content
            refined_result = self._refine_fashion_content(refinable_content, model_to_use, config)

            # Update state
            updated_state = state.copy()
            updated_state["refined_tags"] = refined_result

            # Log refinement statistics
            self._log_fashion_refinement_statistics(refined_result, refinable_content)

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Refinement model error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during fashion refinement: {str(e)}")
            raise

    def _find_refinable_fashion_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find fashion content that can be refined."""
        # Priority order for fashion refinement sources
        sources = [
            "merged_tags",      # Prefer merged results for comprehensive refinement
            "image_tags",       # Direct visual analysis results
            "extracted_tags"    # Text-based extraction results
        ]

        for source in sources:
            if source in state and isinstance(state[source], dict):
                content = state[source]
                if self._is_refinable_fashion_content(content):
                    self.logger.debug(f"Using fashion content from: {source}")
                    return content

        return {}

    def _is_refinable_fashion_content(self, content: Dict[str, Any]) -> bool:
        """Check if content has fashion fields that can be refined."""
        # Fashion-specific refineable fields
        required_fields = ["entities"]  # At minimum need entities
        optional_fields = ["categories", "attributes", "visual_attributes"]

        has_required = any(field in content and content[field] for field in required_fields)
        has_optional = any(field in content and content[field] for field in optional_fields)

        return has_required and (has_optional or len(content.get("entities", [])) > 0)

    def _refine_fashion_content(self, content: Dict[str, Any], model: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Refine the fashion content using specialized QA prompts."""

        # Prepare content for fashion refinement
        import json
        content_json = json.dumps(content, indent=2, ensure_ascii=False)

        # Prepare specialized fashion QA refinement request
        messages = [
            {
                "role": "system",
                "content": RefinementPrompts.SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": RefinementPrompts.format_user_message(content_json)
            }
        ]

        # Get refinement
        refined_result = self.client.call_json(
            model,
            messages,
            max_tokens=config.get("max_tokens", 2500),  # Increased for comprehensive fashion refinement
            temperature=config.get("temperature", 0.2)   # Low for consistent professional output
        )

        # Structure the refined result
        return self._structure_fashion_refined_result(refined_result, content, model)

    def _structure_fashion_refined_result(self, refined_data: Dict[str, Any], original_content: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Structure the refined fashion result with QA metadata."""

        result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "visual_attributes": {},
            "quality_improvements": {},
            "summary": "",
            "refinement_summary": "",
            "model_used": model,
            "refined_by": self.node_name,
            "refinement_type": "fashion_qa_specialist",
            "original_source": original_content.get("extracted_by", "unknown"),
            "commercial_optimization": True
        }

        # Structure refined entities (handle both formats)
        if "entities" in refined_data:
            result["entities"] = self._structure_refined_fashion_entities(refined_data["entities"])

        # Structure refined categories
        if "categories" in refined_data:
            result["categories"] = self._structure_refined_fashion_categories(refined_data["categories"])

        # Structure refined attributes
        for attr_field in ["attributes", "visual_attributes"]:
            if attr_field in refined_data:
                result[attr_field] = self._structure_refined_fashion_attributes(refined_data[attr_field])

        # Extract quality improvements info
        if "quality_improvements" in refined_data:
            result["quality_improvements"] = refined_data["quality_improvements"]

        # Extract summaries
        result["summary"] = str(refined_data.get("summary", ""))
        result["refinement_summary"] = str(refined_data.get("refinement_summary", ""))

        return result

    def _structure_refined_fashion_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure refined fashion entities."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict):
                # Handle new fashion format (name/values)
                if "name" in entity and "values" in entity:
                    structured_entity = {
                        "name": str(entity["name"]),
                        "values": [str(v) for v in entity["values"] if v] if isinstance(entity["values"], list) else [str(entity["values"])],
                        "entity_type": "refined_fashion_attribute",
                        "confidence": 0.9,  # Higher confidence after refinement
                        "source": "qa_refinement",
                        "quality_verified": True
                    }
                elif "name" in entity:
                    # Legacy format handling
                    structured_entity = {
                        "name": str(entity["name"]),
                        "type": str(entity.get("type", "unknown")),
                        "confidence": float(entity.get("confidence", 0.9)),
                        "context": str(entity.get("context", "")),
                        "attributes": entity.get("attributes", []),
                        "refinement_notes": str(entity.get("refinement_notes", ""))
                    }
                else:
                    continue

                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_refined_fashion_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure refined fashion categories."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "type": category.get("type", "general"),
                    "level": str(category.get("level", "main")),
                    "confidence": float(category.get("confidence", 0.9)),
                    "reasoning": str(category.get("reasoning", "")),
                    "entities": category.get("entities", []),
                    "refinement_notes": str(category.get("refinement_notes", "")),
                    "qa_verified": True
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_refined_fashion_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure refined fashion attributes."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _log_fashion_refinement_statistics(self, refined_result: Dict[str, Any], original_content: Dict[str, Any]) -> None:
        """Log statistics about the fashion refinement operation."""
        original_entities = len(original_content.get("entities", []))
        refined_entities = len(refined_result.get("entities", []))

        original_categories = len(original_content.get("categories", []))
        refined_categories = len(refined_result.get("categories", []))

        self.logger.info("Fashion QA refinement completed:")
        self.logger.info(f"  Entities: {original_entities} → {refined_entities}")
        self.logger.info(f"  Categories: {original_categories} → {refined_categories}")

        # Log quality improvements
        quality_improvements = refined_result.get("quality_improvements", {})
        if "entities_removed" in quality_improvements:
            removed_count = len(quality_improvements["entities_removed"])
            self.logger.info(f"  Low-quality entities removed: {removed_count}")

        if "entities_merged" in quality_improvements:
            merged_count = len(quality_improvements["entities_merged"])
            self.logger.info(f"  Entity consolidations: {merged_count}")

        # Log refinement focus
        refinement_summary = refined_result.get("refinement_summary", "")
        if refinement_summary:
            self.logger.info(f"  Refinement focus: {refinement_summary[:100]}...")
