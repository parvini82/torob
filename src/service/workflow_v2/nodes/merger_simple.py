# """
# Merger node for combining multiple extraction results.
#
# Intelligently merges results from different extraction nodes while
# removing duplicates and maintaining quality scores.
# """
#
# from typing import Dict, Any, List, Set
# from ..core.base_node import BaseNode
#
#
# class MergerNode(BaseNode):
#     """
#     Node that merges multiple extraction results into a unified output.
#
#     Combines results from different extraction nodes (caption-based, image-based)
#     while handling duplicates and maintaining quality metrics.
#     """
#
#     def __init__(self, confidence_threshold: float = 0.5):
#         """
#         Initialize the merger node.
#
#         Args:
#             confidence_threshold: Minimum confidence score to include entities
#         """
#         super().__init__("Merger")
#         self.confidence_threshold = confidence_threshold
#
#     def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Merge multiple extraction results in the state.
#
#         Args:
#             state: Workflow state containing multiple extraction results
#
#         Returns:
#             Updated state with merged results
#         """
#         # Find all extraction results to merge
#         extraction_sources = self._find_extraction_sources(state)
#
#         if len(extraction_sources) < 2:
#             self.logger.warning(f"Found only {len(extraction_sources)} sources to merge")
#             if len(extraction_sources) == 1:
#                 # Just pass through the single source
#                 source_name, source_data = next(iter(extraction_sources.items()))
#                 merged_result = source_data.copy()
#                 merged_result["merged_from"] = [source_name]
#                 merged_result["merged_by"] = self.node_name
#             else:
#                 # No sources found
#                 merged_result = self._create_empty_result()
#         else:
#             # Perform the merge
#             self.logger.info(f"Merging results from {len(extraction_sources)} sources: {list(extraction_sources.keys())}")
#             merged_result = self._merge_extraction_results(extraction_sources)
#
#         # Update state
#         updated_state = state.copy()
#         updated_state["merged_tags"] = merged_result
#
#         # Log merge statistics
#         self._log_merge_statistics(merged_result, extraction_sources)
#
#         return updated_state
#
#     def _find_extraction_sources(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
#         """Find all extraction results that can be merged."""
#         possible_sources = [
#             "extracted_tags",      # From TagExtractorNode
#             "image_tags",          # From ImageTagExtractorNode
#             "refined_tags",        # From RefinerNode
#             "conversation_tags"    # From ConversationRefinerNode
#         ]
#
#         found_sources = {}
#
#         for source_name in possible_sources:
#             if source_name in state and isinstance(state[source_name], dict):
#                 source_data = state[source_name]
#
#                 # Validate that it has mergeable content
#                 if self._is_mergeable_content(source_data):
#                     found_sources[source_name] = source_data
#                     self.logger.debug(f"Found mergeable source: {source_name}")
#
#         return found_sources
#
#     def _is_mergeable_content(self, content: Dict[str, Any]) -> bool:
#         """Check if content has fields that can be merged."""
#         required_fields = ["entities", "categories"]
#         return any(field in content and content[field] for field in required_fields)
#
#     def _merge_extraction_results(self, sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
#         """Merge multiple extraction results intelligently."""
#         merged_result = {
#             "entities": [],
#             "categories": [],
#             "keywords": [],
#             "attributes": {},
#             "visual_attributes": {},
#             "summary": "",
#             "merged_from": list(sources.keys()),
#             "merged_by": self.node_name,
#             "merge_statistics": {}
#         }
#
#         # Merge entities with deduplication
#         merged_result["entities"] = self._merge_entities(sources)
#
#         # Merge categories with deduplication
#         merged_result["categories"] = self._merge_categories(sources)
#
#         # Merge keywords
#         merged_result["keywords"] = self._merge_keywords(sources)
#
#         # Merge attributes
#         merged_result["attributes"] = self._merge_attributes(sources, "attributes")
#         merged_result["visual_attributes"] = self._merge_attributes(sources, "visual_attributes")
#
#         # Create comprehensive summary
#         merged_result["summary"] = self._merge_summaries(sources)
#
#         # Add merge statistics
#         merged_result["merge_statistics"] = self._calculate_merge_statistics(sources, merged_result)
#
#         return merged_result
#
#     def _merge_entities(self, sources: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Merge entities from multiple sources with deduplication."""
#         entity_groups = {}  # Group similar entities
#
#         for source_name, source_data in sources.items():
#             entities = source_data.get("entities", [])
#
#             for entity in entities:
#                 if not isinstance(entity, dict) or "name" not in entity:
#                     continue
#
#                 # Skip low-confidence entities
#                 confidence = entity.get("confidence", 0.8)
#                 if confidence < self.confidence_threshold:
#                     continue
#
#                 # Create entity key for grouping
#                 entity_key = self._create_entity_key(entity)
#
#                 if entity_key not in entity_groups:
#                     entity_groups[entity_key] = {
#                         "entities": [],
#                         "sources": []
#                     }
#
#                 entity_groups[entity_key]["entities"].append(entity)
#                 entity_groups[entity_key]["sources"].append(source_name)
#
#         # Create merged entities from groups
#         merged_entities = []
#
#         for entity_key, group_data in entity_groups.items():
#             merged_entity = self._merge_entity_group(group_data["entities"], group_data["sources"])
#             merged_entities.append(merged_entity)
#
#         # Sort by confidence
#         merged_entities.sort(key=lambda x: x.get("confidence", 0), reverse=True)
#
#         return merged_entities
#
#     def _create_entity_key(self, entity: Dict[str, Any]) -> str:
#         """Create a key for entity grouping (handles similar entities)."""
#         name = entity["name"].lower().strip()
#         entity_type = entity.get("type", "unknown").lower()
#
#         # Simple similarity - could be enhanced with fuzzy matching
#         return f"{name}_{entity_type}"
#
#     def _merge_entity_group(self, entities: List[Dict[str, Any]], sources: List[str]) -> Dict[str, Any]:
#         """Merge a group of similar entities into one."""
#         # Use the entity with highest confidence as base
#         base_entity = max(entities, key=lambda x: x.get("confidence", 0))
#
#         merged_entity = {
#             "name": base_entity["name"],
#             "type": base_entity.get("type", "unknown"),
#             "confidence": self._calculate_merged_confidence(entities),
#             "context": self._merge_entity_contexts(entities),
#             "attributes": self._merge_entity_attributes(entities),
#             "sources": sources,
#             "source_count": len(set(sources))
#         }
#
#         return merged_entity
#
#     def _calculate_merged_confidence(self, entities: List[Dict[str, Any]]) -> float:
#         """Calculate confidence for merged entity."""
#         confidences = [entity.get("confidence", 0.8) for entity in entities]
#
#         # Weighted average with boost for multiple sources
#         avg_confidence = sum(confidences) / len(confidences)
#         source_boost = min(0.1 * (len(entities) - 1), 0.2)  # Up to 0.2 boost
#
#         return min(avg_confidence + source_boost, 1.0)
#
#     def _merge_entity_contexts(self, entities: List[Dict[str, Any]]) -> str:
#         """Merge context information from multiple entities."""
#         contexts = [entity.get("context", "") for entity in entities if entity.get("context")]
#
#         # Remove duplicates and combine
#         unique_contexts = []
#         seen = set()
#
#         for context in contexts:
#             context_lower = context.lower().strip()
#             if context_lower and context_lower not in seen:
#                 unique_contexts.append(context)
#                 seen.add(context_lower)
#
#         return ". ".join(unique_contexts)
#
#     def _merge_entity_attributes(self, entities: List[Dict[str, Any]]) -> List[str]:
#         """Merge attributes from multiple entities."""
#         all_attributes = set()
#
#         for entity in entities:
#             attributes = entity.get("attributes", [])
#             if isinstance(attributes, list):
#                 all_attributes.update(attributes)
#
#         return list(all_attributes)
#
#     def _merge_categories(self, sources: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Merge categories from multiple sources."""
#         category_groups = {}
#
#         for source_name, source_data in sources.items():
#             categories = source_data.get("categories", [])
#
#             for category in categories:
#                 if not isinstance(category, dict) or "name" not in category:
#                     continue
#
#                 category_name = category["name"].lower().strip()
#
#                 if category_name not in category_groups:
#                     category_groups[category_name] = {
#                         "categories": [],
#                         "sources": []
#                     }
#
#                 category_groups[category_name]["categories"].append(category)
#                 category_groups[category_name]["sources"].append(source_name)
#
#         # Merge category groups
#         merged_categories = []
#
#         for category_name, group_data in category_groups.items():
#             merged_category = self._merge_category_group(group_data["categories"], group_data["sources"])
#             merged_categories.append(merged_category)
#
#         # Sort by confidence
#         merged_categories.sort(key=lambda x: x.get("confidence", 0), reverse=True)
#
#         return merged_categories
#
#     def _merge_category_group(self, categories: List[Dict[str, Any]], sources: List[str]) -> Dict[str, Any]:
#         """Merge a group of similar categories."""
#         base_category = max(categories, key=lambda x: x.get("confidence", 0))
#
#         merged_category = {
#             "name": base_category["name"],
#             "level": base_category.get("level", "main"),
#             "confidence": self._calculate_merged_confidence(categories),
#             "reasoning": self._merge_category_reasoning(categories),
#             "sources": sources,
#             "source_count": len(set(sources))
#         }
#
#         return merged_category
#
#     def _merge_category_reasoning(self, categories: List[Dict[str, Any]]) -> str:
#         """Merge reasoning from multiple categories."""
#         reasonings = [cat.get("reasoning", "") for cat in categories if cat.get("reasoning")]
#
#         # Take the most detailed reasoning
#         return max(reasonings, key=len) if reasonings else ""
#
#     def _merge_keywords(self, sources: Dict[str, Dict[str, Any]]) -> List[str]:
#         """Merge keywords from all sources."""
#         all_keywords = set()
#
#         for source_data in sources.values():
#             keywords = source_data.get("keywords", [])
#             if isinstance(keywords, list):
#                 all_keywords.update(kw.lower().strip() for kw in keywords if kw)
#
#         return sorted(list(all_keywords))
#
#     def _merge_attributes(self, sources: Dict[str, Dict[str, Any]], attr_field: str) -> Dict[str, List[str]]:
#         """Merge attributes from all sources."""
#         merged_attrs = {}
#
#         for source_data in sources.values():
#             attributes = source_data.get(attr_field, {})
#             if isinstance(attributes, dict):
#                 for attr_key, attr_values in attributes.items():
#                     if attr_key not in merged_attrs:
#                         merged_attrs[attr_key] = set()
#
#                     if isinstance(attr_values, list):
#                         merged_attrs[attr_key].update(v.lower().strip() for v in attr_values if v)
#                     elif attr_values:
#                         merged_attrs[attr_key].add(str(attr_values).lower().strip())
#
#         # Convert sets back to sorted lists
#         return {key: sorted(list(values)) for key, values in merged_attrs.items()}
#
#     def _merge_summaries(self, sources: Dict[str, Dict[str, Any]]) -> str:
#         """Create a comprehensive summary from all sources."""
#         summaries = []
#
#         for source_name, source_data in sources.items():
#             summary = source_data.get("summary", "")
#             if summary and summary.strip():
#                 summaries.append(f"[{source_name}] {summary.strip()}")
#
#         return " | ".join(summaries)
#
#     def _calculate_merge_statistics(self, sources: Dict[str, Dict[str, Any]], merged_result: Dict[str, Any]) -> Dict[str, Any]:
#         """Calculate statistics about the merge operation."""
#         stats = {
#             "sources_merged": len(sources),
#             "total_entities_input": 0,
#             "total_categories_input": 0,
#             "entities_output": len(merged_result.get("entities", [])),
#             "categories_output": len(merged_result.get("categories", [])),
#             "deduplication_ratio": 0.0
#         }
#
#         # Count input items
#         for source_data in sources.values():
#             stats["total_entities_input"] += len(source_data.get("entities", []))
#             stats["total_categories_input"] += len(source_data.get("categories", []))
#
#         # Calculate deduplication effectiveness
#         total_input = stats["total_entities_input"] + stats["total_categories_input"]
#         total_output = stats["entities_output"] + stats["categories_output"]
#
#         if total_input > 0:
#             stats["deduplication_ratio"] = 1.0 - (total_output / total_input)
#
#         return stats
#
#     def _create_empty_result(self) -> Dict[str, Any]:
#         """Create an empty merge result."""
#         return {
#             "entities": [],
#             "categories": [],
#             "keywords": [],
#             "attributes": {},
#             "visual_attributes": {},
#             "summary": "",
#             "merged_from": [],
#             "merged_by": self.node_name,
#             "merge_statistics": {
#                 "sources_merged": 0,
#                 "total_entities_input": 0,
#                 "total_categories_input": 0,
#                 "entities_output": 0,
#                 "categories_output": 0,
#                 "deduplication_ratio": 0.0
#             }
#         }
#
#     def _log_merge_statistics(self, merged_result: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> None:
#         """Log statistics about the merge operation."""
#         stats = merged_result.get("merge_statistics", {})
#
#         self.logger.info("Merge operation completed:")
#         self.logger.info(f"  Sources merged: {stats.get('sources_merged', 0)}")
#         self.logger.info(f"  Entities: {stats.get('total_entities_input', 0)} → {stats.get('entities_output', 0)}")
#         self.logger.info(f"  Categories: {stats.get('total_categories_input', 0)} → {stats.get('categories_output', 0)}")
#         self.logger.info(f"  Deduplication ratio: {stats.get('deduplication_ratio', 0.0):.2%}")
