"""
Scenario One: Caption → Tags → Image Tags → Merge → Translate

This scenario implements a comprehensive workflow that:
1. Generates caption from image
2. Extracts tags from the caption
3. Extracts tags directly from image
4. Merges both tag sources
5. Translates final result to Persian
"""

from typing import Dict, Any
from ..core.graph_builder import GraphBuilder
from ..core.state_manager import StateManager
from ..nodes.caption_generator import CaptionGeneratorNode
from ..nodes.tag_extractor import TagExtractorNode
from ..nodes.image_tag_extractor import ImageTagExtractorNode
from ..nodes.merger import MergerNode
from ..nodes.translator import TranslatorNode


class ScenarioOne:
    """
    Implementation of Scenario One workflow.

    Workflow: Image → Caption → Caption Tags + Direct Image Tags → Merge → Translate
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize scenario one with optional configuration."""
        self.config = config or {}
        self.state_manager = StateManager()
        self.graph = None
        self._build_workflow()

    def _build_workflow(self):
        """Build the workflow graph for scenario one."""
        builder = GraphBuilder("scenario_one")

        # Create nodes
        caption_gen = CaptionGeneratorNode("generate_caption")
        tag_extractor = TagExtractorNode("extract_caption_tags")
        image_extractor = ImageTagExtractorNode("extract_image_tags")
        merger = MergerNode("merge_tags", {"strategy": "union"})
        translator = TranslatorNode("translate_final")

        # Add nodes to graph
        builder.add_node(caption_gen)
        builder.add_node(tag_extractor)
        builder.add_node(image_extractor)
        builder.add_node(merger)
        builder.add_node(translator)

        # Define workflow edges
        builder.add_sequential_edge("generate_caption", "extract_caption_tags")
        builder.add_sequential_edge("generate_caption", "extract_image_tags")
        builder.add_sequential_edge("extract_caption_tags", "merge_tags")
        builder.add_sequential_edge("extract_image_tags", "merge_tags")
        builder.add_sequential_edge("merge_tags", "translate_final")

        # Set entry and finish points
        builder.set_entry_point("generate_caption")
        builder.set_finish_point("translate_final")

        self.graph = builder.build()

    def execute(self, image_url: str) -> Dict[str, Any]:
        """
        Execute scenario one workflow.

        Args:
            image_url: URL or data URI of image to process

        Returns:
            Final workflow results
        """
        initial_state = self.state_manager.create_initial_state(
            image_url=image_url,
            scenario="scenario_one"
        )

        final_state = self.graph.invoke(initial_state)

        return {
            "scenario": "scenario_one",
            "execution_summary": self.state_manager.get_execution_summary(),
            "results": {
                "caption": final_state.get("caption", ""),
                "caption_tags": final_state.get("tags_from_caption", {}),
                "image_tags": final_state.get("image_tags", {}),
                "merged_tags": final_state.get("merged_tags", {}),
                "translated_tags": final_state.get("translated_tags", {}),
                "merge_summary": final_state.get("merge_summary", {})
            },
            "english_output": final_state.get("merged_tags", {}),
            "persian_output": final_state.get("translated_tags", {})
        }
