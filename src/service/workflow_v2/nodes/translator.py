"""
Translation node for multilingual fashion content processing.

Translates extracted fashion tags and content from English to Persian while
preserving structure and maintaining fashion industry terminology accuracy.
"""

from typing import Dict, Any, List

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import TranslationPrompts
from ..config import get_model  # Import centralized model getter




import json
from .utils.json_sanitizer import sanitize_json_response
from .utils.retry_handler import with_retry, RetryError
import re  # for pre-sanitization of pseudo-JSON





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
                ) # First in priority order

                # fallback_key = source_names[0]  # First in priority order
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

        # Convert to JSON string for translation

        content_json = json.dumps(translation_content, indent=2, ensure_ascii=False)

        # Prepare specialized fashion translation request
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

        # Get translation
        # OLD:
        # translated_result = self.client.call_json(
        #     model,
        #     messages,
        #     max_tokens=2500,
        #     temperature=0.1
        # )

        # NEW: get raw text, then sanitize+parse
        translated_raw = self.client.call_text(
            model,
            messages,
            max_tokens=2500,
            temperature=0.1
        )

        try:
            # --- PRE-SANITIZATION: normalize common pseudo-JSON before main sanitizer ---
            # Purpose: Handle ScenarioZero-style outputs like {'entities': ...} or '...'
            # without affecting valid JSON (e.g., {"entities": ...}).
            # --- PRE-SANITIZATION: robust normalization for pseudo/Python-style JSON ---
            # --- PRE-SANITIZATION: robust normalization for pseudo/Python-style JSON ---
            translated_raw = translated_raw.strip()

            # Force extraction even if explanation precedes JSON
            if "{" in translated_raw and "}" in translated_raw:
                start = translated_raw.find("{")
                end = translated_raw.rfind("}")
                translated_raw = translated_raw[start:end + 1].strip()


            # If the model wrapped JSON inside explanations, try to extract only the JSON part
            match_json = re.search(r"(\{[\s\S]+\})", translated_raw)
            if match_json:
                translated_raw = match_json.group(1).strip()

            # Detect JSON-like content that might use single quotes or unquoted keys
            if (
                re.match(r"^\s*\{", translated_raw)
                and not re.match(r"^\s*\{\s*\"", translated_raw)
            ):
                self.logger.debug("Detected single-quoted or unquoted JSON-like structure → enforcing JSON compliance.")

                # Replace single-quoted KEYS → double-quoted
                translated_raw = re.sub(r"([{\[,]\s*)'([^'\"]+?)'\s*:", r'\1"\2":', translated_raw)
                # Replace single-quoted VALUES → double-quoted
                translated_raw = re.sub(r':\s*\'([^\'"]*)\'(\s*[,}\]])', r': "\1"\2', translated_raw)
                # Handle unquoted KEYS → wrap in double quotes
                translated_raw = re.sub(r'([{,]\s*)([A-Za-z0-9_\-]+)\s*:', r'\1"\2":', translated_raw)

            # Strip markdown/code fences or helper prefixes
            translated_raw = re.sub(
                r"^\s*(?:```json|```|Here is.*?:|JSON output:)\s*", "", translated_raw, flags=re.IGNORECASE
            )
            translated_raw = re.sub(r"\s*```$", "", translated_raw)


            translated_result = sanitize_json_response(translated_raw)
        except Exception as e:
            self.logger.warning(f"⚠️ JSON parse failed: {e}. Attempting self-healing retry...")

            # ---- Phase 2: repair prompt ----
            repair_prompt = f"""
        The following text failed JSON parsing. 
        Your task: rewrite it into syntactically valid JSON without changing meanings, 
        preserving field names and structure exactly. 
        Do NOT add explanations or extra text.

        Text to repair:
        {translated_raw}
        """
            try:
                fixed_raw = self.client.call_text(
                    model,
                    [{"role": "user", "content": repair_prompt}],
                    max_tokens=2000,
                    temperature=0.0
                )
                translated_result = sanitize_json_response(fixed_raw)
                self.logger.info("✅ JSON successfully repaired after retry.")
            except Exception as repair_error:
                self.logger.error(f"❌ JSON repair retry failed: {repair_error}")
                raise repair_error

        # If the model returned a top-level list (e.g., entities-only), normalize it.
        if isinstance(translated_result, list):
            # Normalize to an object so downstream code remains stable.
            translated_result = {"entities": translated_result}

        # Structure the translated result
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
