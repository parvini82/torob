"""
Graph builder for creating and managing LangGraph workflows.

This module provides utilities for building complex workflows by connecting
nodes in various patterns (sequential, parallel, conditional).
"""

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph
from .base_node import BaseNode


class GraphBuilder:
    """
    Builder class for creating LangGraph workflows with modular nodes.

    Supports various connection patterns:
    - Sequential: A -> B -> C
    - Parallel: A -> [B, C] -> D
    - Conditional: A -> B (if condition) else C
    """

    def __init__(self, name: str = "workflow"):
        """
        Initialize the graph builder.

        Args:
            name: Name identifier for the workflow
        """
        self.name = name
        self.workflow = StateGraph(dict)
        self.nodes: Dict[str, BaseNode] = {}
        self.entry_point: Optional[str] = None
        self.finish_point: Optional[str] = None

    def add_node(self, node: BaseNode) -> "GraphBuilder":
        """
        Add a node to the workflow.

        Args:
            node: Node instance to add

        Returns:
            Self for method chaining
        """
        self.nodes[node.name] = node
        # Wrap the node's run method for LangGraph compatibility
        self.workflow.add_node(node.name, self._create_node_wrapper(node))
        return self

    def add_sequential_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        """
        Add a sequential edge between two nodes.

        Args:
            from_node: Source node name
            to_node: Target node name

        Returns:
            Self for method chaining
        """
        self.workflow.add_edge(from_node, to_node)
        return self

    def add_parallel_edges(self, from_node: str, to_nodes: List[str]) -> "GraphBuilder":
        """
        Add parallel edges from one node to multiple nodes.

        Args:
            from_node: Source node name
            to_nodes: List of target node names

        Returns:
            Self for method chaining
        """
        for to_node in to_nodes:
            self.workflow.add_edge(from_node, to_node)
        return self

    def set_entry_point(self, node_name: str) -> "GraphBuilder":
        """
        Set the workflow entry point.

        Args:
            node_name: Name of the entry node

        Returns:
            Self for method chaining
        """
        self.entry_point = node_name
        self.workflow.set_entry_point(node_name)
        return self

    def set_finish_point(self, node_name: str) -> "GraphBuilder":
        """
        Set the workflow finish point.

        Args:
            node_name: Name of the finish node

        Returns:
            Self for method chaining
        """
        self.finish_point = node_name
        self.workflow.set_finish_point(node_name)
        return self

    def build(self) -> StateGraph:
        """
        Build and compile the workflow graph.

        Returns:
            Compiled StateGraph ready for execution

        Raises:
            ValueError: If entry or finish points are not set
        """
        if not self.entry_point:
            raise ValueError("Entry point must be set before building")
        if not self.finish_point:
            raise ValueError("Finish point must be set before building")

        return self.workflow.compile()

    def _create_node_wrapper(self, node: BaseNode):
        """
        Create a wrapper function for LangGraph compatibility.

        Args:
            node: Node instance to wrap

        Returns:
            Wrapped function compatible with LangGraph
        """

        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                node.log_execution(
                    f"Starting execution with state keys: {list(state.keys())}"
                )
                result = node.run(state)
                node.log_execution(
                    f"Completed execution, output keys: {list(result.keys())}"
                )
                return result
            except Exception as e:
                node.log_execution(f"Error during execution: {str(e)}", "error")
                raise

        return wrapper

    def get_node_info(self) -> Dict[str, str]:
        """
        Get information about all nodes in the workflow.

        Returns:
            Dictionary mapping node names to their class names
        """
        return {name: node.__class__.__name__ for name, node in self.nodes.items()}
