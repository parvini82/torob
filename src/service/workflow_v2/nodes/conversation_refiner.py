"""
Conversation refiner node for iterative fashion analysis improvement.

Uses conversation loops with AI models to iteratively refine and improve
fashion extraction results through multi-turn analysis until convergence
or maximum iterations reached. Provides highest possible accuracy.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError
from ..prompts import ConversationRefinementPrompts

# Load environment variables
load_dotenv()

# Default conversation model from environment
CONVERSATION_MODEL: str = os.getenv("CONVERSATION_MODEL", "anthropic/claude-3.5-sonnet:beta")


class ConversationRefinerNode(BaseNode):
    """
    Node that uses iterative conversation loops to refine fashion extraction results.

    Engages in multi-turn conversations with AI models to progressively
    improve fashion analysis quality through feedback cycles, achieving
    the highest possible accuracy through iterative enhancement.
    """

    def __init__(self,
                 model: str = None,
                 max_iterations: int = 3,
                 convergence_threshold: float = 0.1):
        """
        Initialize the conversation refiner node.

        Args:
            model: Model for conversation refinement. If None, uses CONVERSATION_MODEL from env
            max_iterations: Maximum number of refinement iterations
            convergence_threshold: Threshold for detecting convergence (lower = more similar)
        """
        super().__init__("ConversationRefiner")
        self.model = model or CONVERSATION_MODEL
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.client = None

        self.logger.info(f"Initialized conversation refiner with model: {self.model}")
        self.logger.info(f"Max iterations: {max_iterations}, Convergence threshold: {convergence_threshold}")

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform iterative conversation-based fashion refinement.

        Conducts multiple rounds of AI-assisted refinement through conversation,
        progressively improving fashion analysis accuracy until convergence
        is achieved or maximum iterations reached.

        Args:
            state: Workflow state containing extraction results and image

        Returns:
            Updated state with refined results and conversation history

        Raises:
            ModelClientError: If conversation model calls fail
        """
        # Find content to refine
        refinable_content = self._find_refinable_fashion_content(state)

        if not refinable_content:
            self.logger.warning("No refinable fashion content found in state")
            return state

        # Get image URL for visual context
        image_url = state.get("image_url")
        if not image_url:
            self.logger.warning("No image URL found - refinement may be less effective")

        # Get configuration
        config = self.get_node_config(state)
        model_to_use = config.get("model", self.model)
        max_iters = config.get("max_iterations", self.max_iterations)
        convergence_thresh = config.get("convergence_threshold", self.convergence_threshold)

        # Initialize client if needed
        if not self.client:
            self.client = create_model_client()

        self.logger.info(f"Starting iterative fashion refinement with {max_iters} max iterations")

        try:
            # Perform iterative refinement conversation
            refined_result, conversation_history = self._perform_iterative_fashion_refinement(
                refinable_content, image_url, model_to_use, max_iters, convergence_thresh
            )

            # Update state
            updated_state = state.copy()
            updated_state["conversation_tags"] = refined_result
            updated_state["conversation_history"] = conversation_history

            # Log final statistics
            self._log_conversation_fashion_statistics(refined_result, conversation_history)

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Conversation model error during iterative refinement: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during conversation refinement: {str(e)}")
            raise

    def _find_refinable_fashion_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find fashion content suitable for conversation refinement."""
        # Priority order for conversation refinement sources
        sources = [
            "refined_tags",     # Already refined content (for further improvement)
            "merged_tags",      # Merged results
            "image_tags",       # Direct image analysis
            "extracted_tags"    # Text-based extraction
        ]

        for source in sources:
            if source in state and isinstance(state[source], dict):
                content = state[source]
                if self._is_conversation_refinable_content(content):
                    self.logger.debug(f"Using fashion content for conversation from: {source}")
                    return content

        return {}

    def _is_conversation_refinable_content(self, content: Dict[str, Any]) -> bool:
        """Check if content is suitable for conversation-based refinement."""
        # Need substantial content for meaningful conversation refinement
        entities = content.get("entities", [])
        categories = content.get("categories", [])

        # Minimum thresholds for conversation refinement to be worthwhile
        has_sufficient_entities = len(entities) >= 2
        has_categories = len(categories) >= 1

        return has_sufficient_entities and has_categories

    def _perform_iterative_fashion_refinement(self,
                                            initial_content: Dict[str, Any],
                                            image_url: Optional[str],
                                            model: str,
                                            max_iterations: int,
                                            convergence_threshold: float) -> tuple:
        """
        Perform the iterative fashion refinement conversation.

        This is the core logic: starts a conversation with AI and keeps
        refining until the changes become minimal (convergence) or max iterations reached.
        """

        conversation_history = []
        current_content = initial_content.copy()
        previous_content = None
        converged = False
        iterations_used = 0

        # Initialize conversation with system message
        conversation_context = [
            {
                "role": "system",
                "content": ConversationRefinementPrompts.SYSTEM_PROMPT
            }
        ]

        self.logger.info(f"Starting conversation refinement - Initial entities: {len(current_content.get('entities', []))}")

        for iteration in range(max_iterations):
            iterations_used = iteration + 1
            self.logger.info(f"Conversation iteration {iterations_used}/{max_iterations}")

            # Create iteration-specific refinement request
            refinement_request = self._create_fashion_refinement_request(
                current_content, iteration, image_url
            )

            conversation_context.append({
                "role": "user",
                "content": refinement_request
            })

            # Get refinement response
            try:
                refined_response = self.client.call_json(
                    model,
                    conversation_context,
                    max_tokens=3000,  # Increased for comprehensive fashion conversations
                    temperature=0.2   # Low for consistent iterative improvements
                )

                # Add response to conversation context (for next iteration)
                conversation_context.append({
                    "role": "assistant",
                    "content": str(refined_response)
                })

                # Structure the refined result
                iteration_result = self._structure_conversation_fashion_result(
                    refined_response, current_content, iteration, model
                )

                # Record this iteration's statistics
                iteration_stats = {
                    "iteration": iteration + 1,
                    "input_entities": len(current_content.get("entities", [])),
                    "output_entities": len(iteration_result.get("entities", [])),
                    "changes_made": iteration_result.get("iteration_changes", []),
                    "refinement_focus": iteration_result.get("refinement_focus", ""),
                    "confidence_improvement": self._calculate_confidence_change(
                        current_content, iteration_result
                    )
                }

                conversation_history.append(iteration_stats)

                # Check for convergence (are changes getting smaller?)
                if previous_content:
                    convergence_score = self._calculate_fashion_convergence(previous_content, iteration_result)
                    conversation_history[-1]["convergence_score"] = convergence_score

                    self.logger.debug(f"Convergence score: {convergence_score:.3f} (threshold: {convergence_threshold})")

                    if convergence_score < convergence_threshold:
                        self.logger.info(f"Fashion refinement converged at iteration {iterations_used}")
                        converged = True
                        break

                # Update for next iteration
                previous_content = current_content.copy()
                current_content = iteration_result

            except Exception as e:
                self.logger.error(f"Error in conversation iteration {iterations_used}: {str(e)}")
                conversation_history.append({
                    "iteration": iteration + 1,
                    "error": str(e),
                    "status": "failed"
                })
                break

        # Create final result with convergence info
        final_result = current_content.copy()
        final_result["convergence_info"] = {
            "converged_early": converged,
            "iterations_used": iterations_used,
            "max_iterations": max_iterations,
            "convergence_threshold": convergence_threshold,
            "final_convergence_score": convergence_score if previous_content else 0.0
        }

        return final_result, conversation_history

    def _create_fashion_refinement_request(self,
                                         current_content: Dict[str, Any],
                                         iteration: int,
                                         image_url: Optional[str]) -> str:
        """Create a fashion-specific refinement request for the current iteration."""

        import json

        # Get iteration-specific focus from prompts
        iteration_focus = ConversationRefinementPrompts.get_iteration_prompt(iteration)

        # Format current content for review
        content_json = json.dumps(current_content, indent=2, ensure_ascii=False)

        request = f"""{iteration_focus}

Fashion extraction results to refine:

{content_json}

Please provide your refined version with clear documentation of improvements made.
Focus on fashion industry accuracy and commercial value."""

        # Add image context for first iteration
        if image_url and iteration == 0:
            request += f"\n\nOriginal fashion product image for visual reference: {image_url}"

        return request

    def _structure_conversation_fashion_result(self,
                                             refined_data: Dict[str, Any],
                                             original_content: Dict[str, Any],
                                             iteration: int,
                                             model: str) -> Dict[str, Any]:
        """Structure the conversation fashion refinement result."""

        result = {
            "entities": [],
            "categories": [],
            "attributes": {},
            "iteration_changes": [],
            "refinement_focus": "",
            "confidence_assessment": "",
            "suggested_next_focus": "",
            "summary": "",
            "model_used": model,
            "refined_by": self.node_name,
            "refinement_method": "iterative_conversation",
            "iteration_number": iteration + 1,
            "original_source": original_content.get("extracted_by", "unknown")
        }

        # Structure entities (handle both formats)
        if "entities" in refined_data:
            result["entities"] = self._structure_conversation_fashion_entities(refined_data["entities"])

        # Structure categories
        if "categories" in refined_data:
            result["categories"] = self._structure_conversation_fashion_categories(refined_data["categories"])

        # Structure attributes
        if "attributes" in refined_data:
            result["attributes"] = self._structure_conversation_fashion_attributes(refined_data["attributes"])

        # Extract conversation metadata
        result["iteration_changes"] = refined_data.get("iteration_changes", [])
        result["refinement_focus"] = str(refined_data.get("refinement_focus", ""))
        result["confidence_assessment"] = str(refined_data.get("confidence_assessment", ""))
        result["suggested_next_focus"] = str(refined_data.get("suggested_next_focus", ""))
        result["summary"] = str(refined_data.get("summary", ""))

        return result

    def _calculate_fashion_convergence(self, previous_content: Dict[str, Any], current_content: Dict[str, Any]) -> float:
        """
        Calculate convergence score between two fashion analysis iterations.

        Returns a score where:
        - 0.0 = identical results (fully converged)
        - 1.0 = completely different results
        """

        # Compare entities (handle both name/values and name/type formats)
        prev_entities = self._extract_entity_signatures(previous_content.get("entities", []))
        curr_entities = self._extract_entity_signatures(current_content.get("entities", []))

        # Calculate entity similarity
        if not prev_entities and not curr_entities:
            entity_similarity = 1.0
        elif not prev_entities or not curr_entities:
            entity_similarity = 0.0
        else:
            intersection = len(prev_entities.intersection(curr_entities))
            union = len(prev_entities.union(curr_entities))
            entity_similarity = intersection / union if union > 0 else 0.0

        # Compare categories
        prev_categories = set()
        curr_categories = set()

        for cat in previous_content.get("categories", []):
            if isinstance(cat, dict) and "name" in cat:
                prev_categories.add(f"{cat['name']}_{cat.get('type', 'general')}")

        for cat in current_content.get("categories", []):
            if isinstance(cat, dict) and "name" in cat:
                curr_categories.add(f"{cat['name']}_{cat.get('type', 'general')}")

        if not prev_categories and not curr_categories:
            category_similarity = 1.0
        elif not prev_categories or not curr_categories:
            category_similarity = 0.0
        else:
            intersection = len(prev_categories.intersection(curr_categories))
            union = len(prev_categories.union(curr_categories))
            category_similarity = intersection / union if union > 0 else 0.0

        # Calculate overall convergence (1.0 = identical, 0.0 = completely different)
        convergence_score = (entity_similarity + category_similarity) / 2.0

        # Return divergence score (lower = more converged)
        return 1.0 - convergence_score

    def _extract_entity_signatures(self, entities: List[Dict[str, Any]]) -> set:
        """Extract unique signatures from entities for comparison."""
        signatures = set()

        for entity in entities:
            if isinstance(entity, dict):
                if "name" in entity and "values" in entity:
                    # New format: name + values
                    values_str = "-".join(entity.get("values", [])[:2])  # Use first 2 values
                    signatures.add(f"{entity['name']}_{values_str}")
                elif "name" in entity and "type" in entity:
                    # Legacy format: name + type
                    signatures.add(f"{entity['name']}_{entity.get('type', 'unknown')}")

        return signatures

    def _calculate_confidence_change(self, previous_content: Dict[str, Any], current_content: Dict[str, Any]) -> float:
        """Calculate the change in average confidence scores."""

        def get_avg_confidence(content):
            confidences = []
            for entity in content.get("entities", []):
                if isinstance(entity, dict):
                    confidences.append(entity.get("confidence", 0.8))
            for category in content.get("categories", []):
                if isinstance(category, dict):
                    confidences.append(category.get("confidence", 0.8))
            return sum(confidences) / len(confidences) if confidences else 0.0

        prev_conf = get_avg_confidence(previous_content)
        curr_conf = get_avg_confidence(current_content)

        return curr_conf - prev_conf

    def _structure_conversation_fashion_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure entities from conversation refinement."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                # Handle different entity formats
                if "values" in entity:
                    # New fashion format
                    structured_entity = {
                        "name": str(entity["name"]),
                        "values": [str(v) for v in entity["values"] if v] if isinstance(entity["values"], list) else [str(entity["values"])],
                        "entity_type": "conversation_refined",
                        "confidence": float(entity.get("confidence", 0.95)),  # Higher confidence after conversation
                        "source": "iterative_conversation",
                        "iteration_notes": str(entity.get("iteration_notes", ""))
                    }
                else:
                    # Legacy format
                    structured_entity = {
                        "name": str(entity["name"]),
                        "type": str(entity.get("type", "unknown")),
                        "confidence": float(entity.get("confidence", 0.95)),
                        "context": str(entity.get("context", "")),
                        "attributes": entity.get("attributes", []),
                        "relationships": entity.get("relationships", []),
                        "iteration_notes": str(entity.get("iteration_notes", ""))
                    }

                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_conversation_fashion_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure categories from conversation refinement."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "type": category.get("type", "general"),
                    "level": str(category.get("level", "main")),
                    "confidence": float(category.get("confidence", 0.95)),
                    "reasoning": str(category.get("reasoning", "")),
                    "entities": category.get("entities", []),
                    "iteration_notes": str(category.get("iteration_notes", ""))
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_conversation_fashion_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure attributes from conversation refinement."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _log_conversation_fashion_statistics(self, refined_result: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> None:
        """Log statistics about the conversation fashion refinement."""
        convergence_info = refined_result.get("convergence_info", {})

        self.logger.info("Iterative fashion refinement completed:")
        self.logger.info(f"  Iterations used: {convergence_info.get('iterations_used', 0)}")
        self.logger.info(f"  Converged early: {convergence_info.get('converged_early', False)}")
        self.logger.info(f"  Final convergence score: {convergence_info.get('final_convergence_score', 0.0):.3f}")

        if conversation_history:
            final_entities = len(refined_result.get("entities", []))
            final_categories = len(refined_result.get("categories", []))

            self.logger.info(f"  Final entities: {final_entities}")
            self.logger.info(f"  Final categories: {final_categories}")

            # Log confidence improvements across all iterations
            total_confidence_change = sum(
                hist.get("confidence_improvement", 0)
                for hist in conversation_history
                if "confidence_improvement" in hist
            )

            if abs(total_confidence_change) > 0.001:
                self.logger.info(f"  Total confidence change: {total_confidence_change:+.3f}")

            # Log iteration focuses
            focuses = [hist.get("refinement_focus", "") for hist in conversation_history if hist.get("refinement_focus")]
            if focuses:
                self.logger.debug(f"  Iteration focuses: {focuses}")
