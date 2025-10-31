"""
Tag extraction node for text-based analysis.

Extracts structured tags and entities from text content (like captions).
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class TagExtractorNode(BaseNode):
    """
    Node that extracts structured tags from text content.

    Takes text input (typically from captions) and extracts relevant
    tags, categories, and entities in a structured format.
    """

    def __init__(self, model: str = "google/gemini-flash-1.5"):
        """
        Initialize the tag extractor node.

        Args:
            model: Model to use for tag extraction
        """
        super().__init__("TagExtractor")
        self.model = model
        self.client = None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags from text content in the state.

        Args:
            state: Workflow state containing text to analyze

        Returns:
            Updated state with extracted tags
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

        self.logger.info(f"Extracting tags from text using model: {model_to_use}")
        self.logger.debug(f"Input text preview: {input_text[:100]}...")

        try:
            # Prepare messages for tag extraction
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"Extract tags from this text:\n\n{input_text}"
                }
            ]

            # Extract tags as JSON
            tags_result = self.client.call_json(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 1000),
                temperature=config.get("temperature", 0.3)
            )

            # Validate and structure the result
            structured_tags = self._structure_tags_result(tags_result, model_to_use)

            # Update state
            updated_state = state.copy()
            updated_state["extracted_tags"] = structured_tags

            self.logger.info(f"Extracted {len(structured_tags.get('entities', []))} entities")
            self.logger.info(f"Found {len(structured_tags.get('categories', []))} categories")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during tag extraction: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during tag extraction: {str(e)}")
            raise

    def _get_input_text(self, state: Dict[str, Any]) -> str:
        """Extract input text from various possible sources in state."""
        # Priority order for text sources
        sources = [
            ("caption", "text"),           # caption.text
            ("description", None),         # description
            ("text", None),               # text
            ("content", None)             # content
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

    def _get_system_prompt(self) -> str:
        """Get the system prompt for tag extraction."""
        return """You are an expert at extracting structured information from text descriptions.

Extract the following information from the provided text and return it as JSON:

{
  "entities": [
    {
      "name": "entity_name",
      "type": "category/brand/feature/material/color/etc",
      "confidence": 0.0-1.0,
      "context": "relevant context from text"
    }
  ],
  "categories": [
    {
      "name": "category_name", 
      "level": "main/sub/specific",
      "confidence": 0.0-1.0
    }
  ],
  "attributes": {
    "color": ["color1", "color2"],
    "material": ["material1", "material2"],
    "style": ["style1", "style2"],
    "features": ["feature1", "feature2"]
  },
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "summary": "brief summary of extracted information"
}

Focus on:
- Product/object names and types
- Brands and manufacturers
- Physical attributes (color, material, size, shape)
- Functional features and capabilities
- Style and design elements
- Categories and classifications

Be accurate and only extract information that is clearly present in the text."""

    def _structure_tags_result(self, raw_result: Dict[str, Any], model_used: str) -> Dict[str, Any]:
        """Structure and validate the tags extraction result."""
        structured_result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "keywords": [],
            "summary": "",
            "model_used": model_used,
            "extracted_by": self.node_name
        }

        # Extract entities
        if "entities" in raw_result and isinstance(raw_result["entities"], list):
            for entity in raw_result["entities"]:
                if isinstance(entity, dict) and "name" in entity:
                    structured_entity = {
                        "name": str(entity["name"]),
                        "type": entity.get("type", "unknown"),
                        "confidence": float(entity.get("confidence", 0.8)),
                        "context": entity.get("context", "")
                    }
                    structured_result["entities"].append(structured_entity)

        # Extract categories
        if "categories" in raw_result and isinstance(raw_result["categories"], list):
            for category in raw_result["categories"]:
                if isinstance(category, dict) and "name" in category:
                    structured_category = {
                        "name": str(category["name"]),
                        "level": category.get("level", "main"),
                        "confidence": float(category.get("confidence", 0.8))
                    }
                    structured_result["categories"].append(structured_category)

        # Extract attributes
        if "attributes" in raw_result and isinstance(raw_result["attributes"], dict):
            for attr_key, attr_values in raw_result["attributes"].items():
                if isinstance(attr_values, list):
                    structured_result["attributes"][attr_key] = [str(v) for v in attr_values]
                elif attr_values:  # Single value
                    structured_result["attributes"][attr_key] = [str(attr_values)]

        # Extract keywords
        if "keywords" in raw_result and isinstance(raw_result["keywords"], list):
            structured_result["keywords"] = [str(kw) for kw in raw_result["keywords"] if kw]

        # Extract summary
        if "summary" in raw_result:
            structured_result["summary"] = str(raw_result["summary"])

        return structured_result
