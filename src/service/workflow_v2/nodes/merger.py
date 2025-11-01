"""
AI-powered intelligent merger node for fashion analysis results.

Uses advanced language models to intelligently merge multiple extraction
results from different analysis methods, resolving conflicts and creating
comprehensive unified fashion product profiles.
"""

from typing import Dict, Any, List, Set

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import MergerPrompts
from ..config import get_model


class MergerNode(BaseNode):
    """
    AI-powered node that intelligently merges multiple fashion extraction results.

    Uses advanced language models with fashion domain expertise to combine
    results from different extraction methods (caption-based, image-based, etc.)
    while resolving conflicts and maintaining commercial accuracy.
    """

    def __init__(self, model: str = None, confidence_threshold: float = 0.5):
        """
        Initialize the AI-powered merger node.

        Args:
            model: Language model for intelligent merging. If None, uses MERGER_MODEL from env
            confidence_threshold: Minimum confidence score for including results
        """
        super().__init__("Merger")
        self.model = model or get_model("merger")
        self.confidence_threshold = confidence_threshold
        self.client = None

        self.logger.info(f"Initialized AI-powered merger with model: {self.model}")
        self.logger.info(f"Confidence threshold: {confidence_threshold}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge multiple fashion extraction results using AI.

        Uses advanced language models to analyze multiple extraction sources,
        resolve conflicts using fashion expertise, and create comprehensive
        unified product profiles with enhanced accuracy and completeness.

        Args:
            state: Workflow state containing multiple extraction results

        Returns:
            Updated state with AI-merged results

        Raises:
            ModelClientError: If merger model call fails
        """
        # Find all extraction results to merge
        extraction_sources = self._find_extraction_sources(state)

        if len(extraction_sources) < 2:
            self.logger.warning(f"Found only {len(extraction_sources)} sources to merge")
            if len(extraction_sources) == 1:
                # Pass through single source with AI enhancement
                source_name, source_data = next(iter(extraction_sources.items()))
                enhanced_result = self._enhance_single_source(source_data, source_name)

            else:
                # No sources found
                enhanced_result = self._create_empty_result()
        else:
            # Perform AI-powered intelligent merging
            self.logger.info(f"AI-merging results from {len(extraction_sources)} sources: {list(extraction_sources.keys())}")
            enhanced_result = self._ai_merge_extraction_results(extraction_sources)

        # Update state
        updated_state = state.copy()
        updated_state["merged_tags"] = enhanced_result

        # Log merge statistics
        self._log_ai_merge_statistics(enhanced_result, extraction_sources)

        return updated_state

    def _find_extraction_sources(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Find all extraction results available for merging."""
        possible_sources = [
            "extracted_tags",      # From TagExtractorNode
            "image_tags",          # From ImageTagExtractorNode
            "refined_tags",        # From RefinerNode
            "conversation_tags"    # From ConversationRefinerNode
        ]

        found_sources = {}

        for source_name in possible_sources:
            if source_name in state and isinstance(state[source_name], dict):
                source_data = state[source_name]

                # Validate that it has mergeable content
                if self._is_mergeable_content(source_data):
                    found_sources[source_name] = source_data
                    self.logger.debug(f"Found mergeable source: {source_name}")

        return found_sources

    def _is_mergeable_content(self, content: Dict[str, Any]) -> bool:
        """Check if content has fields that can be merged."""
        required_fields = ["entities"]  # Minimum requirement
        optional_fields = ["categories", "attributes", "visual_attributes"]

        has_entities = "entities" in content and content["entities"]
        has_optional = any(field in content and content[field] for field in optional_fields)

        return has_entities or has_optional

    def _ai_merge_extraction_results(self, sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Use AI to intelligently merge multiple extraction results."""

        # Get configuration
        config = self.get_node_config({})  # No state needed here
        model_to_use = config.get("model", self.model)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Starting AI-powered intelligent merging using {model_to_use}")

        try:
            # Prepare sources for AI analysis
            prepared_sources = self._prepare_sources_for_ai(sources)

            # Create AI merger request
            messages = [
                {
                    "role": "system",
                    "content": MergerPrompts.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": MergerPrompts.format_user_message(prepared_sources)
                }
            ]

            # Get AI merger result
            ai_merged_result = self.client.call_json(
                model_to_use,
                messages,
                max_tokens=3500,  # Increased for comprehensive merging
                temperature=0.1   # Very low for consistent logical merging
            )

            # Structure the AI-merged result
            structured_result = self._structure_ai_merged_result(ai_merged_result, sources, model_to_use)

            return structured_result

        except ModelClientError as e:
            self.logger.error(f"AI merger model error: {str(e)}")
            # Fallback to simple merging
            self.logger.warning("Falling back to simple merge due to AI error")
            return self._fallback_simple_merge(sources)
        except Exception as e:
            self.logger.error(f"Unexpected error during AI merging: {str(e)}")
            return self._fallback_simple_merge(sources)

    def _prepare_sources_for_ai(self, sources: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Prepare sources for AI analysis by cleaning and formatting."""
        prepared = {}

        for source_name, source_data in sources.items():
            # Clean and prepare each source
            cleaned_source = {
                "entities": source_data.get("entities", []),
                "categories": source_data.get("categories", []),
                "attributes": source_data.get("attributes", {}),
                "visual_attributes": source_data.get("visual_attributes", {}),
                "summary": source_data.get("summary", ""),
                "source_metadata": {
                    "extraction_method": source_data.get("extraction_type", "unknown"),
                    "model_used": source_data.get("model_used", "unknown"),
                    "confidence_level": self._calculate_source_confidence(source_data)
                }
            }

            prepared[source_name] = cleaned_source

        return prepared

    def _calculate_source_confidence(self, source_data: Dict[str, Any]) -> float:
        """Calculate overall confidence level for a source."""
        entities = source_data.get("entities", [])
        if not entities:
            return 0.5

        # Calculate average confidence
        confidences = []
        for entity in entities:
            if isinstance(entity, dict):
                confidences.append(entity.get("confidence", 0.8))

        return sum(confidences) / len(confidences) if confidences else 0.8

    def _structure_ai_merged_result(self, ai_result: Dict[str, Any], original_sources: Dict[str, Dict[str, Any]], model_used: str) -> Dict[str, Any]:
        """Structure the AI-merged result with comprehensive metadata."""

        structured_result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "visual_attributes": {},
            "merge_summary": "",
            "merge_statistics": {},
            "quality_assessment": "",
            "model_used": model_used,
            "merged_by": self.node_name,
            "merge_method": "ai_powered_intelligent",
            "sources_merged": list(original_sources.keys()),
            "merge_confidence": 0.9  # High confidence for AI merging
        }

        # Structure AI-merged entities
        if "entities" in ai_result and isinstance(ai_result["entities"], list):
            structured_result["entities"] = self._structure_ai_merged_entities(ai_result["entities"])

        # Structure AI-merged categories
        if "categories" in ai_result and isinstance(ai_result["categories"], list):
            structured_result["categories"] = self._structure_ai_merged_categories(ai_result["categories"])

        # Structure merged attributes
        for attr_field in ["attributes", "visual_attributes"]:
            if attr_field in ai_result and isinstance(ai_result[attr_field], dict):
                structured_result[attr_field] = self._structure_ai_merged_attributes(ai_result[attr_field])

        # Extract AI analysis results
        structured_result["merge_summary"] = str(ai_result.get("merge_summary", ""))
        structured_result["merge_statistics"] = ai_result.get("merge_statistics", {})
        structured_result["quality_assessment"] = str(ai_result.get("quality_assessment", ""))

        return structured_result

    def _structure_ai_merged_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure AI-merged entities with intelligence metadata."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                structured_entity = {
                    "name": str(entity["name"]),
                    "values": entity.get("values", []) if isinstance(entity.get("values"), list) else [str(entity.get("values", ""))],
                    "confidence": float(entity.get("confidence", 0.9)),
                    "sources": entity.get("sources", []),
                    "merge_reasoning": str(entity.get("merge_reasoning", "")),
                    "entity_type": "ai_merged_fashion_attribute",
                    "merge_method": "intelligent_ai_analysis"
                }
                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_ai_merged_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure AI-merged categories."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "type": category.get("type", "general"),
                    "level": str(category.get("level", "main")),
                    "confidence": float(category.get("confidence", 0.9)),
                    "sources": category.get("sources", []),
                    "merge_reasoning": str(category.get("merge_reasoning", "")),
                    "ai_verified": True
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_ai_merged_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure AI-merged attributes."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _enhance_single_source(self, source_data: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Enhance a single source when no merging is needed."""
        enhanced_result = source_data.copy()
        enhanced_result.update({
            "merged_from": [source_name],
            "merged_by": self.node_name,
            "merge_method": "single_source_enhancement",
            "merge_confidence": 0.8
        })

        return enhanced_result

    def _fallback_simple_merge(self, sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback simple merge when AI fails."""
        self.logger.info("Performing fallback simple merge")

        merged_result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "visual_attributes": {},
            "merged_from": list(sources.keys()),
            "merged_by": self.node_name,
            "merge_method": "fallback_simple",
            "merge_confidence": 0.6
        }

        # Simple entity collection (no intelligence)
        all_entities = []
        for source_data in sources.values():
            all_entities.extend(source_data.get("entities", []))

        merged_result["entities"] = all_entities[:20]  # Limit to prevent bloat

        return merged_result

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty merge result when no sources available."""
        return {
            "entities": [],
            "categories": [],
            "attributes": {},
            "visual_attributes": {},
            "merged_from": [],
            "merged_by": self.node_name,
            "merge_method": "no_sources_available",
            "merge_confidence": 0.0
        }

    def _log_ai_merge_statistics(self, merged_result: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> None:
        """Log statistics about the AI merge operation."""
        merge_stats = merged_result.get("merge_statistics", {})

        self.logger.info("AI-powered merge operation completed:")
        self.logger.info(f"  Sources processed: {len(sources)}")
        self.logger.info(f"  Final entities: {len(merged_result.get('entities', []))}")
        self.logger.info(f"  Final categories: {len(merged_result.get('categories', []))}")
        self.logger.info(f"  Merge method: {merged_result.get('merge_method', 'unknown')}")
        self.logger.info(f"  Merge confidence: {merged_result.get('merge_confidence', 0.0):.2f}")

        # Log AI-specific statistics
        if "conflicts_resolved" in merge_stats:
            self.logger.info(f"  AI conflicts resolved: {merge_stats['conflicts_resolved']}")

        if "completeness_score" in merge_stats:
            self.logger.info(f"  Completeness score: {merge_stats['completeness_score']:.2f}")

        # Log quality assessment
        quality_assessment = merged_result.get("quality_assessment", "")
        if quality_assessment:
            self.logger.info(f"  Quality assessment: {quality_assessment[:100]}...")
