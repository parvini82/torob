import base64
from typing import Any, Dict

from langgraph.graph import StateGraph

from .image_to_tags import image_to_tags_node
from .merge_results import merge_results_node
from .translate_tags import translate_tags_node


def _compile_workflow() -> StateGraph:
    workflow: StateGraph = StateGraph(dict)
    workflow.add_node("image_to_tags", image_to_tags_node)
    workflow.add_node("translate_tags", translate_tags_node)
    workflow.add_node("merge_results", merge_results_node)

    workflow.add_edge("image_to_tags", "translate_tags")
    workflow.add_edge("translate_tags", "merge_results")

    workflow.set_entry_point("image_to_tags")
    workflow.set_finish_point("merge_results")
    return workflow.compile()


_workflow = _compile_workflow()


def run_langgraph_on_bytes(image_bytes: bytes) -> Dict[str, Any]:
    # Encode to data URI for OpenRouter image parts
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"

    initial_state = {"image_url": data_uri}
    final_state = _workflow.invoke(initial_state)

    # Return both English and Persian if present
    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }


def run_langgraph_on_url(image_url: str) -> Dict[str, Any]:
    initial_state = {"image_url": image_url}
    final_state = _workflow.invoke(initial_state)
    return {
        "english": final_state.get("image_tags_en", {}),
        "persian": final_state.get("final_output", {}),
    }
