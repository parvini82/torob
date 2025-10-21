from typing import Dict, Any


def merge_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    image_tags_fa = state.get("image_tags_fa")
    if not image_tags_fa:
        raise ValueError("merge_results_node: 'image_tags_fa' is missing in state")

    return {"final_output": image_tags_fa}

