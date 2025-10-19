"""Result merging and finalization node for the LangGraph pipeline.

This module handles the final stage of the LangGraph workflow where processed
results from previous nodes are consolidated, validated, and formatted for
the final output. It serves as the termination point of the pipeline.
"""

from typing import Dict, Any, Optional


class ResultMergeError(Exception):
    """Custom exception for result merging errors."""
    pass


def validate_merge_input(state: Dict[str, Any]) -> None:
    """Validate input state for result merging.
    
    Args:
        state: Current workflow state
        
    Raises:
        ResultMergeError: If required input is missing or invalid
    """
    if not isinstance(state, dict):
        raise ResultMergeError("State must be a dictionary")
    
    # Check for required Persian tags
    image_tags_fa = state.get("image_tags_fa")
    if image_tags_fa is None:
        raise ResultMergeError("'image_tags_fa' is required but missing in state")
    
    if not isinstance(image_tags_fa, dict):
        raise ResultMergeError("'image_tags_fa' must be a dictionary")


def merge_processing_metadata(state: Dict[str, Any]) -> Dict[str, Any]:
    """Collect and merge metadata from all processing stages.
    
    Args:
        state: Complete workflow state
        
    Returns:
        Dict[str, Any]: Consolidated processing metadata
    """
    metadata = {
        "pipeline_completed": True,
        "stages_processed": [],
        "total_processing_time": None,  # Could be calculated if timestamps were tracked
        "errors_encountered": []
    }
    
    # Collect metadata from analysis stage
    analysis_meta = state.get("analysis_metadata", {})
    if analysis_meta:
        metadata["stages_processed"].append("image_analysis")
        metadata["image_analysis"] = analysis_meta
        
        if not analysis_meta.get("analysis_success", True):
            metadata["errors_encountered"].append({
                "stage": "image_analysis",
                "error": analysis_meta.get("error_message", "Unknown error")
            })
    
    # Collect metadata from translation stage
    translation_meta = state.get("translation_metadata", {})
    if translation_meta:
        metadata["stages_processed"].append("translation")
        metadata["translation"] = translation_meta
        
        if not translation_meta.get("translation_success", True):
            metadata["errors_encountered"].append({
                "stage": "translation",
                "error": translation_meta.get("error_message", "Unknown error")
            })
    
    # Overall success status
    metadata["overall_success"] = len(metadata["errors_encountered"]) == 0
    
    return metadata


def format_final_output(image_tags_fa: Dict[str, Any], 
                       state: Dict[str, Any]) -> Dict[str, Any]:
    """Format the final output with proper structure and metadata.
    
    Args:
        image_tags_fa: Persian translated tags
        state: Complete workflow state
        
    Returns:
        Dict[str, Any]: Formatted final output
    """
    # Start with the Persian tags as the base
    final_output = dict(image_tags_fa)
    
    # Add processing metadata
    processing_metadata = merge_processing_metadata(state)
    final_output["_metadata"] = processing_metadata
    
    # Add source information for traceability
    final_output["_source_info"] = {
        "original_image_url": state.get("image_url", ""),
        "processing_pipeline": "torob-langgraph-v1",
        "stages_completed": processing_metadata["stages_processed"]
    }
    
    # Include raw responses for debugging if available
    if state.get("raw_response") or state.get("translation_raw"):
        debug_info = {}
        if state.get("raw_response"):
            debug_info["analysis_raw"] = state["raw_response"]
        if state.get("translation_raw"):
            debug_info["translation_raw"] = state["translation_raw"]
        
        final_output["_debug"] = debug_info
    
    # Handle translation fallbacks or errors
    if "translation_error" in image_tags_fa:
        final_output["_warnings"] = [{
            "type": "translation_fallback",
            "message": "Translation failed, using fallback or original tags",
            "details": image_tags_fa.get("translation_error")
        }]
    
    if "translation_warning" in image_tags_fa:
        if "_warnings" not in final_output:
            final_output["_warnings"] = []
        final_output["_warnings"].append({
            "type": "translation_incomplete",
            "message": image_tags_fa.get("translation_warning")
        })
    
    return final_output


def validate_final_output(final_output: Dict[str, Any]) -> None:
    """Validate the final output structure and content.
    
    Args:
        final_output: The formatted final output
        
    Raises:
        ResultMergeError: If final output is invalid
    """
    if not isinstance(final_output, dict):
        raise ResultMergeError("Final output must be a dictionary")
    
    # Check for essential content
    has_entities = "entities" in final_output and isinstance(final_output["entities"], list)
    has_fallback = "fallback_tags" in final_output
    
    if not (has_entities or has_fallback):
        raise ResultMergeError(
            "Final output must contain either 'entities' or 'fallback_tags'"
        )
    
    # Validate metadata if present
    if "_metadata" in final_output:
        metadata = final_output["_metadata"]
        if not isinstance(metadata, dict):
            raise ResultMergeError("Metadata must be a dictionary")
        
        if "pipeline_completed" not in metadata:
            raise ResultMergeError("Metadata must indicate pipeline completion status")


def merge_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for merging and finalizing pipeline results.
    
    This function represents the final processing stage in the workflow,
    where all previous results are consolidated into the final output format.
    
    Args:
        state: Complete workflow state from previous nodes
        
    Returns:
        Dict[str, Any]: Final state with consolidated output
        
    Raises:
        ResultMergeError: If result merging fails
    
    State Input:
        - image_tags_fa (dict): Persian translated tags from translation node
        - analysis_metadata (dict, optional): Metadata from image analysis
        - translation_metadata (dict, optional): Metadata from translation
        - raw_response (str, optional): Raw analysis response
        - translation_raw (str, optional): Raw translation response
        - image_url (str, optional): Original image URL for traceability
        
    State Output:
        - final_output (dict): Consolidated and formatted final results
        - merge_metadata (dict): Information about the merging process
    """
    try:
        # Validate input state
        validate_merge_input(state)
        
        # Extract Persian tags from state
        image_tags_fa = state["image_tags_fa"]
        
        # Format the final output with metadata and validation
        final_output = format_final_output(image_tags_fa, state)
        
        # Validate the final output
        validate_final_output(final_output)
        
        # Prepare merge metadata
        merge_metadata = {
            "merge_success": True,
            "output_size_bytes": len(str(final_output)),
            "has_entities": "entities" in final_output,
            "has_warnings": "_warnings" in final_output,
            "has_debug_info": "_debug" in final_output,
            "entity_count": len(final_output.get("entities", [])),
        }
        
        # Return final state with consolidated results
        return {
            "final_output": final_output,
            "merge_metadata": merge_metadata,
            # Preserve original state for potential debugging
            "_original_state_keys": list(state.keys())
        }
        
    except Exception as e:
        error_message = str(e)
        
        # Create minimal fallback output
        fallback_output = {
            "error": "Pipeline merge failed",
            "error_details": error_message,
            "fallback_data": state.get("image_tags_fa", {}),
            "_metadata": {
                "pipeline_completed": False,
                "merge_error": error_message,
                "error_type": type(e).__name__
            }
        }
        
        # Create error state
        error_state = {
            "final_output": fallback_output,
            "merge_metadata": {
                "merge_success": False,
                "error_message": error_message,
                "error_type": type(e).__name__
            },
            "_original_state_keys": list(state.keys())
        }
        
        # For critical errors, re-raise; for others, return fallback
        if isinstance(e, ResultMergeError):
            # Log error but continue with fallback
            print(f"Result merge warning: {error_message}")
            return error_state
        else:
            # Re-raise unexpected errors
            raise ResultMergeError(
                f"Result merge node failed: {error_message}"
            ) from e


# Simplified legacy version for backward compatibility
def simple_merge_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simplified version of merge_results_node for backward compatibility.
    
    Args:
        state: Workflow state
        
    Returns:
        Dict[str, Any]: Simple final output structure
        
    Note:
        This function is deprecated. Use merge_results_node() for full functionality.
    """
    image_tags_fa = state.get("image_tags_fa")
    if not image_tags_fa:
        raise ValueError("merge_results_node: 'image_tags_fa' is missing in state")
    
    return {"final_output": image_tags_fa}
