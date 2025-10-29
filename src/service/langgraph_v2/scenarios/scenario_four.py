"""
Scenario Four: Conversation Loop with Iterative Refinement

This scenario implements a conversation loop where tags are
extracted, then iteratively refined based on previous results
and the original image.
"""

from typing import Dict, Any
from ..core.graph_builder import GraphBuilder
from ..core.state_manager import StateManager
from ..nodes.image_tag_extractor import ImageTagExtractorNode
from ..nodes.refiner import RefinerNode
from ..nodes.translator import TranslatorNode


class ConversationStateManager:
    """
    Manages conversation state for iterative refinement loops.
    """

    def __init__(self, max_iterations: int = 2):
        """
        Initialize conversation state manager.

        Args:
            max_iterations: Maximum number of refinement iterations
        """
        self.max_iterations = max_iterations

    def should_continue_refinement(self, state: Dict[str, Any]) -> bool:
        """
        Determine if refinement loop should continue.

        Args:
            state: Current workflow state

        Returns:
            True if refinement should continue, False otherwise
        """
        current_iteration = state.get("refinement_iteration", 0)

        # Stop if max iterations reached
        if current_iteration >= self.max_iterations:
            return False

        # Stop if previous refinement had minimal changes
        refinement_summary = state.get("refinement_summary", {})
        changes_detected = refinement_summary.get("changes_detected", 0)

        # If very few changes in last iteration, consider converged
        if current_iteration > 0 and changes_detected < 2:
            return False

        return True

    def update_iteration_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update state for next iteration.

        Args:
            state: Current workflow state

        Returns:
            Updated state with iteration tracking
        """
        current_iteration = state.get("refinement_iteration", 0)

        # Move refined tags to previous tags for next iteration
        refined_tags = state.get("refined_tags", {})

        return {
            **state,
            "refinement_iteration": current_iteration + 1,
            "previous_tags": refined_tags,
            "iteration_history": state.get("iteration_history", []) + [
                {
                    "iteration": current_iteration,
                    "tags": refined_tags,
                    "summary": state.get("refinement_summary", {})
                }
            ]
        }


class ConversationRefinerNode(RefinerNode):
    """
    Specialized refiner node for conversation loops.

    This node handles iteration state management and
    convergence detection.
    """

    def __init__(self, name: str = "conversation_refiner", config: Dict[str, Any] = None):
        """
        Initialize conversation refiner node.

        Args:
            name: Node identifier
            config: Optional configuration
        """
        super().__init__(name, config)
        self.conversation_manager = ConversationStateManager(
            max_iterations=self.config.get("max_iterations", 2)
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run refinement with conversation loop management.

        Args:
            state: Current workflow state

        Returns:
            Updated state with refinement results
        """
        current_iteration = state.get("refinement_iteration", 0)
        self.log_execution(f"Starting refinement iteration {current_iteration + 1}")

        # Run the refinement process
        refined_state = super().run(state)

        # Update conversation state
        updated_state = self.conversation_manager.update_iteration_state(refined_state)

        # Check if we should continue refining
        should_continue = self.conversation_manager.should_continue_refinement(updated_state)
        updated_state["should_continue_refinement"] = should_continue

        if should_continue:
            self.log_execution("Refinement will continue for another iteration")
        else:
            self.log_execution("Refinement loop completed - converged or max iterations reached")

        return updated_state


class ScenarioFour:
    """
    Implementation of Scenario Four workflow.

    Workflow: Image → Extract Tags → [Refine Loop] → Translate
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize scenario four with optional configuration.

        Args:
            config: Configuration including max_iterations
        """
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 2)
        self.state_manager = StateManager()
        self.graph = None
        self._build_workflow()

    def _build_workflow(self):
        """Build the conversation loop workflow."""
        builder = GraphBuilder("scenario_four")

        # Create nodes
        initial_extractor = ImageTagExtractorNode(
            "initial_extraction",
            config=self.config.get("extractor_config", {})
        )

        refiner = ConversationRefinerNode(
            "conversation_refiner",
            config={
                "max_iterations": self.max_iterations,
                **self.config.get("refiner_config", {})
            }
        )

        translator = TranslatorNode(
            "translate_final",
            config={"input_key": "refined_tags"}
        )

        # Add nodes to graph
        builder.add_node(initial_extractor)
        builder.add_node(refiner)
        builder.add_node(translator)

        # Define edges
        builder.add_sequential_edge("initial_extraction", "conversation_refiner")

        # Add conditional edge for refinement loop
        def should_continue_refining(state: Dict[str, Any]) -> str:
            """Routing function for refinement loop."""
            if state.get("should_continue_refinement", False):
                return "conversation_refiner"  # Continue loop
            else:
                return "translate_final"  # Exit loop

        # Note: This requires LangGraph conditional edges
        # For simplicity, we'll implement a fixed iteration approach

        builder.add_sequential_edge("conversation_refiner", "translate_final")

        # Set entry and finish points
        builder.set_entry_point("initial_extraction")
        builder.set_finish_point("translate_final")

        self.graph = builder.build()

    def execute(self, image_url: str) -> Dict[str, Any]:
        """
        Execute scenario four workflow with conversation loop.

        Args:
            image_url: URL or data URI of image to process

        Returns:
            Final workflow results with iteration history
        """
        initial_state = self.state_manager.create_initial_state(
            image_url=image_url,
            scenario="scenario_four",
            refinement_iteration=0,
            max_iterations=self.max_iterations
        )

        # For conversation loops, we might need to run multiple times
        # This is a simplified implementation - in practice, you might
        # need more sophisticated loop handling

        current_state = initial_state

        # Run initial extraction
        current_state = self._run_initial_extraction(current_state)

        # Run refinement iterations
        current_state = self._run_refinement_loop(current_state)

        # Run final translation
        final_state = self._run_translation(current_state)

        return {
            "scenario": "scenario_four",
            "execution_summary": self.state_manager.get_execution_summary(),
            "results": {
                "initial_tags": final_state.get("image_tags", {}),
                "iteration_history": final_state.get("iteration_history", []),
                "final_refined_tags": final_state.get("refined_tags", {}),
                "translated_tags": final_state.get("translated_tags", {}),
                "total_iterations": final_state.get("refinement_iteration", 0)
            },
            "english_output": final_state.get("refined_tags", {}),
            "persian_output": final_state.get("translated_tags", {}),
            "convergence_info": {
                "iterations_used": final_state.get("refinement_iteration", 0),
                "max_iterations": self.max_iterations,
                "converged_early": final_state.get("refinement_iteration", 0) < self.max_iterations
            }
        }

    def _run_initial_extraction(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run initial tag extraction."""
        extractor = ImageTagExtractorNode("initial_extraction")
        return extractor.run(state)

    def _run_refinement_loop(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the refinement loop."""
        refiner = ConversationRefinerNode("conversation_refiner", {
            "max_iterations": self.max_iterations
        })

        current_state = state.copy()
        current_state["previous_tags"] = current_state.get("image_tags", {})

        # Run refinement iterations
        for iteration in range(self.max_iterations):
            current_state["refinement_iteration"] = iteration
            refined_state = refiner.run(current_state)

            # Check if we should continue
            if not refined_state.get("should_continue_refinement", False):
                break

            # Prepare for next iteration
            current_state = refined_state

        return refined_state

    def _run_translation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run final translation."""
        translator = TranslatorNode("translate_final", {"input_key": "refined_tags"})
        return translator.run(state)