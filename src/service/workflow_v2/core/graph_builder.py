"""
Graph builder for workflow orchestration.

Provides utilities for constructing and configuring LangGraph StateGraph
instances with proper node registration and edge configuration.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from langgraph.graph import StateGraph

from .base_node import BaseNode
from .state_manager import StateManager


class GraphBuilder:
    """
    Builder class for constructing workflow graphs.

    Simplifies the process of creating LangGraph StateGraph instances
    with proper node registration, edge configuration, and entry point setup.
    """

    def __init__(self, name: str = "WorkflowGraph"):
        """
        Initialize the graph builder.

        Args:
            name: Name for the graph (used in logging)
        """
        self.name = name
        self.graph = StateGraph(StateManager)
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: List[tuple] = []
        self.conditional_edges: List[dict] = []
        self.entry_point: Optional[str] = None

        self.logger = logging.getLogger(f"{__name__}.GraphBuilder")
        self.logger.info(f"Initialized GraphBuilder: {name}")

    def add_node(self, name: str, node: BaseNode) -> 'GraphBuilder':
        """
        Add a node to the graph.

        Args:
            name: Unique name for the node in the graph
            node: BaseNode instance to add

        Returns:
            Self for method chaining

        Raises:
            ValueError: If node name already exists
        """
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists in graph")

        if not isinstance(node, BaseNode):
            raise ValueError(f"Node must be an instance of BaseNode, got {type(node)}")

        # Wrap node execution for graph compatibility
        def node_wrapper(state: StateManager) -> StateManager:
            """Wrapper to make BaseNode compatible with StateGraph."""
            # Get full state as dictionary
            state_dict = state.get_full_state()

            # Execute node
            result_dict = node.execute(state_dict)

            # Update state manager with results
            state.update_state(result_dict)
            return state

        self.graph.add_node(name, node_wrapper)
        self.nodes[name] = node

        self.logger.info(f"Added node '{name}' ({node.__class__.__name__})")
        return self

    def add_edge(self, from_node: str, to_node: str) -> 'GraphBuilder':
        """
        Add a direct edge between two nodes.

        Args:
            from_node: Source node name
            to_node: Target node name

        Returns:
            Self for method chaining
        """
        self._validate_node_exists(from_node)
        self._validate_node_exists(to_node)

        self.graph.add_edge(from_node, to_node)
        self.edges.append((from_node, to_node))

        self.logger.info(f"Added edge: {from_node} -> {to_node}")
        return self

    def add_conditional_edge(
        self,
        from_node: str,
        condition_func: Callable[[StateManager], str],
        edge_map: Dict[str, str]
    ) -> 'GraphBuilder':
        """
        Add a conditional edge with branching logic.

        Args:
            from_node: Source node name
            condition_func: Function that returns the condition key
            edge_map: Map from condition keys to target node names

        Returns:
            Self for method chaining
        """
        self._validate_node_exists(from_node)

        for target_node in edge_map.values():
            self._validate_node_exists(target_node)

        self.graph.add_conditional_edges(from_node, condition_func, edge_map)

        self.conditional_edges.append({
            'from_node': from_node,
            'condition_func': condition_func,
            'edge_map': edge_map
        })

        self.logger.info(f"Added conditional edge from '{from_node}' with {len(edge_map)} branches")
        return self

    def set_entry_point(self, node_name: str) -> 'GraphBuilder':
        """
        Set the entry point for graph execution.

        Args:
            node_name: Name of the node to start execution from

        Returns:
            Self for method chaining
        """
        self._validate_node_exists(node_name)

        self.entry_point = node_name
        self.graph.set_entry_point(node_name)

        self.logger.info(f"Set entry point: {node_name}")
        return self

    def build(self) -> StateGraph:
        """
        Build and return the configured graph.

        Returns:
            Configured StateGraph instance

        Raises:
            ValueError: If entry point is not set or graph is invalid
        """
        if not self.entry_point:
            raise ValueError("Entry point must be set before building graph")

        if not self.nodes:
            raise ValueError("Graph must have at least one node")

        # Build the graph
        built_graph = self.graph.compile()

        self.logger.info(f"Successfully built graph '{self.name}' with:")
        self.logger.info(f"  - Nodes: {len(self.nodes)}")
        self.logger.info(f"  - Direct edges: {len(self.edges)}")
        self.logger.info(f"  - Conditional edges: {len(self.conditional_edges)}")
        self.logger.info(f"  - Entry point: {self.entry_point}")

        return built_graph

    def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about all nodes in the graph.

        Returns:
            Dictionary with node information
        """
        return {
            name: {
                'class': node.__class__.__name__,
                'node_name': node.node_name
            }
            for name, node in self.nodes.items()
        }

    def _validate_node_exists(self, node_name: str) -> None:
        """Validate that a node exists in the graph."""
        if node_name not in self.nodes:
            available_nodes = list(self.nodes.keys())
            raise ValueError(
                f"Node '{node_name}' not found. Available nodes: {available_nodes}"
            )
