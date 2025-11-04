"""
Translation node for multilingual fashion content processing.

Translates extracted fashion tags and content from English to Persian while
preserving structure and maintaining fashion industry terminology accuracy.
"""

from typing import Dict, Any, List
import json
import re
import traceback
from datetime import datetime

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import TranslationPrompts  # استفاده از پرامپت موجود
from ..config import get_model
from .utils.json_sanitizer import sanitize_json_response
from .utils.retry_handler import with_retry, RetryError


class TranslationLogger:
    """Enhanced logging for translation debugging."""

    def __init__(self, logger):
        self.logger = logger

    def log_parsing_failure(self, raw_response: str, error: Exception, model: str):
        """Log detailed parsing failure info."""
        timestamp = datetime.now().isoformat()
        error_details = {
            "timestamp": timestamp,
            "model": model,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "response_length": len(raw_response),
            "response_preview": raw_response[:200].replace('\n', ' '),
            "traceback": traceback.format_exc()
        }

        self.logger.error(f"JSON Parsing Failure Details: {json.dumps(error_details, indent=2)}")

        # Check for common patterns in failed responses
        self._analyze_failure_patterns(raw_response)

    def _analyze_failure_patterns(self, response: str):
        """Analyze common failure patterns in LLM responses."""
        patterns = {
            "has_explanation": bool(re.search(r'^(here|this|the result)', response.lower().strip())),
            "has_markdown": bool(re.search(r'```', response)),
            "has_single_quotes": bool(re.search(r"'[^']*':", response)),
            "has_unquoted_keys": bool(re.search(r'[{,]\s*[a-zA-Z_]+\s*:', response)),
            "truncated_response": response.strip().endswith(',') or not (
                response.strip().endswith('}') or response.strip().endswith(']')),
        }

        self.logger.warning(f"Failure pattern analysis: {patterns}")


class TranslatorNode(BaseNode):
    """
    Node that translates structured fashion content from English to Persian.

    Takes extracted fashion tags and entities in English and produces
    equivalent structured content in Persian while maintaining commercial
    terminology accuracy and fashion industry standards.
    """

    def __init__(self,
                 model: str = None,
                 target_language: str = "Persian",
                 source_language: str = "English"):
        """
        Initialize the translator node.

        Args:
            model: Translation model to use. If None, uses centralized config
            target_language: Target language for translation (default: Persian)
            source_language: Source language (default: English)
        """
        super().__init__("Translator")
        self.model = model or get_model("translate")
        self.target_language = target_language
        self.source_language = source_language
        self.client = None
        self.translation_logger = TranslationLogger(self.logger)

        self.logger.info(f"Initialized translation: {source_language} → {target_language}")
        self.logger.info(f"Using model: {self.model}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate structured fashion content to target language.

        Processes fashion entities and tags extracted by previous nodes and
        translates them to Persian while maintaining structure, preserving
        technical terms, and ensuring commercial accuracy.

        Args:
            state: Workflow state containing extractable fashion content

        Returns:
            Updated state with translated content

        Raises:
            ModelClientError: If translation model call fails
        """
        # Find translatable fashion content in state
        translatable_data = self._extract_translatable_fashion_content(state)

        if not translatable_data:
            self.logger.warning("No translatable fashion content found in state")
            return state

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)
        target_lang = config.get("target_language", self.target_language)
        source_lang = config.get("source_language", self.source_language)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Translating fashion content from {source_lang} to {target_lang}")
        self.logger.info(f"Found {len(translatable_data)} content sources to translate")

        try:
            translated_results = {}

            # Translate each data source
            for source_key, content in translatable_data.items():
                self.logger.debug(f"Translating fashion content from: {source_key}")

                translated_content = self._translate_fashion_structured_content(
                    content, source_lang, target_lang, model_to_use
                )

                # Store with target language suffix
                result_key = f"{target_lang.lower()}_output"
                translated_results[result_key] = translated_content

            # If multiple sources, merge them intelligently
            if len(translated_results) > 1:
                merged_translation = self._merge_fashion_translations(translated_results, target_lang)
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
                "sources_translated": list(translatable_data.keys()),
                "translation_type": "fashion_specialized",
                "terminology_preserved": True
            }

            # Log translation statistics
            for key, result in translated_results.items():
                entities_count = len(result.get("entities", []))
                self.logger.info(f"Successfully translated to {target_lang}: {entities_count} entities")

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Translation model error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during translation: {str(e)}")
            raise

    def _extract_translatable_fashion_content(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Intelligently select fashion-related data for translation based on
        semantic priority and available sources in workflow state.

        Priority order:
        1. merged_tags - Highest quality merged results
        2. refined_tags - Refined/processed results
        3. conversation_tags - Conversation-enhanced results
        4. extracted_tags - Text-based extraction results
        5. image_tags - Direct image analysis results
        """
        translatable_sources = [
            "refined_tags",  # Second - refined processing results
            "merged_tags",  # Highest priority - final merged results
            "conversation_tags",  # Third - conversation enhanced results
            "extracted_tags",  # Fourth - text extraction results
            "image_tags"  # Fifth - direct image analysis
        ]

        found = {}

        # Collect all available sources that have fashion content
        for key in translatable_sources:
            if key in state and isinstance(state[key], dict):
                content = state[key]
                if self._has_translatable_fashion_fields(content):
                    found[key] = content
                    self.logger.debug(f"Found translatable content in: {key}")

        # Case 1: We found at least one high-priority final source
        high_priority_sources = ["refined_tags", "merged_tags"]
        for key in high_priority_sources:
            if key in found:
                entities_count = len(found[key].get("entities", []))
                self.logger.info(f"Using high-priority source '{key}' with {entities_count} entities for translation")
                return {key: found[key]}

        # Case 2: No final sources, but multiple partial ones → merge them
        if len(found) > 1:
            source_names = list(found.keys())
            total_entities = sum(len(content.get("entities", [])) for content in found.values())

            self.logger.info(f"Merging {len(found)} partial sources ({', '.join(source_names)}) "
                             f"with total {total_entities} entities for translation")

            try:
                merged_temp = self._merge_fashion_translations(
                    {f"{k}_temp": v for k, v in found.items()},
                    target_lang="intermediate"  # Intermediate merge before translation
                )
                return {"merged_partial_sources": merged_temp}

            except Exception as e:
                self.logger.error(f"Failed to merge partial sources: {str(e)}")
                # Fallback to highest priority single source
                fallback_key = next(
                    (key for key in translatable_sources if key in found),
                    next(iter(found))
                )

                self.logger.warning(f"Falling back to single source: {fallback_key}")
                return {fallback_key: found[fallback_key]}

        # Case 3: Only one partial source (e.g., image_tags or extracted_tags)
        if len(found) == 1:
            key, content = next(iter(found.items()))
            entities_count = len(content.get("entities", []))
            self.logger.info(f"Using single available source '{key}' with {entities_count} entities for translation")
            return {key: content}

        # Case 4: Nothing found
        self.logger.warning("No translatable fashion content found in state - available keys: "
                            f"{list(state.keys())}")
        return {}

    def _has_translatable_fashion_fields(self, content: Dict[str, Any]) -> bool:
        """Check if content has fashion fields that can be translated."""
        # Fashion-specific translatable fields
        translatable_fields = [
            "entities", "categories", "summary", "keywords",
            "attributes", "visual_attributes"
        ]

        return any(
            field in content and content[field]
            for field in translatable_fields
        )

    def _translate_fashion_structured_content(self,
                                            content: Dict[str, Any],
                                            source_lang: str,
                                            target_lang: str,
                                            model: str) -> Dict[str, Any]:
        """Translate structured fashion content while preserving format."""

        # Prepare fashion content for translation
        translation_content = self._prepare_fashion_content_for_translation(content)
        content_json = json.dumps(translation_content, indent=2, ensure_ascii=False)

        # استفاده از پرامپت موجود
        messages = [
            {
                "role": "system",
                "content": TranslationPrompts.SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": TranslationPrompts.format_user_message(content_json)
            }
        ]

        # Get raw response with enhanced error handling
        try:
            translated_raw = self.client.call_text(
                model,
                messages,
                max_tokens=3000,  # Increased for complex content
                temperature=0.0   # Lower temperature for consistency
            )

            self.logger.debug(f"Raw model response length: {len(translated_raw)}")

            # Use enhanced sanitizer
            translated_result = sanitize_json_response(translated_raw)

        except Exception as e:
            self.logger.warning(f"⚠️ Initial parsing failed: {e}. Trying repair strategy...")

            # Log detailed failure information
            self.translation_logger.log_parsing_failure(translated_raw, e, model)

            # Repair strategy with focused prompt
            repair_messages = [
                {
                    "role": "system",
                    "content": "You are a JSON formatter. Convert the given text to valid JSON format. Output ONLY the JSON, no explanations."
                },
                {
                    "role": "user",
                    "content": f"Convert this to valid JSON:\n\n{translated_raw}"
                }
            ]

            try:
                repaired_raw = self.client.call_text(model, repair_messages, max_tokens=3000, temperature=0.0)
                translated_result = sanitize_json_response(repaired_raw)
                self.logger.info("✅ Successfully repaired JSON after retry")

            except Exception as repair_error:
                self.logger.error(f"❌ JSON repair failed: {repair_error}")
                # Fallback to predefined strategy
                return self._fallback_translation(content, repair_error)

        # Normalize list responses
        if isinstance(translated_result, list):
            translated_result = {"entities": translated_result}

        # Validate the result
        if not self._validate_translation_result(translated_result, content):
            self.logger.warning("Translation validation failed, using fallback")
            return self._fallback_translation(content, Exception("Validation failed"))

        return self._structure_fashion_translated_result(translated_result, content, target_lang)

    def _prepare_fashion_content_for_translation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare fashion content specifically for translation."""
        translation_content = {}

        # Include translatable fashion fields
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

        return translation_content

    def _structure_fashion_translated_result(self,
                                           translated_data: Dict[str, Any],
                                           original_content: Dict[str, Any],
                                           target_lang: str) -> Dict[str, Any]:
        """Structure the translated fashion result with metadata."""

        # Start with original structure
        result = original_content.copy()

        # Update with translated content, handling fashion-specific structure
        if "entities" in translated_data:
            result["entities"] = self._structure_translated_fashion_entities(translated_data["entities"])

        if "categories" in translated_data:
            result["categories"] = self._structure_translated_fashion_categories(translated_data["categories"])

        if "summary" in translated_data:
            result["summary"] = str(translated_data["summary"])

        if "keywords" in translated_data:
            result["keywords"] = [str(kw) for kw in translated_data["keywords"] if kw]

        # Handle fashion attributes
        for attr_field in ["attributes", "visual_attributes"]:
            if attr_field in translated_data:
                result[attr_field] = self._structure_translated_fashion_attributes(translated_data[attr_field])

        # Add translation metadata
        result["language"] = target_lang.lower()
        result["translation_source"] = original_content.get("extracted_by", "unknown")
        result["translation_type"] = "fashion_specialized"
        result["terminology_preserved"] = True

        return result

    def _structure_translated_fashion_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure translated fashion entities."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict):
                # Handle both old format (name/type/confidence) and new format (name/values)
                if "name" in entity and "values" in entity:
                    # New fashion format with name/values
                    structured_entity = {
                        "name": str(entity["name"]),
                        "values": [str(v) for v in entity["values"] if v] if isinstance(entity["values"], list) else [str(entity["values"])],
                        "entity_type": entity.get("entity_type", "fashion_attribute"),
                        "confidence": entity.get("confidence", 0.85),
                        "source": entity.get("source", "translation"),
                        "language": "persian"
                    }
                elif "name" in entity:
                    # Legacy format adaptation
                    structured_entity = {
                        "name": str(entity["name"]),
                        "type": str(entity.get("type", "unknown")),
                        "confidence": entity.get("confidence", 0.8),
                        "context": str(entity.get("context", "")),
                        "attributes": entity.get("attributes", []),
                        "language": "persian"
                    }
                else:
                    continue

                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_translated_fashion_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure translated fashion categories."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "type": category.get("type", "general"),
                    "level": category.get("level", "main"),
                    "confidence": category.get("confidence", 0.8),
                    "reasoning": str(category.get("reasoning", "")),
                    "language": "persian"
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_translated_fashion_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure translated fashion attributes."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _merge_fashion_translations(self, translations: Dict[str, Dict[str, Any]], target_lang: str) -> Dict[str, Any]:
        """Merge multiple fashion translations into a single result."""
        merged_result = {
            "entities": [],
            "categories": [],
            "keywords": [],
            "summary": "",
            "language": target_lang.lower(),
            "merged_from": list(translations.keys()),
            "translation_type": "fashion_specialized"
        }

        # Merge entities from all sources with fashion-specific deduplication
        seen_entities = set()
        for trans_data in translations.values():
            for entity in trans_data.get("entities", []):
                # Create unique key for fashion entities
                if "values" in entity:
                    entity_key = f"{entity['name']}_{'-'.join(entity.get('values', [])[:2])}"
                else:
                    entity_key = f"{entity['name']}_{entity.get('type', 'unknown')}"

                if entity_key not in seen_entities:
                    merged_result["entities"].append(entity)
                    seen_entities.add(entity_key)

        # Merge categories with fashion hierarchy consideration
        seen_categories = set()
        for trans_data in translations.values():
            for category in trans_data.get("categories", []):
                category_key = f"{category['name']}_{category.get('type', 'general')}"
                if category_key not in seen_categories:
                    merged_result["categories"].append(category)
                    seen_categories.add(category_key)

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

    def _validate_translation_result(self, result: Dict[str, Any], original: Dict[str, Any]) -> bool:
        """Validate translation result maintains structure."""
        try:
            # Check essential fields exist
            required_fields = ["entities", "categories"]
            for field in required_fields:
                if field in original and field not in result:
                    self.logger.warning(f"Missing field after translation: {field}")
                    return False

            # Check entities structure
            if "entities" in result and isinstance(result["entities"], list):
                for entity in result["entities"]:
                    if not isinstance(entity, dict) or "name" not in entity:
                        self.logger.warning("Invalid entity structure in translation")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def _fallback_translation(self, content: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """Fallback when JSON parsing completely fails."""
        self.logger.warning("Using fallback translation strategy")

        # Return original content with Persian language marker
        fallback_result = content.copy()
        fallback_result.update({
            "language": "persian",
            "translation_method": "fallback",
            "translation_error": str(error),
            "original_language": "english"
        })

        return fallback_result
