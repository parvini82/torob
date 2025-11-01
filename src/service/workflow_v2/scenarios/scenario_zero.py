"""
Scenario Zero: Ultra-Fast Direct Analysis.

Image → Direct Tags → Translate
Fastest possible workflow with direct image analysis and translation only.
Perfect for high-volume processing or real-time applications.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from ..core import StateManager, GraphBuilder, get_workflow_logger
from ..nodes import (
    ImageTagExtractorNode,
    TranslatorNode
)


class ScenarioZero:
    """
    Ultra-fast direct analysis scenario.

    Workflow:
    1. ImageTagExtractor: Direct image analysis for fashion tags
    2. Translator: Translate results to target language

    This is the fastest possible workflow, skipping caption generation
    and merging steps for maximum speed while maintaining accuracy.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scenario Zero.

        Args:
            config: Optional configuration for the scenario
        """
        self.config = config or {}
        self.logger = get_workflow_logger(f"{__name__}.ScenarioZero")
        self.graph = None

        self.logger.info("Initialized Scenario Zero - Ultra-Fast Direct Analysis")

    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph for Scenario Zero.

        Returns:
            Configured StateGraph for execution
        """
        self.logger.info("Building Scenario Zero workflow graph")

        # Initialize graph builder
        builder = GraphBuilder("ScenarioZero_Graph")

        # Add nodes with configuration
        node_config = self.config.get("node_config", {})

        builder.add_node("image_tag_extractor", ImageTagExtractorNode(
            model=node_config.get("image_model", None)  # Uses env variable by default
        ))

        builder.add_node("translator", TranslatorNode(
            model=node_config.get("translation_model", None),  # Uses env variable by default
            target_language=node_config.get("target_language", "Persian")
        ))

        # Add direct edge - no intermediate steps
        builder.add_edge("image_tag_extractor", "translator")

        # Set entry point
        builder.set_entry_point("image_tag_extractor")

        # Build and store the graph
        self.graph = builder.build()

        self.logger.info("Successfully built Scenario Zero workflow graph")
        return self.graph

    def execute(self, image_url: str, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Scenario Zero workflow.

        Args:
            image_url: URL or data URI of image to analyze
            initial_state: Optional initial state data

        Returns:
            Complete workflow execution results
        """
        self.logger.info(f"Executing Scenario Zero for image: {image_url[:50]}...")

        try:
            # Build graph if not already built
            if not self.graph:
                self.build_graph()

            # Prepare initial state
            init_state = {
                "image_url": image_url,
                "scenario": "scenario_zero",
                "config": self.config
            }

            # Add any provided initial state
            if initial_state:
                init_state.update(initial_state)

            # Execute the workflow (direct invoke)
            self.logger.info("Starting ultra-fast workflow execution...")
            results = self.graph.invoke(init_state)

            # Add execution metadata
            results["execution_info"] = {
                "scenario": "scenario_zero",
                "workflow": "image → direct_tags → translate",
                "nodes_executed": ["image_tag_extractor", "translator"],
                "optimization": "ultra_fast",
                "model_calls": 2,
                "success": True
            }

            self.logger.info("Scenario Zero execution completed successfully")
            self._log_execution_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Scenario Zero: {str(e)}")

            # Return error result
            error_result = {
                "error": str(e),
                "scenario": "scenario_zero",
                "image_url": image_url,
                "execution_info": {
                    "scenario": "scenario_zero",
                    "success": False,
                    "error": str(e)
                }
            }

            return error_result

    def _log_execution_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of ultra-fast execution results."""

        # Log direct image analysis results
        if "image_tags" in results:
            image_data = results["image_tags"]
            entities_count = len(image_data.get("entities", []))
            categories_count = len(image_data.get("categories", []))
            quality_score = image_data.get("quality_score", 0.0)

            self.logger.info(f"Direct image analysis: {entities_count} entities, {categories_count} categories")
            if quality_score > 0:
                self.logger.info(f"Image analysis quality: {quality_score:.2f}")

        # Log translation results
        if "persian_output" in results:
            persian_data = results["persian_output"]
            persian_entities = len(persian_data.get("entities", []))

            self.logger.info(f"Persian translation: {persian_entities} entities")

        # Log performance metrics
        exec_info = results.get("execution_info", {})
        model_calls = exec_info.get("model_calls", 0)
        self.logger.info(f"Performance: {model_calls} model calls total")

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
            "name": "Scenario Zero",
            "description": "Ultra-fast direct image analysis with immediate translation",
            "workflow": [
                "Direct Image Tag Extraction",
                "Translation to Target Language"
            ],
            "strengths": [
                "Maximum speed",
                "Minimal resource usage",
                "Direct visual analysis",
                "Real-time capable",
                "Cost effective"
            ],
            "use_cases": [
                "High-volume processing",
                "Real-time applications",
                "Mobile applications",
                "Resource-constrained environments",
                "Quick product categorization"
            ],
            "estimated_time": "8-15 seconds",
            "model_calls": 2,
            "optimization_level": "ultra_fast"
        }
