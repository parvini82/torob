"""LangGraph service orchestrator for image processing pipeline.

This module defines and manages the complete workflow for processing product images
through a multi-step pipeline including image analysis, translation, and result merging.
It uses LangGraph to create a state-based workflow that processes images through
different AI models to generate comprehensive product tags.
"""

import base64
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from .image_to_tags import image_to_tags_node
from .translate_tags import translate_tags_node
from .merge_results import merge_results_node
from .config import get_config_summary


class LangGraphError(Exception):
    """Custom exception for LangGraph workflow errors."""
    pass


class ImageProcessingPipeline:
    """Manages the complete image processing workflow using LangGraph.
    
    This class encapsulates the workflow definition and execution logic
    for processing product images through multiple AI processing stages.
    """
    
    def __init__(self):
        """Initialize the image processing pipeline."""
        self._workflow = None
        self._compile_workflow()
    
    def _compile_workflow(self) -> None:
        """Compile the LangGraph workflow with all processing nodes.
        
        Creates a state-based workflow that processes images through:
        1. image_to_tags: Initial image analysis and tag extraction
        2. translate_tags: Translation of tags to target language
        3. merge_results: Combining and formatting final results
        """
        try:
            # Initialize the workflow graph with dict state
            workflow = StateGraph(dict)
            
            # Add processing nodes to the workflow
            workflow.add_node("image_to_tags", image_to_tags_node)
            workflow.add_node("translate_tags", translate_tags_node)
            workflow.add_node("merge_results", merge_results_node)
            
            # Define the processing flow between nodes
            workflow.add_edge("image_to_tags", "translate_tags")
            workflow.add_edge("translate_tags", "merge_results")
            
            # Set workflow entry and exit points
            workflow.set_entry_point("image_to_tags")
            workflow.set_finish_point("merge_results")
            
            # Compile the workflow for execution
            self._workflow = workflow.compile()
            
        except Exception as e:
            raise LangGraphError(f"Failed to compile workflow: {str(e)}") from e

    # _validate_image_url
    def _validate_image_url(self, image_url: str) -> None:
        if not image_url or not isinstance(image_url, str):
            raise LangGraphError("Image URL must be a non-empty string")
        if not image_url.startswith(("http://", "https://", "data:")):
            raise LangGraphError(
                "Image URL must be either a valid HTTP/HTTPS URL or a data URI"
            )

        # Check if it's a data URI or regular URL
        is_data_uri = image_url.startswith("data:")
        is_http_url = image_url.startswith(("http://", "https://"))
        
        if not (is_data_uri or is_http_url):
            raise LangGraphError(
                "Image URL must be either a valid HTTP/HTTPS URL or a data URI"
            )
    
    def _prepare_initial_state(self, image_url: str) -> Dict[str, Any]:
        """Prepare the initial state for workflow execution.
        
        Args:
            image_url: URL or data URI of the image
            
        Returns:
            Dict[str, Any]: Initial state dictionary for the workflow
        """
        return {
            "image_url": image_url,
            "processing_metadata": {
                "pipeline_version": "1.0.0",
                "config_summary": get_config_summary()
            }
        }
    
    def _format_results(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate workflow results.
        
        Args:
            final_state: Final state from workflow execution
            
        Returns:
            Dict[str, Any]: Formatted results with English and Persian outputs
        """
        # Extract results from final state
        english_tags = final_state.get("image_tags_en", {})
        persian_tags = final_state.get("final_output", {})
        
        # Prepare formatted response
        formatted_results = {
            "english": english_tags,
            "persian": persian_tags,
            "metadata": {
                "processing_success": True,
                "workflow_state_keys": list(final_state.keys()),
                "has_english_results": bool(english_tags),
                "has_persian_results": bool(persian_tags)
            }
        }
        
        # Add error information if results are empty
        if not english_tags and not persian_tags:
            formatted_results["metadata"]["processing_success"] = False
            formatted_results["metadata"]["error"] = "No results generated from image processing"
        
        return formatted_results
    
    def process_image_url(self, image_url: str) -> Dict[str, Any]:
        """Process an image from a URL through the complete pipeline.
        
        Args:
            image_url: HTTP/HTTPS URL of the image to process
            
        Returns:
            Dict[str, Any]: Processing results with English and Persian tags
            
        Raises:
            LangGraphError: If processing fails at any stage
        """
        try:
            # Validate input
            self._validate_image_url(image_url)
            
            # Prepare workflow state
            initial_state = self._prepare_initial_state(image_url)
            
            # Execute the workflow
            final_state = self._workflow.invoke(initial_state)
            
            # Format and return results
            return self._format_results(final_state)
            
        except Exception as e:
            if isinstance(e, LangGraphError):
                raise
            raise LangGraphError(f"Image processing failed: {str(e)}") from e
    
    def process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Process raw image bytes through the complete pipeline.
        
        Args:
            image_bytes: Raw image data as bytes
            
        Returns:
            Dict[str, Any]: Processing results with English and Persian tags
            
        Raises:
            LangGraphError: If processing fails at any stage
        """
        try:
            # Validate input
            if not image_bytes or not isinstance(image_bytes, bytes):
                raise LangGraphError("Image bytes must be non-empty bytes object")
            
            # Convert bytes to data URI
            b64_encoded = base64.b64encode(image_bytes).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{b64_encoded}"
            
            # Process using URL method
            return self.process_image_url(data_uri)
            
        except Exception as e:
            if isinstance(e, LangGraphError):
                raise
            raise LangGraphError(f"Image bytes processing failed: {str(e)}") from e
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the current workflow configuration.
        
        Returns:
            Dict[str, Any]: Workflow configuration and status information
        """
        return {
            "workflow_compiled": self._workflow is not None,
            "node_count": 3,  # image_to_tags, translate_tags, merge_results
            "nodes": ["image_to_tags", "translate_tags", "merge_results"],
            "edges": [
                ("image_to_tags", "translate_tags"),
                ("translate_tags", "merge_results")
            ],
            "entry_point": "image_to_tags",
            "finish_point": "merge_results",
            "config": get_config_summary()
        }


# Global pipeline instance
_pipeline_instance: Optional[ImageProcessingPipeline] = None


def get_pipeline() -> ImageProcessingPipeline:
    """Get or create the global pipeline instance.
    
    Returns:
        ImageProcessingPipeline: Singleton pipeline instance
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ImageProcessingPipeline()
    return _pipeline_instance


# Backward compatibility functions
def run_langgraph_on_url(image_url: str) -> Dict[str, Any]:
    """Process an image URL through the LangGraph workflow (legacy interface).
    
    Args:
        image_url: URL of the image to process
        
    Returns:
        Dict[str, Any]: Processing results with English and Persian tags
        
    Note:
        This function maintains backward compatibility with the existing API.
        New code should use ImageProcessingPipeline.process_image_url() directly.
    """
    pipeline = get_pipeline()
    return pipeline.process_image_url(image_url)


def run_langgraph_on_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """Process image bytes through the LangGraph workflow (legacy interface).
    
    Args:
        image_bytes: Raw image data as bytes
        
    Returns:
        Dict[str, Any]: Processing results with English and Persian tags
        
    Note:
        This function maintains backward compatibility with the existing API.
        New code should use ImageProcessingPipeline.process_image_bytes() directly.
    """
    pipeline = get_pipeline()
    return pipeline.process_image_bytes(image_bytes)


# Legacy workflow compilation (for compatibility)
def _compile_workflow() -> StateGraph:
    """Legacy workflow compilation function (deprecated).
    
    Returns:
        StateGraph: Compiled workflow graph
        
    Note:
        This function is deprecated. Use ImageProcessingPipeline class instead.
    """
    pipeline = get_pipeline()
    return pipeline._workflow
