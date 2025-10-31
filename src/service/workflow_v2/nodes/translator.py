"""
Translation node for multilingual content processing.

Translates extracted tags and content between languages while preserving
structure and maintaining translation quality.
"""

from typing import Dict, Any, List
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class TranslatorNode(BaseNode):
    """
    Node that translates structured content between languages.

    Takes extracted tags and entities in one language and produces
    equivalent structured content in the target language.
    """

    def __init__(self,
                 model: str = "google/gemini-flash-1.5",
                 target_language: str = "Persian",
                 source_language: str = "English"):
        """
        Initialize the translator node.

        Args:
            model: Model to use for translation
            target_language: Target language for translation
            source_language: Source language (auto-detected if not specified)
        """
        super().__init__("Translator")
        self.model = model
        self.target_language = target_language
        self.source_language = source_language
        self.client = None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate structured content to target language.

        Args:
            state: Workflow state containing extractable content

        Returns:
            Updated state with translated content
        """
        # Find translatable content in state
        translatable_data = self._extract_translatable_content(state)

        if not translatable_data:
            self.logger.warning("No translatable content found in state")
            return state

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)
        target_lang = config.get("target_language", self.target_language)
        source_lang = config.get("source_language", self.source_language)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Translating content from {source_lang} to {target_lang}")
        self.logger.info(f"Found {len(translatable_data)} items to translate")

        try:
            translated_results = {}

            # Translate each data source
            for source_key, content in translatable_data.items():
                self.logger.debug(f"Translating content from: {source_key}")

                translated_content = self._translate_structured_content(
                    content, source_lang, target_lang, model_to_use
                )

                # Store with target language suffix
                result_key = f"{target_lang.lower()}_output"
                translated_results[result_key] = translated_content

            # If multiple sources, merge them intelligently
            if len(translated_results) > 1:
                merged_translation = self._merge_translations(translated_results, target_lang)
                final_key = f"{target_lang.lower()}_output"
                translated_results = {final_key: merged_translation}

            # Update state
            updated_state = state.copy()
            updated_state.update(translated_results)

            # Add translation metadata
            updated_state["translation_info"] = {
                "source_language": source_lang,
                "target_language": target_lang,
                "model_used": model_to_use,
                "translated_by": self.node_name,
                "sources_translated": list(translatable_data.keys())
            }

            self.logger.info(f"Successfully translated content to {target_lang}")
            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during translation: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during translation: {str(e)}")
            raise

    def _extract_translatable_content(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract content that can be translated from the state."""
        translatable_sources = [
            "extracted_tags",
            "image_tags",
            "merged_tags",
            "refined_tags"
        ]

        found_content = {}

        for source in translatable_sources:
            if source in state and isinstance(state[source], dict):
                content = state[source]

                # Check if content has translatable fields
                if self._has_translatable_fields(content):
                    found_content[source] = content
                    self.logger.debug(f"Found translatable content in: {source}")

        return found_content

    def _has_translatable_fields(self, content: Dict[str, Any]) -> bool:
        """Check if content has fields that can be translated."""
        translatable_fields = ["entities", "categories", "summary", "keywords"]

        return any(
            field in content and content[field]
            for field in translatable_fields
        )

    def _translate_structured_content(self,
                                    content: Dict[str, Any],
                                    source_lang: str,
                                    target_lang: str,
                                    model: str) -> Dict[str, Any]:
        """Translate structured content while preserving format."""

        # Prepare translation request
        messages = [
            {
                "role": "system",
                "content": self._get_translation_system_prompt(source_lang, target_lang)
            },
            {
                "role": "user",
                "content": f"Translate this structured content:\n\n{self._format_content_for_translation(content)}"
            }
        ]

        # Get translation
        translated_result = self.client.call_json(
            model,
            messages,
            max_tokens=2000,
            temperature=0.3
        )

        # Structure the translated result
        return self._structure_translated_result(translated_result, content, target_lang)

    def _get_translation_system_prompt(self, source_lang: str, target_lang: str) -> str:
        """Get system prompt for translation."""
        return f"""You are an expert translator specializing in structured content translation from {source_lang} to {target_lang}.

Translate the provided structured data while:
1. Preserving the exact JSON structure and field names
2. Translating only the content values, not the keys
3. Maintaining technical accuracy for product/brand names
4. Keeping confidence scores and metadata unchanged
5. Providing culturally appropriate translations
6. Preserving any English brand names or technical terms when appropriate

Return the translated content in the same JSON structure format.

For {target_lang} translation specifically:
- Use proper {target_lang} grammar and terminology
- Keep internationally recognized brand names in English
- Translate descriptive terms and categories appropriately
- Maintain technical precision

Output only the translated JSON, no additional text."""

    def _format_content_for_translation(self, content: Dict[str, Any]) -> str:
        """Format content for translation request."""
        import json

        # Create a clean version for translation
        translation_content = {}

        # Include translatable fields
        translatable_fields = {
            "entities": True,
            "categories": True,
            "summary": True,
            "keywords": True,
            "attributes": True,
            "visual_attributes": True
        }

        for field, should_translate in translatable_fields.items():
            if field in content and should_translate:
                translation_content[field] = content[field]

        return json.dumps(translation_content, indent=2, ensure_ascii=False)

    def _structure_translated_result(self,
                                   translated_data: Dict[str, Any],
                                   original_content: Dict[str, Any],
                                   target_lang: str) -> Dict[str, Any]:
        """Structure the translated result with metadata."""

        # Start with original structure
        result = original_content.copy()

        # Update with translated content
        if "entities" in translated_data:
            result["entities"] = self._structure_translated_entities(translated_data["entities"])

        if "categories" in translated_data:
            result["categories"] = self._structure_translated_categories(translated_data["categories"])

        if "summary" in translated_data:
            result["summary"] = str(translated_data["summary"])

        if "keywords" in translated_data:
            result["keywords"] = [str(kw) for kw in translated_data["keywords"] if kw]

        # Handle attributes
        for attr_field in ["attributes", "visual_attributes"]:
            if attr_field in translated_data:
                result[attr_field] = self._structure_translated_attributes(translated_data[attr_field])

        # Add translation metadata
        result["language"] = target_lang.lower()
        result["translation_source"] = original_content.get("extracted_by", "unknown")

        return result

    def _structure_translated_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure translated entities."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                structured_entity = {
                    "name": str(entity["name"]),
                    "type": str(entity.get("type", "unknown")),
                    "confidence": entity.get("confidence", 0.8),
                    "context": str(entity.get("context", "")),
                    "attributes": entity.get("attributes", [])
                }
                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_translated_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure translated categories."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "level": category.get("level", "main"),
                    "confidence": category.get("confidence", 0.8),
                    "reasoning": str(category.get("reasoning", ""))
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_translated_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure translated attributes."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _merge_translations(self, translations: Dict[str, Dict[str, Any]], target_lang: str) -> Dict[str, Any]:
        """Merge multiple translations into a single result."""
        merged_result = {
            "entities": [],
            "categories": [],
            "keywords": [],
            "summary": "",
            "language": target_lang.lower(),
            "merged_from": list(translations.keys())
        }

        # Merge entities from all sources
        seen_entities = set()
        for trans_data in translations.values():
            for entity in trans_data.get("entities", []):
                entity_key = f"{entity['name']}_{entity['type']}"
                if entity_key not in seen_entities:
                    merged_result["entities"].append(entity)
                    seen_entities.add(entity_key)

        # Merge categories
        seen_categories = set()
        for trans_data in translations.values():
            for category in trans_data.get("categories", []):
                if category["name"] not in seen_categories:
                    merged_result["categories"].append(category)
                    seen_categories.add(category["name"])

        # Merge keywords
        all_keywords = set()
        for trans_data in translations.values():
            for keyword in trans_data.get("keywords", []):
                all_keywords.add(keyword)
        merged_result["keywords"] = list(all_keywords)

        # Use the most comprehensive summary
        summaries = [trans_data.get("summary", "") for trans_data in translations.values()]
        merged_result["summary"] = max(summaries, key=len) if summaries else ""

        return merged_result
