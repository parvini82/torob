"""
Tag extraction node for text-based analysis.

Extracts structured fashion product tags from text content (like captions)
using specialized e-commerce prompts and configurable language models.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import TagExtractionPrompts

# Load environment variables
load_dotenv()

# Default model from environment
TAG_MODEL: str = os.getenv("TAG_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")


class TagExtractorNode(BaseNode):
    """
    Node that extracts structured fashion tags from text content.

    Takes text input (typically from fashion captions) and extracts relevant
    commercial tags, categories, and product attributes using specialized
    e-commerce taxonomy prompts. Designed for fashion retail applications.
    """

    def __init__(self, model: str = None):
        """
        Initialize the tag extractor node.

        Args:
            model: Language model to use. If None, uses TAG_MODEL from env
        """
        super().__init__("TagExtractor")
        self.model = model or TAG_MODEL
        self.client = None

        self.logger.info(f"Initialized with model: {self.model}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured fashion tags from text content in the state.

        Uses specialized fashion taxonomy prompts to convert descriptive text
        into structured, searchable product metadata suitable for e-commerce.

        Args:
            state: Workflow state containing text to analyze

        Returns:
            Updated state with extracted tags in fashion-specific structure

        Raises:
            ValueError: If no suitable text content found for extraction
            ModelClientError: If language model call fails
        """
        # Determine input source
        input_text = self._get_input_text(state)
        if not input_text:
            raise ValueError("No text content found for tag extraction")

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Extracting fashion tags using model: {model_to_use}")
        self.logger.debug(f"Input text preview: {input_text[:200]}...")

        try:
            # Prepare messages with specialized fashion taxonomy prompt
            messages = [
                {
                    "role": "system",
                    "content": TagExtractionPrompts.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": TagExtractionPrompts.format_user_message(input_text)
                }
            ]

            # Extract tags as JSON using fashion-specific taxonomy
            tags_result = self.client.call_json(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 1200),  # Increased for comprehensive fashion tags
                temperature=config.get("temperature", 0.2)   # Lower for more consistent structured output
            )

            # Structure the result according to fashion taxonomy
            structured_tags = self._structure_fashion_tags_result(tags_result, model_to_use, input_text)

            # Update state
            updated_state = state.copy()
            updated_state["extracted_tags"] = structured_tags

            # Log extraction statistics
            entities_count = len(structured_tags.get("entities", []))
            self.logger.info(f"Extracted {entities_count} fashion entities")
            self.logger.info(f"Categories found: {self._get_unique_categories(structured_tags)}")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during tag extraction: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during tag extraction: {str(e)}")
            raise

    def _get_input_text(self, state: Dict[str, Any]) -> str:
        """Extract input text from various possible sources in state."""
        # Priority order for text sources (fashion-specific)
        sources = [
            ("caption", "text"),           # caption.text (from CaptionGeneratorNode)
            ("description", None),         # raw description
            ("product_description", None), # product_description
            ("text", None),               # generic text
            ("content", None)             # generic content
        ]

        for source_key, sub_key in sources:
            if source_key in state:
                source_data = state[source_key]

                if sub_key and isinstance(source_data, dict):
                    text = source_data.get(sub_key)
                elif not sub_key and isinstance(source_data, str):
                    text = source_data
                else:
                    continue

                if text and isinstance(text, str) and len(text.strip()) > 0:
                    self.logger.debug(f"Using text from: {source_key}{f'.{sub_key}' if sub_key else ''}")
                    return text.strip()

        return ""

    def _structure_fashion_tags_result(self, raw_result: Dict[str, Any], model_used: str, input_text: str) -> Dict[str, Any]:
        """Structure and validate the fashion tags extraction result."""

        # Initialize structured result with fashion-specific metadata
        structured_result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "keywords": [],
            "summary": "",
            "model_used": model_used,
            "extracted_by": self.node_name,
            "extraction_type": "fashion_taxonomy",
            "input_source": "caption_text",
            "input_length": len(input_text.split())
        }

        # Process entities with fashion-specific validation
        if "entities" in raw_result and isinstance(raw_result["entities"], list):
            for entity in raw_result["entities"]:
                if isinstance(entity, dict) and "name" in entity and "values" in entity:
                    structured_entity = {
                        "name": str(entity["name"]),
                        "values": [str(v) for v in entity["values"] if v],
                        "entity_type": "fashion_attribute",
                        "confidence": 0.85,  # Default confidence for fashion taxonomy
                        "source": "text_extraction"
                    }
                    structured_result["entities"].append(structured_entity)

        # Extract key fashion categories
        fashion_categories = self._extract_fashion_categories(structured_result["entities"])
        structured_result["categories"] = fashion_categories

        # Build fashion-specific attributes dictionary
        structured_result["attributes"] = self._build_fashion_attributes(structured_result["entities"])

        # Extract fashion keywords
        structured_result["keywords"] = self._extract_fashion_keywords(structured_result["entities"])

        # Generate fashion-focused summary
        structured_result["summary"] = self._generate_fashion_summary(structured_result)

        return structured_result

    def _extract_fashion_categories(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract main fashion categories from entities."""
        categories = []

        # Look for key fashion category indicators
        category_entities = ["product_type", "category", "style", "target_demographic"]

        for entity in entities:
            if entity.get("name") in category_entities:
                for value in entity.get("values", []):
                    categories.append({
                        "name": value,
                        "type": entity.get("name"),
                        "level": "main" if entity.get("name") == "category" else "sub",
                        "confidence": 0.9
                    })

        return categories

    def _build_fashion_attributes(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build structured fashion attributes dictionary."""
        attributes = {}

        for entity in entities:
            attr_name = entity.get("name", "")
            attr_values = entity.get("values", [])

            if attr_name and attr_values:
                attributes[attr_name] = attr_values

        return attributes

    def _extract_fashion_keywords(self, entities: List[Dict[str, Any]]) -> List[str]:
        """Extract searchable fashion keywords."""
        keywords = set()

        for entity in entities:
            for value in entity.get("values", []):
                # Split compound terms and add individual words
                words = str(value).lower().replace("-", " ").split()
                keywords.update(word.strip() for word in words if len(word) > 2)

        return sorted(list(keywords))

    def _generate_fashion_summary(self, structured_result: Dict[str, Any]) -> str:
        """Generate a concise fashion-focused summary."""
        entities = structured_result.get("entities", [])

        # Find key product information
        product_type = self._find_entity_values(entities, "product_type")
        colors = self._find_entity_values(entities, "color")
        materials = self._find_entity_values(entities, "material")
        style = self._find_entity_values(entities, "style")

        summary_parts = []

        if product_type:
            summary_parts.append(f"Product: {', '.join(product_type[:2])}")
        if colors:
            summary_parts.append(f"Colors: {', '.join(colors[:3])}")
        if materials:
            summary_parts.append(f"Materials: {', '.join(materials[:2])}")
        if style:
            summary_parts.append(f"Style: {', '.join(style[:2])}")

        return " | ".join(summary_parts) if summary_parts else "Fashion product analysis completed"

    def _find_entity_values(self, entities: List[Dict[str, Any]], entity_name: str) -> List[str]:
        """Find values for a specific entity name."""
        for entity in entities:
            if entity.get("name") == entity_name:
                return entity.get("values", [])
        return []

    def _get_unique_categories(self, structured_tags: Dict[str, Any]) -> List[str]:
        """Get list of unique category names for logging."""
        categories = structured_tags.get("categories", [])
        return list(set(cat.get("name", "") for cat in categories if cat.get("name")))
