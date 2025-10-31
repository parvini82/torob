import base64
from typing import Annotated, TypedDict, Any, Dict
import operator
from langgraph.graph import StateGraph, END
from .image_to_tags import image_to_tags_node
from .merge_results import merge_results_node
from .serpapi_search import serpapi_search_node
from .translate_tags import translate_tags_node
from .config import get_vision_model, get_translate_model, should_use_serpapi


def last(a, b):
    return b


class WorkflowState(TypedDict, total=False):
    image_url: Annotated[str, last]
    image_tags_en: Annotated[Dict[str, Any], operator.or_]
    serpapi_results: Annotated[Dict[str, Any], operator.or_]
    merged_data: Annotated[Dict[str, Any], operator.or_]
    image_tags_fa: Annotated[Dict[str, Any], operator.or_]
    final_output: Annotated[Dict[str, Any], operator.or_]
    mode: Annotated[str, last]  # Track the mode
    vision_model: Annotated[str, last]
    translate_model: Annotated[str, last]
    use_serpapi: Annotated[bool, last]


def fan_out_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pass-through node to start parallel execution branches."""
    return state


def merge_for_translate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge outputs from `image_to_tags` and `serpapi_search` into a single key
    that translate node will consume. Keep other state keys intact.
    """
    merged_data = {
        "image_tags_en": state.get("image_tags_en", {}),
        "serpapi_results": state.get("serpapi_results", {}),
    }
    return {**state, "merged_data": merged_data}


def should_use_serpapi_node(state: Dict[str, Any]) -> str:
    """Conditional edge: determine if serpapi should be used"""
    if state.get("use_serpapi", False):
        return "serpapi_search"
    else:
        return "merge_for_translate"


def _compile_workflow(mode: str = "fast") -> StateGraph:
    workflow: StateGraph = StateGraph(WorkflowState)

    use_serpapi = should_use_serpapi(mode)

    # Nodes
    workflow.add_node("fan_out", fan_out_node)
    workflow.add_node("image_to_tags", image_to_tags_node)
    workflow.add_node("merge_for_translate", merge_for_translate_node)
    workflow.add_node("translate_tags", translate_tags_node)
    workflow.add_node("merge_results", merge_results_node)

    # Set entry point
    workflow.set_entry_point("fan_out")

    # Always go from fan_out to image_to_tags
    workflow.add_edge("fan_out", "image_to_tags")

    if use_serpapi:
        # Add serpapi node and edges
        workflow.add_node("serpapi_search", serpapi_search_node)
        workflow.add_edge("fan_out", "serpapi_search")
        workflow.add_edge("image_to_tags", "merge_for_translate")
        workflow.add_edge("serpapi_search", "merge_for_translate")
    else:
        # Skip serpapi, go directly from image_to_tags to merge_for_translate
        workflow.add_edge("image_to_tags", "merge_for_translate")

    # Continue sequence
    workflow.add_edge("merge_for_translate", "translate_tags")
    workflow.add_edge("translate_tags", "merge_results")

    workflow.set_finish_point("merge_results")

    return workflow.compile()


def run_langgraph_on_bytes(image_bytes: bytes, mode: str = "fast") -> Dict[str, Any]:
    """Convenience entry: image bytes → data URI → invoke graph."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"

    # Get configuration based on mode
    vision_model = get_vision_model(mode)
    translate_model = get_translate_model(mode)
    use_serpapi_flag = should_use_serpapi(mode)

    # Compile workflow based on mode
    workflow = _compile_workflow(mode)

    initial_state = {
        "image_url": data_uri,
        "mode": mode,
        "vision_model": vision_model,
        "translate_model": translate_model,
        "use_serpapi": use_serpapi_flag
    }

    final_state = workflow.invoke(initial_state)

    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }


def run_langgraph_on_url(image_url: str, mode: str = "fast") -> Dict[str, Any]:
    """Convenience entry: image URL → invoke graph."""
    # Get configuration based on mode
    vision_model = get_vision_model(mode)
    translate_model = get_translate_model(mode)
    use_serpapi_flag = should_use_serpapi(mode)

    # Compile workflow based on mode
    workflow = _compile_workflow(mode)

    initial_state = {
        "image_url": image_url,
        "mode": mode,
        "vision_model": vision_model,
        "translate_model": translate_model,
        "use_serpapi": use_serpapi_flag
    }

    final_state = workflow.invoke(initial_state)

    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }
