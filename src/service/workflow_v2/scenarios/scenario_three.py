"""
Scenario Three: Parallel Processing Analysis.

Parallel Extractors → Merge → Translate
High-confidence results through parallel processing with multiple extractors.
"""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph

from ..core import StateManager, GraphBuilder, get_workflow_logger
from ..nodes import (
    CaptionGeneratorNode,
    TagExtractorNode,
    ImageTagExtractorNode,
    MergerNode,
    TranslatorNode
)


class ScenarioThree:
    """
    Parallel processing analysis scenario.

    Workflow:
    1. Parallel execution of:
       - CaptionGenerator + TagExtractor
       - ImageTagExtractor (multiple instances with different configs)
    2. Merger: Combine all parallel results
    3. Translator: Translate final merged results
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scenario Three.

        Args:
            config: Optional configuration for the scenario
        """
        self.config = config or {}
        self.logger = get_workflow_logger(f"{__name__}.ScenarioThree")
        self.graph = None

        self.logger.info("Initialized Scenario Three - Parallel Processing Analysis")

    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph for Scenario Three.

        Returns:
            Configured StateGraph for execution
        """
        self.logger.info("Building Scenario Three workflow graph")

        # Initialize graph builder
        builder = GraphBuilder("ScenarioThree_Graph")

        # Get configuration
        node_config = self.config.get("node_config", {})
        num_parallel_extractors = node_config.get("num_parallel_extractors", 2)

        # Add caption generation branch
        builder.add_node("caption_generator", CaptionGeneratorNode(
            model=node_config.get("caption_model", "google/gemini-flash-1.5")
        ))

        builder.add_node("tag_extractor", TagExtractorNode(
            model=node_config.get("tag_model", "google/gemini-flash-1.5")
        ))

        # Add multiple parallel image extractors
        extractor_models = node_config.get("extractor_models", [
            "google/gemini-flash-1.5",
            "google/gemini-pro-1.5"
        ])

        for i in range(num_parallel_extractors):
            model = extractor_models[i % len(extractor_models)]
            node_name = f"image_extractor_{i + 1}"

            builder.add_node(node_name, ImageTagExtractorNode(model=model))

        # Add merger and translator
        builder.add_node("merger", MergerNode(
            confidence_threshold=node_config.get("merge_threshold", 0.4)
        ))

        builder.add_node("translator", TranslatorNode(
            model=node_config.get("translation_model", "google/gemini-flash-1.5"),
            target_language=node_config.get("target_language", "Persian")
        ))

        # Create parallel execution pattern
        # All extractors can run in parallel from the start
        builder.set_entry_point("parallel_dispatcher")

        # Add a parallel dispatcher node
        builder.add_node("parallel_dispatcher", ParallelDispatcherNode(num_parallel_extractors))

        # Connect dispatcher to all parallel branches
        builder.add_edge("parallel_dispatcher", "caption_generator")
        for i in range(num_parallel_extractors):
            builder.add_edge("parallel_dispatcher", f"image_extractor_{i + 1}")

        # Connect caption branch
        builder.add_edge("caption_generator", "tag_extractor")
        builder.add_edge("tag_extractor", "parallel_collector")

        # Connect image extractors to collector
        for i in range(num_parallel_extractors):
            builder.add_edge(f"image_extractor_{i + 1}", "parallel_collector")

        # Add collector node
        builder.add_node("parallel_collector", ParallelCollectorNode(num_parallel_extractors + 1))

        # Connect collector to merger and translator
        builder.add_edge("parallel_collector", "merger")
        builder.add_edge("merger", "translator")

        # Build and store the graph
        self.graph = builder.build()

        self.logger.info("Successfully built Scenario Three workflow graph")
        return self.graph

    def execute(self, image_url: str, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Scenario Three workflow.

        Args:
            image_url: URL or data URI of image to analyze
            initial_state: Optional initial state data

        Returns:
            Complete workflow execution results
        """
        self.logger.info(f"Executing Scenario Three for image: {image_url[:50]}...")

        try:
            # For simplicity, we'll implement a sequential version that simulates parallel processing
            # In a real implementation, you'd use LangGraph's parallel execution capabilities

            results = self._execute_parallel_simulation(image_url, initial_state)

            self.logger.info("Scenario Three execution completed successfully")
            self._log_execution_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Scenario Three: {str(e)}")

            # Return error result
            error_result = {
                "error": str(e),
                "scenario": "scenario_three",
                "image_url": image_url,
                "execution_info": {
                    "scenario": "scenario_three",
                    "success": False,
                    "error": str(e)
                }
            }

            return error_result

    def _execute_parallel_simulation(self, image_url: str, initial_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a simulated parallel workflow."""

        # Initialize state
        state = {
            "image_url": image_url,
            "scenario": "scenario_three",
            "config": self.config
        }

        if initial_state:
            state.update(initial_state)

        node_config = self.config.get("node_config", {})

        # Simulate parallel execution
        self.logger.info("Starting parallel extraction simulation...")

        # Branch 1: Caption + Tag extraction
        caption_generator = CaptionGeneratorNode()
        state = caption_generator.execute(state)

        tag_extractor = TagExtractorNode()
        state = tag_extractor.execute(state)

        # Branch 2: Multiple image extractors
        num_extractors = node_config.get("num_parallel_extractors", 2)
        extractor_models = node_config.get("extractor_models", [
            "google/gemini-flash-1.5",
            "google/gemini-pro-1.5"
        ])

        parallel_results = []

        # Add caption-based result
        if "extracted_tags" in state:
            parallel_results.append(("extracted_tags", state["extracted_tags"]))

        # Run parallel image extractors
        for i in range(num_extractors):
            model = extractor_models[i % len(extractor_models)]
            extractor = ImageTagExtractorNode(model=model)

            # Each extractor works on fresh state with just image_url
            extractor_state = {
                "image_url": image_url,
                "config": self.config
            }

            result_state = extractor.execute(extractor_state)

            if "image_tags" in result_state:
                result_key = f"image_tags_{i + 1}"
                state[result_key] = result_state["image_tags"]
                parallel_results.append((result_key, result_state["image_tags"]))

        # Merge all parallel results
        self.logger.info(f"Merging {len(parallel_results)} parallel extraction results")

        # Temporarily add all parallel results to state for merging
        for result_key, result_data in parallel_results:
            state[result_key] = result_data

        merger = MergerNode()
        state = merger.execute(state)

        # Translate merged results
        translator = TranslatorNode(
            target_language=node_config.get("target_language", "Persian")
        )
        state = translator.execute(state)

        # Add execution metadata
        state["execution_info"] = {
            "scenario": "scenario_three",
            "workflow": "parallel extractors → merge → translate",
            "parallel_extractors_used": num_extractors,
            "extractor_models": extractor_models[:num_extractors],
            "nodes_executed": [
                "caption_generator", "tag_extractor",
                *[f"image_extractor_{i+1}" for i in range(num_extractors)],
                "merger", "translator"
            ],
            "success": True
        }

        return state

    def _log_execution_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""

        exec_info = results.get("execution_info", {})
        num_extractors = exec_info.get("parallel_extractors_used", 0)

        self.logger.info(f"Parallel processing used {num_extractors} extractors")

        # Log merged results
        if "merged_tags" in results:
            merged_data = results["merged_tags"]
            entities_count = len(merged_data.get("entities", []))
            categories_count = len(merged_data.get("categories", []))

            merge_stats = merged_data.get("merge_statistics", {})
            dedup_ratio = merge_stats.get("deduplication_ratio", 0.0)

            self.logger.info(f"Merged results: {entities_count} entities, {categories_count} categories")
            self.logger.info(f"Deduplication ratio: {dedup_ratio:.2%}")

        # Log translation results
        if "persian_output" in results:
            persian_data = results["persian_output"]
            persian_entities = len(persian_data.get("entities", []))

            self.logger.info(f"Persian translation: {persian_entities} entities")

    def get_scenario_info(self) -> Dict[str, Any]:
        """
        Get information about this scenario.

        Returns:
            Scenario description and capabilities
        """
        return {
            "name": "Scenario Three",
            "description": "High-confidence results through parallel processing",
            "workflow": [
                "Parallel Caption Generation + Tag Extraction",
                "Multiple Parallel Image Tag Extractors",
                "Intelligent Merging with Deduplication",
                "Translation to Target Language"
            ],
            "strengths": [
                "Highest confidence through consensus",
                "Robust against individual model failures",
                "Comprehensive coverage",
                "Advanced deduplication"
            ],
            "use_cases": [
                "Critical accuracy requirements",
                "Complex image analysis",
                "Quality validation",
                "Research and development"
            ],
            "estimated_time": "45-90 seconds",
            "model_calls": "5-8 (configurable)"
        }


class ParallelDispatcherNode:
    """Helper node to dispatch parallel execution."""

    def __init__(self, num_parallel: int):
        self.num_parallel = num_parallel
        self.logger = get_workflow_logger(f"{__name__}.ParallelDispatcher")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch state to parallel branches."""
        self.logger.info(f"Dispatching to {self.num_parallel} parallel branches")
        return state


class ParallelCollectorNode:
    """Helper node to collect parallel results."""

    def __init__(self, expected_results: int):
        self.expected_results = expected_results
        self.logger = get_workflow_logger(f"{__name__}.ParallelCollector")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect results from parallel branches."""
        self.logger.info(f"Collecting results from {self.expected_results} parallel branches")
        return state
