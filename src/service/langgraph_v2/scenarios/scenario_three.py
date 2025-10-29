"""
Scenario Three: Parallel Image Tag Extraction → Merge → Translate

This scenario implements parallel processing where multiple nodes
extract tags from the same image simultaneously, then merges
results and translates to Persian.
"""

from typing import Dict, Any, List
from ..core.graph_builder import GraphBuilder
from ..core.state_manager import StateManager
from ..nodes.image_tag_extractor import ImageTagExtractorNode
from ..nodes.merger import MergerNode
from ..nodes.translator import TranslatorNode


class ParallelImageExtractorNode(ImageTagExtractorNode):
    """
    Specialized image tag extractor for parallel processing.

    This node stores its results in a parallel results array
    to enable proper merging with other parallel nodes.
    """

    def __init__(self, name: str, extractor_id: int, config: Dict[str, Any] = None):
        """
        Initialize parallel image extractor.

        Args:
            name: Node identifier
            extractor_id: Unique ID for this parallel extractor
            config: Optional configuration
        """
        super().__init__(name, config)
        self.extractor_id = extractor_id

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags and store in parallel results array.

        Args:
            state: Current workflow state

        Returns:
            Updated state with parallel results
        """
        # Call parent method to get tags
        result_state = super().run(state)

        # Initialize parallel results if not exists
        if "parallel_results" not in result_state:
            result_state["parallel_results"] = {}

        # Store this extractor's results
        tags = result_state.get("image_tags", {})
        result_state["parallel_results"][f"extractor_{self.extractor_id}"] = tags

        self.log_execution(f"Stored results for parallel extractor {self.extractor_id}")

        return result_state


class ParallelMergerNode(MergerNode):
    """
    Specialized merger for parallel extraction results.
    """

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge parallel extraction results.

        Args:
            state: Current workflow state

        Returns:
            Updated state with merged results
        """
        parallel_results = state.get("parallel_results", {})

        if not parallel_results:
            self.log_execution("No parallel results found to merge", "warning")
            return {
                **state,
                "merged_tags": {"entities": []},
                "step_count": state.get("step_count", 0) + 1
            }

        self.log_execution(f"Merging {len(parallel_results)} parallel results")

        try:
            # Convert parallel results to list format for merging
            tag_sources = list(parallel_results.values())
            merged_result = self._merge_tag_sources(tag_sources)

            summary = {
                "parallel_extractors": len(parallel_results),
                "extractor_ids": list(parallel_results.keys()),
                "total_entities": len(merged_result.get("entities", [])),
                "strategy": self.merge_strategy
            }

            self.log_execution(f"Parallel merge completed: {summary['total_entities']} entities")

            return {
                **state,
                "merged_tags": merged_result,
                "final_merged_tags": merged_result,
                "parallel_merge_summary": summary,
                "step_count": state.get("step_count", 0) + 1
            }

        except Exception as e:
            self.log_execution(f"Error merging parallel results: {str(e)}", "error")
            return {
                **state,
                "merged_tags": {"entities": []},
                "parallel_merge_error": str(e),
                "step_count": state.get("step_count", 0) + 1
            }


class ScenarioThree:
    """
    Implementation of Scenario Three workflow.

    Workflow: Image → [Parallel Extractors] → Merge → Translate
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize scenario three with optional configuration.

        Args:
            config: Configuration including number of parallel extractors
        """
        self.config = config or {}
        self.num_extractors = self.config.get("num_parallel_extractors", 3)
        self.state_manager = StateManager()
        self.graph = None
        self._build_workflow()

    def _build_workflow(self):
        """Build the parallel workflow graph."""
        builder = GraphBuilder("scenario_three")

        # Create parallel extractor nodes
        extractors = []
        for i in range(self.num_extractors):
            extractor = ParallelImageExtractorNode(
                name=f"parallel_extractor_{i}",
                extractor_id=i,
                config=self._get_extractor_config(i)
            )
            extractors.append(extractor)
            builder.add_node(extractor)

        # Create merger and translator
        merger = ParallelMergerNode("parallel_merger", {"strategy": "union"})
        translator = TranslatorNode("translate_merged")

        builder.add_node(merger)
        builder.add_node(translator)

        # Connect parallel extractors to merger
        for extractor in extractors:
            builder.add_sequential_edge(extractor.name, "parallel_merger")

        # Connect merger to translator
        builder.add_sequential_edge("parallel_merger", "translate_merged")

        # Set entry points (all parallel extractors) and finish point
        # Note: LangGraph will start all nodes without incoming edges
        builder.set_finish_point("translate_merged")

        self.graph = builder.build()

    def _get_extractor_config(self, extractor_id: int) -> Dict[str, Any]:
        """
        Get configuration for specific extractor.

        This allows for different prompts or models per extractor
        to increase diversity in parallel processing.
        """
        base_config = self.config.get("extractor_config", {})

        # Optionally vary prompts or other settings per extractor
        if "prompt_variations" in self.config:
            variations = self.config["prompt_variations"]
            if extractor_id < len(variations):
                base_config["prompt"] = variations[extractor_id]

        return base_config

    def execute(self, image_url: str) -> Dict[str, Any]:
        """
        Execute scenario three workflow with parallel processing.

        Args:
            image_url: URL or data URI of image to process

        Returns:
            Final workflow results
        """
        initial_state = self.state_manager.create_initial_state(
            image_url=image_url,
            scenario="scenario_three",
            num_parallel_extractors=self.num_extractors
        )

        final_state = self.graph.invoke(initial_state)

        return {
            "scenario": "scenario_three",
            "execution_summary": self.state_manager.get_execution_summary(),
            "results": {
                "parallel_results": final_state.get("parallel_results", {}),
                "merged_tags": final_state.get("merged_tags", {}),
                "translated_tags": final_state.get("translated_tags", {}),
                "parallel_merge_summary": final_state.get("parallel_merge_summary", {})
            },
            "english_output": final_state.get("merged_tags", {}),
            "persian_output": final_state.get("translated_tags", {}),
            "num_parallel_extractors": self.num_extractors
        }