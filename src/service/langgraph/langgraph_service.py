import base64
from typing import Annotated, TypedDict, Any, Dict
import operator
from langgraph.graph import StateGraph

from .image_to_tags import image_to_tags_node
from .merge_results import merge_results_node
from .serpapi_search import serpapi_search_node
from .translate_tags import translate_tags_node

def last(a, b):
    return b

class WorkflowState(TypedDict, total=False):
    image_url: Annotated[str, last]   # ← changed line
    image_tags_en: Annotated[Dict[str, Any], operator.or_]
    serpapi_results: Annotated[Dict[str, Any], operator.or_]
    merged_data: Annotated[Dict[str, Any], operator.or_]
    image_tags_fa: Annotated[Dict[str, Any], operator.or_]
    final_output: Annotated[Dict[str, Any], operator.or_]


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


def _compile_workflow() -> StateGraph:
    workflow: StateGraph = StateGraph(WorkflowState)

    # Nodes
    workflow.add_node("fan_out", fan_out_node)
    workflow.add_node("image_to_tags", image_to_tags_node)
    workflow.add_node("serpapi_search", serpapi_search_node)
    workflow.add_node("merge_for_translate", merge_for_translate_node)
    workflow.add_node("translate_tags", translate_tags_node)
    workflow.add_node("merge_results", merge_results_node)

    # Parallel branches
    workflow.add_edge("fan_out", "image_to_tags")
    workflow.add_edge("fan_out", "serpapi_search")

    # Join into merge_for_translate
    workflow.add_edge("image_to_tags", "merge_for_translate")
    workflow.add_edge("serpapi_search", "merge_for_translate")

    # Continue sequence
    workflow.add_edge("merge_for_translate", "translate_tags")
    workflow.add_edge("translate_tags", "merge_results")

    workflow.set_entry_point("fan_out")
    workflow.set_finish_point("merge_results")
    return workflow.compile()


_workflow = _compile_workflow()


def run_langgraph_on_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """Convenience entry: image bytes → data URI → invoke graph."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"

    initial_state = {"image_url": data_uri}
    final_state = _workflow.invoke(initial_state)
    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }


def run_langgraph_on_url(image_url: str) -> Dict[str, Any]:
    """Convenience entry: image URL → invoke graph."""
    initial_state = {"image_url": image_url}
    final_state = _workflow.invoke(initial_state)
    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }
