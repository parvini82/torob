"""
State management utilities for workflow execution.

This module provides utilities for managing and tracking state
throughout workflow execution.
"""

from typing import Any, Dict, List, Optional
import json
import logging


class StateManager:
    """
    Utility class for managing workflow state and execution tracking.
    """

    def __init__(self):
        """Initialize the state manager."""
        self.execution_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def create_initial_state(self, **kwargs) -> Dict[str, Any]:
        """
        Create initial state for workflow execution.

        Args:
            **kwargs: Initial state key-value pairs

        Returns:
            Initial state dictionary
        """
        initial_state = {
            "execution_id": self._generate_execution_id(),
            "step_count": 0,
            **kwargs
        }

        self.log_state_change("INIT", initial_state)
        return initial_state

    def log_state_change(self, step_name: str, state: Dict[str, Any]) -> None:
        """
        Log state changes during workflow execution.

        Args:
            step_name: Name of the execution step
            state: Current state
        """
        step_info = {
            "step": step_name,
            "step_count": state.get("step_count", 0),
            "execution_id": state.get("execution_id"),
            "keys": list(state.keys()),
            "timestamp": self._get_timestamp()
        }

        self.execution_history.append(step_info)
        self.logger.info(f"State update [{step_name}]: {len(state)} keys")

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of workflow execution.

        Returns:
            Execution summary with steps and timing
        """
        if not self.execution_history:
            return {"status": "no_execution", "steps": 0}

        return {
            "status": "completed",
            "steps": len(self.execution_history),
            "execution_id": self.execution_history[0].get("execution_id"),
            "start_time": self.execution_history[0].get("timestamp"),
            "end_time": self.execution_history[-1].get("timestamp"),
            "step_names": [step["step"] for step in self.execution_history]
        }

    def export_execution_log(self) -> str:
        """
        Export execution history as JSON string.

        Returns:
            JSON formatted execution history
        """
        return json.dumps(self.execution_history, indent=2, ensure_ascii=False)

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

