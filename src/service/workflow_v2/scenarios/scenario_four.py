"""
Scenario Four: Iterative Conversation Refinement.

Extract → Iterative Refinement → Translate
Highest accuracy through iterative improvement with conversation loops.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from ..core import StateManager, GraphBuilder, get_workflow_logger
from ..nodes import (
    ImageTagExtractorNode,
    ConversationRefinerNode,
    TranslatorNode
)


class ScenarioFour:
    """
    Iterative conversation refinement scenario.

    Workflow:
    1. ImageTagExtractor: Initial direct image analysis
    2. ConversationRefiner: Iterative refinement through conversation
    3. Translator: Translate final refined results
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Scenario Four.

        Args:
            config: Optional configuration for the scenario
        """
        self.config = config or {}
        self.logger = get_workflow_logger(f"{__name__}.ScenarioFour")
        self.graph = None

        self.logger.info("Initialized Scenario Four - Iterative Conversation Refinement")

    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph for Scenario Four.

        Returns:
            Configured StateGraph for execution
        """
        self.logger.info("Building Scenario Four workflow graph")

        # Initialize graph builder
        builder = GraphBuilder("ScenarioFour_Graph")

        # Add nodes with configuration
        node_config = self.config.get("node_config", {})

        builder.add_node("image_tag_extractor", ImageTagExtractorNode(
            model=node_config.get("extractor_model", "google/gemini-flash-1.5")
        ))

        builder.add_node("conversation_refiner", ConversationRefinerNode(
            model=node_config.get("refiner_model", "google/gemini-flash-1.5"),
            max_iterations=node_config.get("max_iterations", 3),
            convergence_threshold=node_config.get("convergence_threshold", 0.1)
        ))

        builder.add_node("translator", TranslatorNode(
            model=node_config.get("translation_model", "google/gemini-flash-1.5"),
            target_language=node_config.get("target_language", "Persian")
        ))

        # Add edges to create the workflow
        builder.add_edge("image_tag_extractor", "conversation_refiner")
        builder.add_edge("conversation_refiner", "translator")

        # Set entry point
        builder.set_entry_point("image_tag_extractor")

        # Build and store the graph
        self.graph = builder.build()

        self.logger.info("Successfully built Scenario Four workflow graph")
        return self.graph

    def execute(self, image_url: str, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Scenario Four workflow.

        Args:
            image_url: URL or data URI of image to analyze
            initial_state: Optional initial state data

        Returns:
            Complete workflow execution results
        """
        self.logger.info(f"Executing Scenario Four for image: {image_url[:50]}...")

        try:
            # Build graph if not already built
            if not self.graph:
                self.build_graph()

            # Initialize state
            state_manager = StateManager()

            # Prepare initial state
            init_state = {
                "image_url": image_url,
                "scenario": "scenario_four",
                "config": self.config
            }

            # Add any provided initial state
            if initial_state:
                init_state.update(initial_state)

            state_manager.initialize_state(init_state)

            # Execute the workflow
            self.logger.info("Starting workflow execution...")
            final_state = self.graph.invoke(state_manager)

            # Extract results
            results = final_state.get_full_state()

            # Add execution metadata
            convergence_info = results.get("conversation_tags", {}).get("convergence_info", {})

            results["execution_info"] = {
                "scenario": "scenario_four",
                "workflow": "extract → iterative_refinement → translate",
                "nodes_executed": ["image_tag_extractor", "conversation_refiner", "translator"],
                "refinement_iterations": convergence_info.get("iterations_used", 0),
                "converged_early": convergence_info.get("converged_early", False),
                "success": True
            }

            self.logger.info("Scenario Four execution completed successfully")
            self._log_execution_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Scenario Four: {str(e)}")

            # Return error result
            error_result = {
                "error": str(e),
                "scenario": "scenario_four",
                "image_url": image_url,
                "execution_info": {
                    "scenario": "scenario_four",
                    "success": False,
                    "error": str(e)
                }
            }

            return error_result

    def _log_execution_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""

        exec_info = results.get("execution_info", {})

        # Log refinement statistics
        iterations = exec_info.get("refinement_iterations", 0)
        converged = exec_info.get("converged_early", False)

        self.logger.info(f"Conversation refinement: {iterations} iterations")
        self.logger.info(f"Early convergence: {converged}")

        # Log conversation history
        if "conversation_history" in results:
            history = results["conversation_history"]
            successful_iterations = len([h for h in history if "error" not in h])

            self.logger.info(f"Successful refinement iterations: {successful_iterations}")

            # Log confidence improvements
            total_confidence_change = sum(
                h.get("confidence_improvement", 0) for h in history
            )

            if total_confidence_change != 0:
                self.logger.info(f"Total confidence improvement: {total_confidence_change:+.3f}")

        # Log final results
        if "conversation_tags" in results:
            conversation_data = results["conversation_tags"]
            entities_count = len(conversation_data.get("entities", []))
            categories_count = len(conversation_data.get("categories", []))

            self.logger.info(f"Final refined results: {entities_count} entities, {categories_count} categories")

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
            "name": "Scenario Four",
            "description": "Highest accuracy through iterative conversation refinement",
            "workflow": [
                "Initial Image Tag Extraction",
                "Iterative Conversation Refinement",
                "Translation to Target Language"
            ],
            "strengths": [
                "Highest possible accuracy",
                "Self-improving through iterations",
                "Adaptive convergence detection",
                "Detailed refinement tracking"
            ],
            "use_cases": [
                "Maximum accuracy requirements",
                "Research and analysis",
                "Quality benchmarking",
                "Model evaluation"
            ],
            "estimated_time": "60-180 seconds",
            "model_calls": "4-10 (depends on convergence)"
        }
