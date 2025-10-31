"""
Refiner node for improving extraction quality.

Analyzes and refines extraction results to improve accuracy,
remove noise, and enhance entity relationships.
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class RefinerNode(BaseNode):
    """
    Node that refines and improves extraction results.

    Takes existing extraction results and applies quality improvements,
    noise reduction, and relationship enhancement.
    """

    def __init__(self, model: str = "google/gemini-flash-1.5"):
        """
        Initialize the refiner node.

        Args:
            model: Model to use for refinement
        """
        super().__init__("Refiner")
        self.model = model
        self.client = None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine extraction results in the state.

        Args:
            state: Workflow state containing extraction results

        Returns:
            Updated state with refined results
        """
        # Find content to refine
        refinable_content = self._find_refinable_content(state)

        if not refinable_content:
            self.logger.warning("No refinable content found in state")
            return state

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Refining content using model: {model_to_use}")

        try:
            # Refine the content
            refined_result = self._refine_content(refinable_content, model_to_use, config)

            # Update state
            updated_state = state.copy()
            updated_state["refined_tags"] = refined_result

            # Log refinement statistics
            self._log_refinement_statistics(refined_result, refinable_content)

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during refinement: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during refinement: {str(e)}")
            raise

    def _find_refinable_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find content that can be refined."""
        # Priority order for refinement sources
        sources = [
            "merged_tags",      # Prefer merged results
            "image_tags",       # Direct image analysis
            "extracted_tags"    # Text-based extraction
        ]

        for source in sources:
            if source in state and isinstance(state[source], dict):
                content = state[source]
                if self._is_refinable_content(content):
                    self.logger.debug(f"Using content from: {source}")
                    return content

        return {}

    def _is_refinable_content(self, content: Dict[str, Any]) -> bool:
        """Check if content has fields that can be refined."""
        required_fields = ["entities", "categories"]
        return any(field in content and content[field] for field in required_fields)

    def _refine_content(self, content: Dict[str, Any], model: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Refine the content using AI model."""

        # Prepare refinement prompt
        messages = [
            {
                "role": "system",
                "content": self._get_refinement_system_prompt()
            },
            {
                "role": "user",
                "content": f"Refine and improve this extraction result:\n\n{self._format_content_for_refinement(content)}"
            }
        ]

        # Get refinement
        refined_result = self.client.call_json(
            model,
            messages,
            max_tokens=config.get("max_tokens", 2000),
            temperature=config.get("temperature", 0.3)
        )

        # Structure the refined result
        return self._structure_refined_result(refined_result, content, model)

    def _get_refinement_system_prompt(self) -> str:
        """Get system prompt for refinement."""
        return """You are an expert data analyst specializing in improving extraction results.

Your task is to refine and improve the provided extraction data by:

1. **Quality Enhancement:**
   - Remove low-quality or irrelevant entities
   - Improve entity names and descriptions
   - Correct categorization errors
   - Enhance attribute associations

2. **Deduplication:**
   - Merge similar or duplicate entities
   - Consolidate related categories
   - Remove redundant attributes

3. **Relationship Enhancement:**
   - Identify hierarchical relationships between entities
   - Group related entities and attributes
   - Improve category-entity mappings

4. **Confidence Refinement:**
   - Adjust confidence scores based on evidence
   - Provide reasoning for confidence adjustments
   - Highlight high-confidence vs uncertain extractions

5. **Structure Improvements:**
   - Ensure consistent naming conventions
   - Improve attribute organization
   - Enhance summaries and descriptions

Return the refined result in this JSON structure:

{
  "entities": [
    {
      "name": "refined_entity_name",
      "type": "category/brand/feature/etc",
      "confidence": 0.0-1.0,
      "context": "enhanced context",
      "attributes": ["attr1", "attr2"],
      "relationships": ["related_entity1", "related_entity2"],
      "refinement_notes": "what was improved"
    }
  ],
  "categories": [
    {
      "name": "refined_category",
      "level": "main/sub/specific",
      "confidence": 0.0-1.0,
      "reasoning": "enhanced reasoning",
      "entities": ["entity1", "entity2"],
      "refinement_notes": "what was improved"
    }
  ],
  "attributes": {
    "color": ["refined_colors"],
    "material": ["refined_materials"],
    "style": ["refined_styles"]
  },
  "relationships": [
    {
      "type": "hierarchy/similarity/association",
      "entities": ["entity1", "entity2"],
      "strength": 0.0-1.0,
      "description": "relationship description"
    }
  ],
  "quality_improvements": {
    "entities_removed": ["removed_entity1"],
    "entities_merged": [["old1", "old2", "new_merged"]],
    "confidence_adjustments": {"entity": {"old": 0.5, "new": 0.8, "reason": "explanation"}}
  },
  "summary": "comprehensive improved summary",
  "refinement_summary": "what improvements were made"
}

Focus on accuracy, relevance, and usefulness. Be conservative - only make changes you're confident about."""

    def _format_content_for_refinement(self, content: Dict[str, Any]) -> str:
        """Format content for refinement request."""
        import json

        # Create focused content for refinement
        refinement_content = {}

        # Include key fields for refinement
        fields_to_include = [
            "entities", "categories", "attributes", "visual_attributes",
            "keywords", "summary"
        ]

        for field in fields_to_include:
            if field in content:
                refinement_content[field] = content[field]

        return json.dumps(refinement_content, indent=2, ensure_ascii=False)

    def _structure_refined_result(self, refined_data: Dict[str, Any], original_content: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Structure the refined result with metadata."""

        result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "relationships": [],
            "quality_improvements": {},
            "summary": "",
            "refinement_summary": "",
            "model_used": model,
            "refined_by": self.node_name,
            "original_source": original_content.get("extracted_by", "unknown")
        }

        # Structure refined entities
        if "entities" in refined_data:
            result["entities"] = self._structure_refined_entities(refined_data["entities"])

        # Structure refined categories
        if "categories" in refined_data:
            result["categories"] = self._structure_refined_categories(refined_data["categories"])

        # Structure refined attributes
        if "attributes" in refined_data:
            result["attributes"] = self._structure_refined_attributes(refined_data["attributes"])

        # Structure relationships
        if "relationships" in refined_data:
            result["relationships"] = self._structure_relationships(refined_data["relationships"])

        # Structure quality improvements
        if "quality_improvements" in refined_data:
            result["quality_improvements"] = refined_data["quality_improvements"]

        # Extract summaries
        result["summary"] = str(refined_data.get("summary", ""))
        result["refinement_summary"] = str(refined_data.get("refinement_summary", ""))

        return result

    def _structure_refined_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure refined entities."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                structured_entity = {
                    "name": str(entity["name"]),
                    "type": str(entity.get("type", "unknown")),
                    "confidence": float(entity.get("confidence", 0.8)),
                    "context": str(entity.get("context", "")),
                    "attributes": entity.get("attributes", []),
                    "relationships": entity.get("relationships", []),
                    "refinement_notes": str(entity.get("refinement_notes", ""))
                }
                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_refined_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure refined categories."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "level": str(category.get("level", "main")),
                    "confidence": float(category.get("confidence", 0.8)),
                    "reasoning": str(category.get("reasoning", "")),
                    "entities": category.get("entities", []),
                    "refinement_notes": str(category.get("refinement_notes", ""))
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_refined_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure refined attributes."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _structure_relationships(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure entity relationships."""
        structured_relationships = []

        for relationship in relationships:
            if isinstance(relationship, dict):
                structured_rel = {
                    "type": str(relationship.get("type", "association")),
                    "entities": relationship.get("entities", []),
                    "strength": float(relationship.get("strength", 0.5)),
                    "description": str(relationship.get("description", ""))
                }
                structured_relationships.append(structured_rel)

        return structured_relationships

    def _log_refinement_statistics(self, refined_result: Dict[str, Any], original_content: Dict[str, Any]) -> None:
        """Log statistics about the refinement operation."""
        original_entities = len(original_content.get("entities", []))
        original_categories = len(original_content.get("categories", []))

        refined_entities = len(refined_result.get("entities", []))
        refined_categories = len(refined_result.get("categories", []))

        self.logger.info("Refinement operation completed:")
        self.logger.info(f"  Entities: {original_entities} → {refined_entities}")
        self.logger.info(f"  Categories: {original_categories} → {refined_categories}")

        quality_improvements = refined_result.get("quality_improvements", {})
        if "entities_removed" in quality_improvements:
            removed_count = len(quality_improvements["entities_removed"])
            self.logger.info(f"  Entities removed: {removed_count}")

        if "entities_merged" in quality_improvements:
            merged_count = len(quality_improvements["entities_merged"])
            self.logger.info(f"  Entity merges: {merged_count}")

        relationships_count = len(refined_result.get("relationships", []))
        if relationships_count > 0:
            self.logger.info(f"  Relationships identified: {relationships_count}")
