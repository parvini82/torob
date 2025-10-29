"""
Scenario Two: Caption → Tags → Translate

Simple workflow that generates caption, extracts tags, and translates.
"""

from typing import Dict, Any
from ..core.graph_builder import GraphBuilder
from ..core.state_manager import StateManager
from ..nodes.caption_generator import CaptionGeneratorNode
from ..nodes.tag_extractor import TagExtractorNode
from ..nodes.translator import TranslatorNode


class ScenarioTwo:
    """Implementation of Scenario Two workflow."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize scenario two."""
        self.config = config or {}
        self.state_manager = StateManager()
        self.graph = None
        self._build_workflow()

    def _build_workflow(self):
        """Build the workflow graph."""
        builder = GraphBuilder("scenario_two")

        # Create nodes
        caption_gen = CaptionGeneratorNode("generate_caption")
        tag_extractor = TagExtractorNode("extract_tags")
        translator = TranslatorNode("translate_tags")

        # Add nodes and edges
        builder.add_node(caption_gen)
        builder.add_node(tag_extractor)
        builder.add_node(translator)

        builder.add_sequential_edge("generate_caption", "extract_tags")
        builder.add_sequential_edge("extract_tags", "translate_tags")

        builder.set_entry_point("generate_caption")
        builder.set_finish_point("translate_tags")

        self.graph = builder.build()

    def execute(self, image_url: str) -> Dict[str, Any]:
        """Execute scenario two workflow."""
        initial_state = self.state_manager.create_initial_state(
            image_url=image_url,
            scenario="scenario_two"
        )

        final_state = self.graph.invoke(initial_state)

        return {
            "scenario": "scenario_two",
            "results": {
                "caption": final_state.get("caption", ""),
                "tags": final_state.get("tags_from_caption", {}),
                "translated_tags": final_state.get("translated_tags", {})
            },
            "english_output": final_state.get("tags_from_caption", {}),
            "persian_output": final_state.get("translated_tags", {})
        }
