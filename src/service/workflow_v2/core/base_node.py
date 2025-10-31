"""
Base node class for workflow components.

Provides the foundation for all workflow nodes with standardized
execution interface, logging, and error handling.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNode(ABC):
    """
    Abstract base class for all workflow nodes.

    Defines the standard interface that all nodes must implement
    and provides common functionality for logging and error handling.
    """

    def __init__(self, node_name: str = None):
        """
        Initialize the base node.

        Args:
            node_name: Optional custom name for the node
        """
        self.node_name = node_name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.node_name}")

        self.logger.debug(f"Initialized node: {self.node_name}")

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node's main logic.

        This method must be implemented by all concrete node classes.
        It should perform the node's specific operation and return
        the updated state.

        Args:
            state: Current workflow state

        Returns:
            Updated state dictionary

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(f"Node {self.node_name} must implement run() method")

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node with logging and error handling.

        This method wraps the run() method with standardized logging
        and error handling. It should not be overridden by subclasses.

        Args:
            state: Current workflow state

        Returns:
            Updated state dictionary

        Raises:
            Exception: If node execution fails
        """
        self.logger.info(f"Starting execution of node: {self.node_name}")

        try:
            # Validate input state
            if not isinstance(state, dict):
                raise ValueError(f"State must be a dictionary, got {type(state)}")

            # Log input state summary
            self._log_input_summary(state)

            # Execute node logic
            result = self.run(state)

            # Validate output
            if not isinstance(result, dict):
                raise ValueError(f"Node {self.node_name} must return a dictionary")

            # Log output summary
            self._log_output_summary(result)

            self.logger.info(f"Successfully completed node: {self.node_name}")
            return result

        except Exception as e:
            self.logger.error(f"Error in node {self.node_name}: {str(e)}")

            # Return original state with error information
            error_state = state.copy()
            error_state.setdefault('errors', []).append({
                'node': self.node_name,
                'error': str(e),
                'error_type': type(e).__name__
            })

            return error_state

    def _log_input_summary(self, state: Dict[str, Any]) -> None:
        """Log summary of input state."""
        input_keys = list(state.keys())
        self.logger.debug(f"Input state keys: {input_keys}")

        # Log specific keys that are commonly important
        if 'image_url' in state:
            url = state['image_url']
            url_preview = url[:50] + '...' if len(url) > 50 else url
            self.logger.debug(f"Processing image: {url_preview}")

    def _log_output_summary(self, result: Dict[str, Any]) -> None:
        """Log summary of output state."""
        output_keys = list(result.keys())
        self.logger.debug(f"Output state keys: {output_keys}")

        # Log any new keys added by this node
        if hasattr(self, '_input_keys'):
            new_keys = set(output_keys) - set(self._input_keys)
            if new_keys:
                self.logger.info(f"Added new keys: {list(new_keys)}")

    def validate_required_keys(self, state: Dict[str, Any], required_keys: list) -> None:
        """
        Validate that required keys exist in state.

        Args:
            state: State dictionary to validate
            required_keys: List of required key names

        Raises:
            ValueError: If any required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in state]

        if missing_keys:
            raise ValueError(
                f"Node {self.node_name} requires keys {missing_keys}, "
                f"but they are missing from state. Available keys: {list(state.keys())}"
            )

    def get_node_config(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract node-specific configuration from state.

        Args:
            state: Current workflow state

        Returns:
            Configuration dictionary for this node
        """
        # Look for node-specific config
        node_config_key = f"{self.node_name.lower()}_config"
        if node_config_key in state:
            return state[node_config_key]

        # Fall back to global config
        return state.get('config', {})

    def __repr__(self) -> str:
        """String representation of the node."""
        return f"{self.__class__.__name__}(name='{self.node_name}')"
