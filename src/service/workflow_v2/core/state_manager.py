"""
State management for workflow execution.

Provides thread-safe state operations with deep merging capabilities
and structured logging for all state changes.
"""

import copy
import logging
from typing import Dict, Any, Optional
from threading import Lock


class StateManager:
    """
    Thread-safe state manager for workflow execution.

    Handles state initialization, updates, and deep merging operations
    with comprehensive logging and error handling.
    """

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """
        Initialize the state manager.

        Args:
            initial_state: Optional initial state dictionary
        """
        self._state: Dict[str, Any] = initial_state or {}
        self._lock = Lock()
        self.logger = logging.getLogger(f"{__name__}.StateManager")

        if initial_state:
            self.logger.info(f"StateManager initialized with {len(initial_state)} keys")
        else:
            self.logger.info("StateManager initialized with empty state")

    def initialize_state(self, initial_data: Dict[str, Any]) -> None:
        """
        Initialize the state with provided data.

        Args:
            initial_data: Dictionary to initialize state with
        """
        with self._lock:
            self._state = copy.deepcopy(initial_data)
            self.logger.info(f"State initialized with keys: {list(initial_data.keys())}")

    def update_state(self, new_data: Dict[str, Any]) -> None:
        """
        Update state with new data using deep merge.

        Args:
            new_data: Dictionary with new data to merge into state
        """
        with self._lock:
            old_keys = set(self._state.keys())
            self._state = self.merge_dicts(self._state, new_data)
            new_keys = set(self._state.keys())

            added_keys = new_keys - old_keys
            modified_keys = old_keys.intersection(new_keys)

            if added_keys:
                self.logger.info(f"Added new state keys: {list(added_keys)}")
            if modified_keys:
                self.logger.debug(f"Modified existing keys: {list(modified_keys)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from state by key.

        Supports dot notation for nested access (e.g., 'caption.tags').

        Args:
            key: State key to retrieve
            default: Default value if key not found

        Returns:
            Value from state or default
        """
        with self._lock:
            if '.' in key:
                return self._get_nested(key, default)
            return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in state by key.

        Supports dot notation for nested setting (e.g., 'caption.tags').

        Args:
            key: State key to set
            value: Value to set
        """
        with self._lock:
            if '.' in key:
                self._set_nested(key, value)
            else:
                self._state[key] = value

            self.logger.debug(f"Set state key '{key}' to type {type(value).__name__}")

    def get_full_state(self) -> Dict[str, Any]:
        """
        Get a deep copy of the entire state.

        Returns:
            Deep copy of current state
        """
        with self._lock:
            return copy.deepcopy(self._state)

    def merge_dicts(self, dict_a: Dict[str, Any], dict_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform deep merge of two dictionaries.

        Args:
            dict_a: Base dictionary
            dict_b: Dictionary to merge into base

        Returns:
            New dictionary with merged contents
        """
        result = copy.deepcopy(dict_a)

        for key, value in dict_b.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                # Recursively merge nested dictionaries
                result[key] = self.merge_dicts(result[key], value)
            else:
                # Direct assignment for non-dict values or new keys
                result[key] = copy.deepcopy(value)

        return result

    def _get_nested(self, key: str, default: Any) -> Any:
        """Get nested value using dot notation."""
        keys = key.split('.')
        current = self._state

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def _set_nested(self, key: str, value: Any) -> None:
        """Set nested value using dot notation."""
        keys = key.split('.')
        current = self._state

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final key
        current[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dictionary-style assignment."""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        with self._lock:
            if '.' in key:
                try:
                    self._get_nested(key, object())  # Use unique sentinel
                    return True
                except:
                    return False
            return key in self._state

    def keys(self):
        """Get state keys."""
        with self._lock:
            return self._state.keys()

    def items(self):
        """Get state items."""
        with self._lock:
            return self._state.items()
