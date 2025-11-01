"""
Direct image tag extraction node.

Extracts structured fashion tags directly from images without intermediate
caption generation using specialized computer vision and fashion analysis prompts.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import ImageTagExtractionPrompts

# Load environment variables
load_dotenv()

# Default vision model from environment
VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")


class ImageTagExtractorNode(BaseNode):
    """
    Node that extracts structured fashion tags directly from images.

    Uses advanced computer vision models with specialized fashion industry
    prompts to analyze product images and extract comprehensive commercial
    metadata without requiring intermediate text generation.
    """

    def __init__(self, model: str = None):
        """
        Initialize the image tag extractor node.

        Args:
            model: Vision model to use. If None, uses VISION_MODEL from env
        """
        super().__init__("ImageTagExtractor")
        self.model = model or VISION_MODEL
        self.client = None

        self.logger.info(f"Initialized with vision model: {self.model}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured fashion tags directly from the image.

        Uses specialized computer vision and fashion analysis prompts to
        perform comprehensive visual product analysis and extract commercial
        metadata suitable for e-commerce applications.

        Args:
            state: Workflow state containing image_url

        Returns:
            Updated state with extracted image tags in fashion-specific structure

        Raises:
            ValueError: If image_url is missing from state
            ModelClientError: If vision model call fails
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
        self.logger.info(f"Extracting fashion tags directly from image using model: {model_to_use}")

        try:
            # Prepare messages with specialized computer vision fashion prompt
            messages = [
                {
                    "role": "system",
                    "content": ImageTagExtractionPrompts.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this fashion product image and extract comprehensive commercial metadata using the systematic visual analysis protocol."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]

            # Extract tags as JSON using specialized computer vision analysis
            tags_result = self.client.call_json(
                model_to_use,
                messages,
                max_tokens=config.get("max_tokens", 2000),  # Increased for comprehensive fashion analysis
                temperature=config.get("temperature", 0.1)   # Very low for consistent structured output
            )

            # Structure the result according to fashion taxonomy
            structured_tags = self._structure_image_fashion_tags_result(tags_result, model_to_use)

            # Update state
            updated_state = state.copy()
            updated_state["image_tags"] = structured_tags

            # Log extraction statistics
            entities_count = len(structured_tags.get("entities", []))
            unique_categories = self._get_unique_categories(structured_tags)

            self.logger.info(f"Extracted {entities_count} fashion entities from image")
            self.logger.info(f"Visual categories identified: {unique_categories[:5]}")  # Show first 5

            # Log quality assessment if available
            quality_score = structured_tags.get("quality_score", 0)
            if quality_score > 0:
                self.logger.info(f"Image analysis quality score: {quality_score:.2f}")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Vision model error during image tag extraction: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during image tag extraction: {str(e)}")
            raise

    def _structure_image_fashion_tags_result(self, raw_result: Dict[str, Any], model_used: str) -> Dict[str, Any]:
        """Structure and validate the image fashion tags extraction result."""

        # Initialize structured result with fashion-specific metadata
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
            "extraction_type": "direct_image_analysis",
            "analysis_method": "computer_vision_fashion"
        }

        # Process entities with fashion-specific structure adaptation
        if "entities" in raw_result and isinstance(raw_result["entities"], list):
            for entity in raw_result["entities"]:
                if isinstance(entity, dict) and "name" in entity and "values" in entity:
                    structured_entity = {
                        "name": str(entity["name"]),
                        "values": [str(v) for v in entity["values"] if v],
                        "entity_type": "visual_attribute",
                        "confidence": 0.85,  # Default confidence for visual analysis
                        "source": "direct_image_analysis",
                        "visual_evidence": "confirmed"
                    }
                    structured_result["entities"].append(structured_entity)

        # Extract visual categories from entities
        visual_categories = self._extract_visual_categories(structured_result["entities"])
        structured_result["categories"] = visual_categories

        # Build visual attributes dictionary
        structured_result["visual_attributes"] = self._build_visual_attributes(structured_result["entities"])

        # Extract scene context information
        structured_result["scene_context"] = self._extract_scene_context(raw_result)

        # Extract detected text and brands
        structured_result["text_detected"] = self._extract_detected_text(raw_result)
        structured_result["brands_visible"] = self._extract_visible_brands(raw_result)

        # Extract quality score
        structured_result["quality_score"] = self._extract_quality_score(raw_result)

        # Generate comprehensive visual summary
        structured_result["summary"] = self._generate_visual_summary(structured_result)

        return structured_result

    def _extract_visual_categories(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract visual categories from fashion entities."""
        categories = []

        # Key visual category indicators for fashion
        category_entities = [
            "product_type", "subcategory", "style_classification",
            "target_demographic", "occasion_primary"
        ]

        for entity in entities:
            if entity.get("name") in category_entities:
                for value in entity.get("values", []):
                    categories.append({
                        "name": value,
                        "type": entity.get("name"),
                        "level": self._determine_category_level(entity.get("name")),
                        "confidence": 0.9,
                        "visual_evidence": "confirmed",
                        "source": "direct_image_analysis"
                    })

        return categories

    def _determine_category_level(self, entity_name: str) -> str:
        """Determine hierarchy level for fashion categories."""
        level_mapping = {
            "product_type": "main",
            "subcategory": "sub",
            "style_classification": "specific",
            "target_demographic": "demographic",
            "occasion_primary": "usage"
        }
        return level_mapping.get(entity_name, "general")

    def _build_visual_attributes(self, entities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build structured visual attributes dictionary."""
        visual_attrs = {}

        # Focus on visual fashion attributes
        visual_attribute_names = [
            "color_primary", "color_secondary", "pattern_type",
            "material_primary", "texture_finish", "fit_profile",
            "construction_features", "hardware_details", "design_elements"
        ]

        for entity in entities:
            attr_name = entity.get("name", "")
            attr_values = entity.get("values", [])

            if attr_name in visual_attribute_names and attr_values:
                visual_attrs[attr_name] = attr_values

        return visual_attrs

    def _extract_scene_context(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scene context information from raw result."""
        scene_context = {}

        # Look for scene context in raw result
        if "scene_context" in raw_result and isinstance(raw_result["scene_context"], dict):
            scene_context = {
                k: str(v) for k, v in raw_result["scene_context"].items() if v
            }

        return scene_context

    def _extract_detected_text(self, raw_result: Dict[str, Any]) -> List[str]:
        """Extract any text detected in the image."""
        detected_text = []

        if "text_detected" in raw_result and isinstance(raw_result["text_detected"], list):
            detected_text = [str(text) for text in raw_result["text_detected"] if text]

        return detected_text

    def _extract_visible_brands(self, raw_result: Dict[str, Any]) -> List[str]:
        """Extract visible brand names from the image."""
        brands = []

        if "brands_visible" in raw_result and isinstance(raw_result["brands_visible"], list):
            brands = [str(brand) for brand in raw_result["brands_visible"] if brand]

        return brands

    def _extract_quality_score(self, raw_result: Dict[str, Any]) -> float:
        """Extract image analysis quality score."""
        try:
            return float(raw_result.get("quality_score", 0.0))
        except (ValueError, TypeError):
            return 0.8  # Default reasonable quality score

    def _generate_visual_summary(self, structured_result: Dict[str, Any]) -> str:
        """Generate a comprehensive visual analysis summary."""
        entities = structured_result.get("entities", [])

        # Find key visual elements
        product_type = self._find_entity_values(entities, "product_type")
        colors = self._find_entity_values(entities, "color_primary")
        materials = self._find_entity_values(entities, "material_primary")
        style = self._find_entity_values(entities, "style_classification")
        quality_tier = self._find_entity_values(entities, "quality_tier")

        summary_parts = []

        if product_type:
            summary_parts.append(f"Visual ID: {', '.join(product_type[:2])}")
        if colors:
            summary_parts.append(f"Colors: {', '.join(colors[:3])}")
        if materials:
            summary_parts.append(f"Materials: {', '.join(materials[:2])}")
        if style:
            summary_parts.append(f"Style: {', '.join(style[:2])}")
        if quality_tier:
            summary_parts.append(f"Quality: {', '.join(quality_tier[:1])}")

        # Add image quality info
        quality_score = structured_result.get("quality_score", 0)
        if quality_score > 0:
            summary_parts.append(f"Analysis Score: {quality_score:.2f}")

        return " | ".join(summary_parts) if summary_parts else "Direct image analysis completed"

    def _find_entity_values(self, entities: List[Dict[str, Any]], entity_name: str) -> List[str]:
        """Find values for a specific entity name in the entities list."""
        for entity in entities:
            if entity.get("name") == entity_name:
                return entity.get("values", [])
        return []

    def _get_unique_categories(self, structured_tags: Dict[str, Any]) -> List[str]:
        """Get list of unique category names for logging."""
        categories = structured_tags.get("categories", [])
        return list(set(cat.get("name", "") for cat in categories if cat.get("name")))
