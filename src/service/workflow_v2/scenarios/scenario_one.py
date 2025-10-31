"""
Scenario One: Comprehensive Sequential Analysis.

Caption → Tags → Image Tags → Merge → Translate
Complete workflow with both caption-based and direct image analysis.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from ..core import StateManager, GraphBuilder
from ..core.logger import get_workflow_logger

from ..nodes import (
    CaptionGeneratorNode,
    TagExtractorNode,
    ImageTagExtractorNode,
    MergerNode,
    TranslatorNode
)


class ScenarioOne:
    """
    Comprehensive sequential analysis scenario.

    Workflow:
    1. CaptionGenerator: Generate descriptive caption from image
    2. TagExtractor: Extract structured tags from caption
    3. ImageTagExtractor: Direct image analysis for tags
    4. Merger: Combine caption-based and image-based results
    5. Translator: Translate final results to target language
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scenario One.

        Args:
            config: Optional configuration for the scenario
        """
        self.config = config or {}
        self.logger = get_workflow_logger(f"{__name__}.ScenarioOne")
        self.graph = None

        self.logger.info("Initialized Scenario One - Comprehensive Sequential Analysis")

    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph for Scenario One.

        Returns:
            Configured StateGraph for execution
        """
        self.logger.info("Building Scenario One workflow graph")

        # Initialize graph builder
        builder = GraphBuilder("ScenarioOne_Graph")

        # Add nodes with configuration
        node_config = self.config.get("node_config", {})

        builder.add_node("caption_generator", CaptionGeneratorNode(
            model=node_config.get("caption_model", "qwen/qwen2.5-vl-32b-instruct:free")
        ))

        builder.add_node("tag_extractor", TagExtractorNode(
            model=node_config.get("tag_model", "qwen/qwen2.5-vl-32b-instruct:free")
        ))

        builder.add_node("image_tag_extractor", ImageTagExtractorNode(
            model=node_config.get("image_model", "qwen/qwen2.5-vl-32b-instruct:free")
        ))

        builder.add_node("merger", MergerNode(
            confidence_threshold=node_config.get("merge_threshold", 0.5)
        ))

        builder.add_node("translator", TranslatorNode(
            model=node_config.get("translation_model", "qwen/qwen2.5-vl-32b-instruct:free"),
            target_language=node_config.get("target_language", "Persian")
        ))

        # Add edges to create the workflow
        builder.add_edge("caption_generator", "tag_extractor")
        builder.add_edge("tag_extractor", "image_tag_extractor")
        builder.add_edge("image_tag_extractor", "merger")
        builder.add_edge("merger", "translator")

        # Set entry point
        builder.set_entry_point("caption_generator")

        # Build and store the graph
        self.graph = builder.build()

        self.logger.info("Successfully built Scenario One workflow graph")
        return self.graph

    def execute(self, image_url: str, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Scenario One workflow.

        Args:
            image_url: URL or data URI of image to analyze
            initial_state: Optional initial state data

        Returns:
            Complete workflow execution results
        """
        self.logger.info(f"Executing Scenario One for image: {image_url[:50]}...")

        try:
            # Build graph if not already built
            if not self.graph:
                self.build_graph()

            init_state = {
                "image_url": image_url,
                "scenario": "scenario_one",
                "config": self.config
            }

            # Add any provided initial state
            if initial_state:
                init_state.update(initial_state)

            # Execute the workflow
            self.logger.info("Starting workflow execution...")
            results = self.graph.invoke(init_state)

            # Add execution metadata
            results["execution_info"] = {
                "scenario": "scenario_one",
                "workflow": "caption → tags → image_tags → merge → translate",
                "nodes_executed": [
                    "caption_generator", "tag_extractor",
                    "image_tag_extractor", "merger", "translator"
                ],
                "success": True
            }

            self.logger.info("Scenario One execution completed successfully")
            self._log_execution_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Scenario One: {str(e)}")

            # Return error result
            error_result = {
                "error": str(e),
                "scenario": "scenario_one",
                "image_url": image_url,
                "execution_info": {
                    "scenario": "scenario_one",
                    "success": False,
                    "error": str(e)
                }
            }

            return error_result

    def _log_execution_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""

        # Log English results
        if "merged_tags" in results:
            merged_data = results["merged_tags"]
            entities_count = len(merged_data.get("entities", []))
            categories_count = len(merged_data.get("categories", []))

            self.logger.info(f"Merged results: {entities_count} entities, {categories_count} categories")

        # Log translation results
        if "persian_output" in results:
            persian_data = results["persian_output"]
            persian_entities = len(persian_data.get("entities", []))

            self.logger.info(f"Persian translation: {persian_entities} entities")

        # Log any errors
        if "errors" in results and results["errors"]:
            error_count = len(results["errors"])
            self.logger.warning(f"Execution completed with {error_count} errors")

    def get_scenario_info(self) -> Dict[str, Any]:
        """
        Get information about this scenario.

        Returns:
            Scenario description and capabilities
        """
        return {
            "name": "Scenario One",
            "description": "Comprehensive sequential analysis with both caption and direct image processing",
            "workflow": [
                "Caption Generation",
                "Tag Extraction from Caption",
                "Direct Image Tag Extraction",
                "Intelligent Merging",
                "Translation to Target Language"
            ],
            "strengths": [
                "Most comprehensive analysis",
                "Combines multiple extraction methods",
                "High accuracy through merging",
                "Multi-language support"
            ],
            "use_cases": [
                "Product catalog analysis",
                "Detailed image understanding",
                "Multi-source validation",
                "International content processing"
            ],
            "estimated_time": "30-60 seconds",
            "model_calls": 5
        }
