"""
Scenario Two: Simple Caption-Based Analysis.

Caption → Tags → Translate
Fast and simple workflow using only caption-based extraction.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from ..core import StateManager, GraphBuilder, get_workflow_logger
from ..nodes import (
    CaptionGeneratorNode,
    TagExtractorNode,
    TranslatorNode
)


class ScenarioTwo:
    """
    Simple caption-based analysis scenario.

    Workflow:
    1. CaptionGenerator: Generate descriptive caption from image
    2. TagExtractor: Extract structured tags from caption
    3. Translator: Translate results to target language
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scenario Two.

        Args:
            config: Optional configuration for the scenario
        """
        self.config = config or {}
        self.logger = get_workflow_logger(f"{__name__}.ScenarioTwo")
        self.graph = None

        self.logger.info("Initialized Scenario Two - Simple Caption-Based Analysis")

    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph for Scenario Two.

        Returns:
            Configured StateGraph for execution
        """
        self.logger.info("Building Scenario Two workflow graph")

        # Initialize graph builder
        builder = GraphBuilder("ScenarioTwo_Graph")

        # Add nodes with configuration
        node_config = self.config.get("node_config", {})

        builder.add_node("caption_generator", CaptionGeneratorNode(
            model=node_config.get("caption_model", "qwen/qwen2.5-vl-32b-instruct:free")
        ))

        builder.add_node("tag_extractor", TagExtractorNode(
            model=node_config.get("tag_model", "qwen/qwen2.5-vl-32b-instruct:free")
        ))

        builder.add_node("translator", TranslatorNode(
            model=node_config.get("translation_model", "qwen/qwen2.5-vl-32b-instruct:free"),
            target_language=node_config.get("target_language", "Persian")
        ))

        # Add edges to create the workflow
        builder.add_edge("caption_generator", "tag_extractor")
        builder.add_edge("tag_extractor", "translator")

        # Set entry point
        builder.set_entry_point("caption_generator")

        # Build and store the graph
        self.graph = builder.build()

        self.logger.info("Successfully built Scenario Two workflow graph")
        return self.graph

    def execute(self, image_url: str, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Scenario Two workflow.

        Args:
            image_url: URL or data URI of image to analyze
            initial_state: Optional initial state data

        Returns:
            Complete workflow execution results
        """
        self.logger.info(f"Executing Scenario Two for image: {image_url[:50]}...")

        try:
            # Build graph if not already built
            if not self.graph:
                self.build_graph()

            # Prepare initial state
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
                "scenario": "scenario_two",
                "workflow": "caption → tags → translate",
                "nodes_executed": ["caption_generator", "tag_extractor", "translator"],
                "success": True
            }

            self.logger.info("Scenario Two execution completed successfully")
            self._log_execution_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Scenario Two: {str(e)}")

            # Return error result
            error_result = {
                "error": str(e),
                "scenario": "scenario_two",
                "image_url": image_url,
                "execution_info": {
                    "scenario": "scenario_two",
                    "success": False,
                    "error": str(e)
                }
            }

            return error_result

    def _log_execution_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""

        # Log extraction results
        if "extracted_tags" in results:
            extracted_data = results["extracted_tags"]
            entities_count = len(extracted_data.get("entities", []))
            categories_count = len(extracted_data.get("categories", []))

            self.logger.info(f"Extracted: {entities_count} entities, {categories_count} categories")

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
            "name": "Scenario Two",
            "description": "Fast and simple caption-based analysis",
            "workflow": [
                "Caption Generation",
                "Tag Extraction from Caption",
                "Translation to Target Language"
            ],
            "strengths": [
                "Fast execution",
                "Simple and reliable",
                "Good for basic analysis",
                "Low resource usage"
            ],
            "use_cases": [
                "Quick image categorization",
                "Basic product analysis",
                "High-volume processing",
                "Performance-critical applications"
            ],
            "estimated_time": "15-30 seconds",
            "model_calls": 3
        }
