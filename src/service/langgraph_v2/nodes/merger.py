"""
Merger node for combining multiple tag extraction results.

This node merges tag results from different sources (caption-based,
image-based) and creates a unified output.
"""

from typing import Any, Dict, List
from ..core.base_node import BaseNode


class MergerNode(BaseNode):
    """
    Node that merges multiple tag extraction results into a unified output.

    Input state keys:
        - tags_from_caption: Tags extracted from caption (optional)
        - image_tags: Tags extracted directly from image (optional)
        - parallel_results: List of parallel extraction results (optional)

    Output state keys:
        - merged_tags: Combined and deduplicated tags
        - merge_summary: Summary of merge process
    """

    def __init__(self, name: str = "merger", config: Dict[str, Any] = None):
        """
        Initialize the merger node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.merge_strategy = self.config.get("strategy", "union")  # union, intersection
        self.deduplicate = self.config.get("deduplicate", True)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple tag extraction results.

        Args:
            state: Current workflow state

        Returns:
            Updated state with merged tags
        """
        self.log_execution("Starting tag merge process")

        # Collect all available tag sources
        tag_sources = []
        source_info = []

        # Check for caption-based tags
        if "tags_from_caption" in state and state["tags_from_caption"]:
            tag_sources.append(state["tags_from_caption"])
            source_info.append("caption")

        # Check for image-based tags
        if "image_tags" in state and state["image_tags"]:
            tag_sources.append(state["image_tags"])
            source_info.append("image")

        # Check for parallel results
        if "parallel_results" in state and state["parallel_results"]:
            for i, result in enumerate(state["parallel_results"]):
                if result:
                    tag_sources.append(result)
                    source_info.append(f"parallel_{i}")

        if not tag_sources:
            self.log_execution("No tag sources found for merging", "warning")
            return {
                **state,
                "merged_tags": {"entities": []},
                "merge_summary": {"sources": 0, "total_entities": 0},
                "step_count": state.get("step_count", 0) + 1
            }

        self.log_execution(f"Merging {len(tag_sources)} tag sources: {source_info}")

        try:
            merged_result = self._merge_tag_sources(tag_sources)

            summary = {
                "sources": len(tag_sources),
                "source_types": source_info,
                "total_entities": len(merged_result.get("entities", [])),
                "strategy": self.merge_strategy
            }

            self.log_execution(f"Merge completed: {summary['total_entities']} entities")

            return {
                **state,
                "merged_tags": merged_result,
                "final_merged_tags": merged_result,  # Alias for compatibility
                "merge_summary": summary,
                "step_count": state.get("step_count", 0) + 1
            }

        except Exception as e:
            self.log_execution(f"Error merging tags: {str(e)}", "error")
            return {
                **state,
                "merged_tags": {"entities": []},
                "merge_error": str(e),
                "step_count": state.get("step_count", 0) + 1
            }

    def _merge_tag_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple tag sources using configured strategy.

        Args:
            sources: List of tag dictionaries to merge

        Returns:
            Merged tag dictionary
        """
        if self.merge_strategy == "union":
            return self._union_merge(sources)
        elif self.merge_strategy == "intersection":
            return self._intersection_merge(sources)
        else:
            return self._union_merge(sources)  # Default fallback

    def _union_merge(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Union merge strategy - combine all unique entities."""
        merged_entities = {}

        for source in sources:
            entities = source.get("entities", [])
            for entity in entities:
                name = entity.get("name", "")
                values = entity.get("values", [])

                if name not in merged_entities:
                    merged_entities[name] = set()

                merged_entities[name].update(values)

        # Convert back to list format
        result_entities = [
            {"name": name, "values": list(values)}
            for name, values in merged_entities.items()
        ]

        return {"entities": result_entities}

    def _intersection_merge(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intersection merge strategy - only keep common entities."""
        if not sources:
            return {"entities": []}

        # Start with first source
        common_entities = {}
        first_source = sources[0].get("entities", [])

        for entity in first_source:
            name = entity.get("name", "")
            values = set(entity.get("values", []))
            common_entities[name] = values

        # Intersect with remaining sources
        for source in sources[1:]:
            source_entities = {}
            for entity in source.get("entities", []):
                name = entity.get("name", "")
                values = set(entity.get("values", []))
                source_entities[name] = values

            # Keep only common entity names and intersect values
            new_common = {}
            for name in common_entities:
                if name in source_entities:
                    new_common[name] = common_entities[name].intersection(
                        source_entities[name]
                    )
            common_entities = new_common

        # Convert back to list format
        result_entities = [
            {"name": name, "values": list(values)}
            for name, values in common_entities.items()
            if values  # Only include non-empty intersections
        ]

        return {"entities": result_entities}
