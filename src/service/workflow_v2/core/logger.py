"""
Centralized logging configuration for workflow system.

Provides consistent logging setup and utilities for all workflow components.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class WorkflowLogger:
    """
    Centralized logger configuration for workflow system.

    Provides standardized logging setup with configurable levels,
    formatting, and output destinations.
    """

    _instance = None
    _configured = False

    def __new__(cls):
        """Singleton pattern to ensure single logger configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the workflow logger."""
        if not self._configured:
            self.configure_logging()
            self._configured = True

    def configure_logging(
            self,
            level: str = "INFO",
            format_style: str = "detailed",
            enable_file_logging: bool = False,
            log_file_path: Optional[str] = None
    ) -> None:
        """
        Configure logging for the workflow system.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_style: Format style ('simple', 'detailed', 'json')
            enable_file_logging: Whether to enable file logging
            log_file_path: Path for log file (auto-generated if None)
        """
        # Convert string level to logging constant
        numeric_level = getattr(logging, level.upper(), logging.INFO)

        # Create formatter based on style
        formatter = self._get_formatter(format_style)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Add file handler if requested
        if enable_file_logging:
            file_path = log_file_path or self._generate_log_filename()
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            root_logger.info(f"File logging enabled: {file_path}")

        root_logger.info(f"Workflow logging configured - Level: {level}, Style: {format_style}")

    def _get_formatter(self, style: str) -> logging.Formatter:
        """Get formatter based on style preference."""
        formats = {
            'simple': '%(levelname)s - %(name)s - %(message)s',
            'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'json': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}'
        }

        format_string = formats.get(style, formats['detailed'])
        return logging.Formatter(format_string)

    def _generate_log_filename(self) -> str:
        """Generate timestamped log filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"workflow_v2_{timestamp}.log"

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance for a specific component.

        Args:
            name: Logger name (usually __name__ or component name)

        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)

    @staticmethod
    def log_execution_start(logger: logging.Logger, component_name: str, **kwargs) -> None:
        """
        Log the start of component execution.

        Args:
            logger: Logger instance
            component_name: Name of component starting execution
            **kwargs: Additional context to log
        """
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.info(f"=== Starting {component_name} execution ===")
        if context_str:
            logger.info(f"Context: {context_str}")

    @staticmethod
    def log_execution_end(logger: logging.Logger, component_name: str, success: bool = True, **kwargs) -> None:
        """
        Log the end of component execution.

        Args:
            logger: Logger instance
            component_name: Name of component ending execution
            success: Whether execution was successful
            **kwargs: Additional context to log
        """
        status = "SUCCESS" if success else "FAILED"
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.info(f"=== {component_name} execution {status} ===")
        if context_str:
            logger.info(f"Results: {context_str}")

    @staticmethod
    def log_state_change(logger: logging.Logger, operation: str, keys_changed: list) -> None:
        """
        Log state changes in workflow.

        Args:
            logger: Logger instance
            operation: Type of operation (added, modified, removed)
            keys_changed: List of state keys that changed
        """
        if keys_changed:
            logger.debug(f"State {operation}: {keys_changed}")


# Initialize global logger instance
workflow_logger = WorkflowLogger()


# Convenience function for getting loggers
def get_workflow_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a workflow logger.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return WorkflowLogger.get_logger(name)
