"""
Conversation refiner node for iterative improvement.

Uses conversation loops with AI models to iteratively refine and improve
extraction results until convergence or maximum iterations reached.
"""

from typing import Dict, Any, List, Optional
from ..core.base_node import BaseNode
from ..model_client import create_model_client, ModelClientError


class ConversationRefinerNode(BaseNode):
    """
    Node that uses conversation loops to iteratively refine extraction results.

    Engages in multi-turn conversations with AI models to progressively
    improve extraction quality through feedback and refinement cycles.
    """

    def __init__(self,
                 model: str = "qwen/qwen2.5-vl-32b-instruct:free",
                 max_iterations: int = 3,
                 convergence_threshold: float = 0.1):
        """
        Initialize the conversation refiner node.

        Args:
            model: Model to use for conversation refinement
            max_iterations: Maximum number of refinement iterations
            convergence_threshold: Threshold for detecting convergence
        """
        super().__init__("ConversationRefiner")
        self.model = model
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.client = None

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform iterative conversation-based refinement.

        Args:
            state: Workflow state containing extraction results and image

        Returns:
            Updated state with refined results and conversation history
        """
        # Find content to refine
        refinable_content = self._find_refinable_content(state)

        if not refinable_content:
            self.logger.warning("No refinable content found in state")
            return state

        # Get image URL for context
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

        self.logger.info(f"Starting conversation refinement with {max_iters} max iterations")

        try:
            # Perform iterative refinement
            refined_result, conversation_history = self._perform_iterative_refinement(
                refinable_content, image_url, model_to_use, max_iters, convergence_thresh
            )

            # Update state
            updated_state = state.copy()
            updated_state["conversation_tags"] = refined_result
            updated_state["conversation_history"] = conversation_history

            # Log final statistics
            self._log_conversation_statistics(refined_result, conversation_history)

            return updated_state

        except ModelClientError as e:
            self.logger.error(f"Model client error during conversation refinement: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during conversation refinement: {str(e)}")
            raise

    def _find_refinable_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Find content that can be refined through conversation."""
        # Priority order for refinement sources
        sources = [
            "refined_tags",  # Already refined content
            "merged_tags",  # Merged results
            "image_tags",  # Direct image analysis
            "extracted_tags"  # Text-based extraction
        ]

        for source in sources:
            if source in state and isinstance(state[source], dict):
                content = state[source]
                if self._is_refinable_content(content):
                    self.logger.debug(f"Using content from: {source}")
                    return content

        return {}

    def _is_refinable_content(self, content: Dict[str, Any]) -> bool:
        """Check if content has fields that can be refined."""
        required_fields = ["entities", "categories"]
        return any(field in content and content[field] for field in required_fields)

    def _perform_iterative_refinement(self,
                                      initial_content: Dict[str, Any],
                                      image_url: Optional[str],
                                      model: str,
                                      max_iterations: int,
                                      convergence_threshold: float) -> tuple:
        """Perform the iterative refinement conversation."""

        conversation_history = []
        current_content = initial_content.copy()
        previous_content = None
        converged = False
        iterations_used = 0

        # Initialize conversation with system message
        conversation_context = [
            {
                "role": "system",
                "content": self._get_conversation_system_prompt()
            }
        ]

        for iteration in range(max_iterations):
            iterations_used = iteration + 1
            self.logger.info(f"Refinement iteration {iterations_used}/{max_iterations}")

            # Create refinement request
            refinement_request = self._create_refinement_request(
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
                    max_tokens=2500,
                    temperature=0.3
                )

                # Add response to conversation context
                conversation_context.append({
                    "role": "assistant",
                    "content": str(refined_response)
                })

                # Structure the refined result
                iteration_result = self._structure_conversation_result(
                    refined_response, current_content, iteration, model
                )

                # Record this iteration
                conversation_history.append({
                    "iteration": iteration + 1,
                    "input_entities": len(current_content.get("entities", [])),
                    "output_entities": len(iteration_result.get("entities", [])),
                    "changes_made": iteration_result.get("iteration_changes", []),
                    "refinement_focus": iteration_result.get("refinement_focus", ""),
                    "confidence_improvement": self._calculate_confidence_change(
                        current_content, iteration_result
                    )
                })

                # Check for convergence
                if previous_content:
                    convergence_score = self._calculate_convergence(previous_content, iteration_result)
                    conversation_history[-1]["convergence_score"] = convergence_score

                    if convergence_score < convergence_threshold:
                        self.logger.info(f"Convergence achieved at iteration {iterations_used}")
                        converged = True
                        break

                # Update for next iteration
                previous_content = current_content.copy()
                current_content = iteration_result

            except Exception as e:
                self.logger.error(f"Error in iteration {iterations_used}: {str(e)}")
                conversation_history.append({
                    "iteration": iteration + 1,
                    "error": str(e),
                    "status": "failed"
                })
                break

        # Create final result
        final_result = current_content.copy()
        final_result["convergence_info"] = {
            "converged_early": converged,
            "iterations_used": iterations_used,
            "max_iterations": max_iterations,
            "convergence_threshold": convergence_threshold
        }

        return final_result, conversation_history

    def _get_conversation_system_prompt(self) -> str:
        """Get system prompt for conversation refinement."""
        return """You are an expert extraction analyst engaged in iterative refinement through conversation.

Your role is to progressively improve extraction results through multiple rounds of analysis and refinement. Each iteration should build upon the previous results while addressing specific areas for improvement.

For each refinement iteration:

1. **Analyze Current State:**
   - Review the current extraction results
   - Identify areas that need improvement
   - Consider feedback from previous iterations

2. **Apply Targeted Improvements:**
   - Focus on 1-2 specific improvement areas per iteration
   - Make incremental, well-reasoned changes
   - Maintain high-quality existing extractions

3. **Document Changes:**
   - Clearly explain what changes were made and why
   - Provide confidence assessments for new/modified entities
   - Note any uncertainties or areas needing further refinement

4. **Convergence Consideration:**
   - As iterations progress, make smaller, more targeted changes
   - Focus on fine-tuning rather than major restructuring
   - Indicate when you believe the results are well-refined

Return results in this JSON structure:

{
  "entities": [...],
  "categories": [...],
  "attributes": {...},
  "iteration_changes": ["change1", "change2"],
  "refinement_focus": "what this iteration focused on",
  "confidence_assessment": "overall confidence in current results",
  "suggested_next_focus": "what to focus on in next iteration (if any)",
  "summary": "updated comprehensive summary"
}

Be thoughtful and incremental. Quality over quantity of changes."""

    def _create_refinement_request(self,
                                   current_content: Dict[str, Any],
                                   iteration: int,
                                   image_url: Optional[str]) -> str:
        """Create a refinement request for the current iteration."""

        import json

        # Create focused request based on iteration
        if iteration == 0:
            focus_prompt = """This is the initial refinement iteration.

Please analyze the extraction results and improve:
- Entity accuracy and completeness
- Category appropriateness and hierarchy
- Attribute organization and relevance

Focus on the most obvious improvements and quality issues."""

        elif iteration == 1:
            focus_prompt = """This is the second refinement iteration.

Building on the previous improvements, now focus on:
- Entity relationships and groupings
- Attribute refinement and consolidation
- Category hierarchy optimization
- Confidence score adjustments"""

        else:
            focus_prompt = f"""This is iteration {iteration + 1} of refinement.

Focus on fine-tuning and final optimizations:
- Minor entity adjustments
- Confidence fine-tuning
- Final attribute cleanup
- Summary enhancement

Make smaller, targeted improvements as we approach convergence."""

        # Format current content
        content_json = json.dumps(current_content, indent=2, ensure_ascii=False)

        request = f"""{focus_prompt}

Current extraction results to refine:

{content_json}

Please provide your refined version with clear documentation of changes made."""

        # Add image context if available
        if image_url and iteration == 0:
            request += f"\n\nOriginal image URL for context: {image_url}"

        return request

    def _structure_conversation_result(self,
                                       refined_data: Dict[str, Any],
                                       original_content: Dict[str, Any],
                                       iteration: int,
                                       model: str) -> Dict[str, Any]:
        """Structure the conversation refinement result."""

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
            "iteration_number": iteration + 1,
            "original_source": original_content.get("extracted_by", "unknown")
        }

        # Structure entities
        if "entities" in refined_data:
            result["entities"] = self._structure_conversation_entities(refined_data["entities"])

        # Structure categories
        if "categories" in refined_data:
            result["categories"] = self._structure_conversation_categories(refined_data["categories"])

        # Structure attributes
        if "attributes" in refined_data:
            result["attributes"] = self._structure_conversation_attributes(refined_data["attributes"])

        # Extract conversation metadata
        result["iteration_changes"] = refined_data.get("iteration_changes", [])
        result["refinement_focus"] = str(refined_data.get("refinement_focus", ""))
        result["confidence_assessment"] = str(refined_data.get("confidence_assessment", ""))
        result["suggested_next_focus"] = str(refined_data.get("suggested_next_focus", ""))
        result["summary"] = str(refined_data.get("summary", ""))

        return result

    def _structure_conversation_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure entities from conversation refinement."""
        structured_entities = []

        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                structured_entity = {
                    "name": str(entity["name"]),
                    "type": str(entity.get("type", "unknown")),
                    "confidence": float(entity.get("confidence", 0.8)),
                    "context": str(entity.get("context", "")),
                    "attributes": entity.get("attributes", []),
                    "relationships": entity.get("relationships", []),
                    "iteration_notes": str(entity.get("iteration_notes", ""))
                }
                structured_entities.append(structured_entity)

        return structured_entities

    def _structure_conversation_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Structure categories from conversation refinement."""
        structured_categories = []

        for category in categories:
            if isinstance(category, dict) and "name" in category:
                structured_category = {
                    "name": str(category["name"]),
                    "level": str(category.get("level", "main")),
                    "confidence": float(category.get("confidence", 0.8)),
                    "reasoning": str(category.get("reasoning", "")),
                    "entities": category.get("entities", []),
                    "iteration_notes": str(category.get("iteration_notes", ""))
                }
                structured_categories.append(structured_category)

        return structured_categories

    def _structure_conversation_attributes(self, attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Structure attributes from conversation refinement."""
        structured_attrs = {}

        for attr_key, attr_values in attributes.items():
            if isinstance(attr_values, list):
                structured_attrs[attr_key] = [str(v) for v in attr_values if v]
            elif attr_values:
                structured_attrs[attr_key] = [str(attr_values)]

        return structured_attrs

    def _calculate_convergence(self, previous_content: Dict[str, Any], current_content: Dict[str, Any]) -> float:
        """Calculate convergence score between two iterations."""

        # Compare entities
        prev_entities = set()
        curr_entities = set()

        for entity in previous_content.get("entities", []):
            if isinstance(entity, dict) and "name" in entity:
                prev_entities.add(f"{entity['name']}_{entity.get('type', 'unknown')}")

        for entity in current_content.get("entities", []):
            if isinstance(entity, dict) and "name" in entity:
                curr_entities.add(f"{entity['name']}_{entity.get('type', 'unknown')}")

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
        prev_categories = set(cat.get("name", "") for cat in previous_content.get("categories", []))
        curr_categories = set(cat.get("name", "") for cat in current_content.get("categories", []))

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

    def _log_conversation_statistics(self, refined_result: Dict[str, Any],
                                     conversation_history: List[Dict[str, Any]]) -> None:
        """Log statistics about the conversation refinement."""
        convergence_info = refined_result.get("convergence_info", {})

        self.logger.info("Conversation refinement completed:")
        self.logger.info(f"  Iterations used: {convergence_info.get('iterations_used', 0)}")
        self.logger.info(f"  Converged early: {convergence_info.get('converged_early', False)}")

        if conversation_history:
            final_entities = len(refined_result.get("entities", []))
            final_categories = len(refined_result.get("categories", []))

            self.logger.info(f"  Final entities: {final_entities}")
            self.logger.info(f"  Final categories: {final_categories}")

            # Log confidence improvements
            total_confidence_change = sum(
                hist.get("confidence_improvement", 0)
                for hist in conversation_history
                if "confidence_improvement" in hist
            )

            if total_confidence_change != 0:
                self.logger.info(f"  Total confidence change: {total_confidence_change:+.3f}")
