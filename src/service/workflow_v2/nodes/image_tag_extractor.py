"""
Direct image tag extraction node.

Extracts tags directly from images without intermediate caption generation.
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class ImageTagExtractorNode(BaseNode):
    """
    Node that extracts tags directly from images.

    Uses vision models to analyze images and extract structured
    tags, entities, and categories without intermediate text generation.
    """

    def __init__(self, model: str = "google/gemini-flash-1.5"):
        """
        Initialize the image tag extractor node.

        Args:
            model: Vision model to use for direct image analysis
        """
        super().__init__("ImageTagExtractor")
        self.model = model
        self.client = None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags directly from the image.

        Args:
            state: Workflow state containing image_url

        Returns:
            Updated state with extracted image tags
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
        self.logger.info(f"Extracting tags directly from image using model: {model_to_use}")

        try:
            # Prepare messages for direct image analysis
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
                            "text": "Analyze this image and extract structured tags and information."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]

            # Extract tags as JSON
            tags_result = self.client.call_json(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 1500),
                temperature=config.get("temperature", 0.3)
            )

            # Structure the result
            structured_tags = self._structure_image_tags_result(tags_result, model_to_use)

            # Update state
            updated_state = state.copy()
            updated_state["image_tags"] = structured_tags

            self.logger.info(f"Extracted {len(structured_tags.get('entities', []))} entities from image")
            self.logger.info(f"Identified {len(structured_tags.get('categories', []))} categories")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during image tag extraction: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during image tag extraction: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """Get the system prompt for direct image tag extraction."""
        return """You are an expert computer vision analyst. Analyze images and extract comprehensive structured information.

Examine the image carefully and return detailed information as JSON:

{
  "entities": [
    {
      "name": "object/brand/feature name",
      "type": "product/brand/feature/material/color/shape/etc",
      "confidence": 0.0-1.0,
      "location": "description of where in image",
      "attributes": ["attr1", "attr2"]
    }
  ],
  "categories": [
    {
      "name": "category name",
      "level": "main/sub/specific", 
      "confidence": 0.0-1.0,
      "reasoning": "why this category applies"
    }
  ],
  "visual_attributes": {
    "colors": ["primary_color", "secondary_color"],
    "materials": ["material1", "material2"],
    "textures": ["texture1", "texture2"],
    "shapes": ["shape1", "shape2"],
    "patterns": ["pattern1", "pattern2"]
  },
  "scene_context": {
    "setting": "indoor/outdoor/studio/etc",
    "lighting": "bright/dim/natural/artificial",
    "background": "description",
    "composition": "close-up/wide/etc"
  },
  "text_detected": ["any visible text"],
  "brands_visible": ["brand1", "brand2"],
  "quality_score": 0.0-1.0,
  "summary": "comprehensive summary of what you see"
}

Be thorough and accurate. Only include information you can clearly observe in the image. Assign appropriate confidence scores based on visibility and certainty."""

    def _structure_image_tags_result(self, raw_result: Dict[str, Any], model_used: str) -> Dict[str, Any]:
        """Structure and validate the image tags extraction result."""
        structured_result = {
            "entities": [],
            "categories": [],
            "visual_attributes": {},
            "scene_context": {},
            "text_detected": [],
            "brands_visible": [],
            "quality_score": 0.0,
            "summary": "",
            "model_used": model_used,
            "extracted_by": self.node_name,
            "extraction_type": "direct_image_analysis"
        }

        # Extract entities
        if "entities" in raw_result and isinstance(raw_result["entities"], list):
            for entity in raw_result["entities"]:
                if isinstance(entity, dict) and "name" in entity:
                    structured_entity = {
                        "name": str(entity["name"]),
                        "type": entity.get("type", "unknown"),
                        "confidence": float(entity.get("confidence", 0.8)),
                        "location": entity.get("location", ""),
                        "attributes": entity.get("attributes", [])
                    }
                    structured_result["entities"].append(structured_entity)

        # Extract categories
        if "categories" in raw_result and isinstance(raw_result["categories"], list):
            for category in raw_result["categories"]:
                if isinstance(category, dict) and "name" in category:
                    structured_category = {
                        "name": str(category["name"]),
                        "level": category.get("level", "main"),
                        "confidence": float(category.get("confidence", 0.8)),
                        "reasoning": category.get("reasoning", "")
                    }
                    structured_result["categories"].append(structured_category)

        # Extract visual attributes
        if "visual_attributes" in raw_result and isinstance(raw_result["visual_attributes"], dict):
            for attr_key, attr_values in raw_result["visual_attributes"].items():
                if isinstance(attr_values, list):
                    structured_result["visual_attributes"][attr_key] = [str(v) for v in attr_values if v]
                elif attr_values:
                    structured_result["visual_attributes"][attr_key] = [str(attr_values)]

        # Extract scene context
        if "scene_context" in raw_result and isinstance(raw_result["scene_context"], dict):
            structured_result["scene_context"] = {
                k: str(v) for k, v in raw_result["scene_context"].items() if v
            }

        # Extract detected text
        if "text_detected" in raw_result and isinstance(raw_result["text_detected"], list):
            structured_result["text_detected"] = [str(text) for text in raw_result["text_detected"] if text]

        # Extract visible brands
        if "brands_visible" in raw_result and isinstance(raw_result["brands_visible"], list):
            structured_result["brands_visible"] = [str(brand) for brand in raw_result["brands_visible"] if brand]

        # Extract quality score
        if "quality_score" in raw_result:
            try:
                structured_result["quality_score"] = float(raw_result["quality_score"])
            except (ValueError, TypeError):
                structured_result["quality_score"] = 0.8

        # Extract summary
        if "summary" in raw_result:
            structured_result["summary"] = str(raw_result["summary"])

        return structured_result
