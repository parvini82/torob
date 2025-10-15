from typing import Dict, Any


def merge_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node:
    Input state: {'image_tags_fa': dict}
    Output state: {'final_output': dict}
    """
    image_tags_fa = state.get("image_tags_fa")
    if not image_tags_fa:
        raise ValueError("merge_results_node: 'image_tags_fa' is missing in state")

    # Keep only the Persian translation as the final result
    return {"final_output": image_tags_fa}
