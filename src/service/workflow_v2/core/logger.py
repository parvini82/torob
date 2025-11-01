"""
Centralized logging configuration for workflow system.

Provides consistent logging setup and utilities for all workflow components.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds ANSI color codes to log messages.

    Provides color-coded output for different log levels to improve
    terminal readability while maintaining all formatting functionality.
    """

    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',

        # Log level colors
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[34m',     # Blue
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'SUCCESS': '\033[32m',  # Green

        # Component colors
        'TIMESTAMP': '\033[90m', # Dark gray
        'NAME': '\033[96m',      # Light cyan
        'FUNCTION': '\033[93m',  # Light yellow
    }

    def __init__(self, *args, **kwargs):
        """Initialize the colored formatter."""
        super().__init__(*args, **kwargs)

    def format(self, record):
        """Format the log record with appropriate colors."""
        # Store original values
        original_levelname = record.levelname
        original_name = record.name
        original_funcName = getattr(record, 'funcName', '')

        # Determine if this is a success message
        is_success = ('SUCCESS' in record.msg or
                     'success' in record.msg.lower() or
                     record.levelname == 'SUCCESS')

        # Apply colors to different components
        if is_success or 'SUCCESS' in original_levelname:
            colored_level = f"{self.COLORS['SUCCESS']}{self.COLORS['BOLD']}SUCCESS{self.COLORS['RESET']}"
        else:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            colored_level = f"{color}{self.COLORS['BOLD']}{record.levelname}{self.COLORS['RESET']}"

        # Color the logger name
        colored_name = f"{self.COLORS['NAME']}{original_name}{self.COLORS['RESET']}"

        # Color the function name if present
        if original_funcName:
            colored_funcName = f"{self.COLORS['FUNCTION']}{original_funcName}{self.COLORS['RESET']}"
            record.funcName = colored_funcName

        # Temporarily modify record for formatting
        record.levelname = colored_level
        record.name = colored_name

        # Format the message
        formatted = super().format(record)

        # Add timestamp coloring if present in format
        if '%(asctime)s' in self._style._fmt:
            # Color the timestamp portion (assuming it's at the beginning)
            parts = formatted.split(' - ', 1)
            if len(parts) > 1:
                timestamp_part = parts[0]
                rest_part = parts[1]
                colored_timestamp = f"{self.COLORS['TIMESTAMP']}{timestamp_part}{self.COLORS['RESET']}"
                formatted = f"{colored_timestamp} - {rest_part}"

        # Restore original values
        record.levelname = original_levelname
        record.name = original_name
        if original_funcName:
            record.funcName = original_funcName

        return formatted


class WorkflowLogger:
    """
    Centralized logger configuration for workflow system.

    Provides standardized logging setup with configurable levels,
    formatting, and output destinations with enhanced visual appearance.
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
        console_formatter = self._get_colored_formatter(format_style)
        file_formatter = self._get_formatter(format_style)  # Plain formatter for files

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler with colored formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Add file handler if requested (without colors)
        if enable_file_logging:
            file_path = log_file_path or self._generate_log_filename()
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            root_logger.info(f"File logging enabled: {file_path}")

        root_logger.info(f"Workflow logging configured - Level: {level}, Style: {format_style}")

    def _get_colored_formatter(self, style: str) -> ColoredFormatter:
        """Get colored formatter based on style preference."""
        formats = {
            'simple': '%(levelname)s - %(name)s - %(message)s',
            'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'json': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}'
        }

        format_string = formats.get(style, formats['detailed'])
        return ColoredFormatter(format_string)

    def _get_formatter(self, style: str) -> logging.Formatter:
        """Get plain formatter based on style preference (for file output)."""
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
        Log the start of component execution with enhanced visual formatting.

        Args:
            logger: Logger instance
            component_name: Name of component starting execution
            **kwargs: Additional context to log
        """
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())

        # Enhanced visual separator with colors
        separator = "=" * 50
        logger.info(f"\n{separator}")
        logger.info(f"🚀 Starting {component_name} execution")
        logger.info(f"{separator}")

        if context_str:
            logger.info(f"📋 Context: {context_str}")

    @staticmethod
    def log_execution_end(logger: logging.Logger, component_name: str, success: bool = True, **kwargs) -> None:
        """
        Log the end of component execution with enhanced visual formatting.

        Args:
            logger: Logger instance
            component_name: Name of component ending execution
            success: Whether execution was successful
            **kwargs: Additional context to log
        """
        status = "SUCCESS" if success else "FAILED"
        context_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())

        # Enhanced visual separator with status indicators
        separator = "=" * 50
        emoji = "✅" if success else "❌"

        logger.info(f"{separator}")

        if success:
            # This will trigger the success color formatting
            logger.info(f"{emoji} {component_name} execution SUCCESS")
        else:
            logger.error(f"{emoji} {component_name} execution FAILED")

        logger.info(f"{separator}\n")

        if context_str:
            if success:
                logger.info(f"📊 Results: {context_str}")
            else:
                logger.error(f"💥 Error details: {context_str}")

    @staticmethod
    def log_state_change(logger: logging.Logger, operation: str, keys_changed: list) -> None:
        """
        Log state changes in workflow with enhanced formatting.

        Args:
            logger: Logger instance
            operation: Type of operation (added, modified, removed)
            keys_changed: List of state keys that changed
        """
        if keys_changed:
            # Add emoji indicators for different operations
            emoji_map = {
                'added': '➕',
                'modified': '🔄',
                'removed': '➖',
                'updated': '🔄',
                'created': '➕',
                'deleted': '➖'
            }

            emoji = emoji_map.get(operation.lower(), '🔧')
            logger.debug(f"{emoji} State {operation}: {keys_changed}")


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
