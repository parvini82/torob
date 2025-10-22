from typing import Any, Dict

from image_to_tags import image_to_tags_node
from langgraph.graph import StateGraph
from merge_results import merge_results_node
from translate_tags import translate_tags_node


def create_langgraph_workflow():
    """
    Create and compile the LangGraph workflow for:
        image → english tags → persian tags → final output
    """
    # Define a StateGraph with Dict-based state
    workflow = StateGraph(Dict[str, Any])

    # Register nodes
    workflow.add_node("image_to_tags", image_to_tags_node)
    workflow.add_node("translate_tags", translate_tags_node)
    workflow.add_node("merge_results", merge_results_node)

    # Define edges (data flow between nodes)
    workflow.add_edge("image_to_tags", "translate_tags")
    workflow.add_edge("translate_tags", "merge_results")

    # Set entry and exit points
    workflow.set_entry_point("image_to_tags")
    workflow.set_finish_point("merge_results")

    # Compile and return runnable graph
    return workflow.compile()


# Create a global instance of the workflow (can be reused in endpoint)
langgraph_workflow = create_langgraph_workflow()


def run_langgraph(image_url: str) -> Dict[str, Any]:
    """
    Execute the LangGraph workflow for a given image URL.
    Returns the final Persian tags JSON.
    """
    initial_state = {"image_url": image_url}
    final_state = langgraph_workflow.invoke(initial_state)

    # Return only the final_output (Persian tags)
    return final_state.get("final_output", {})
