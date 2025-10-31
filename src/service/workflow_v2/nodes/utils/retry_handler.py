"""
Retry handling utilities for node operations.
"""

import time
import logging
from typing import Callable, Any, Type, Tuple
from functools import wraps


class RetryError(Exception):
    """Raised when all retry attempts fail."""

    def __init__(self, message: str, last_exception: Exception = None):
        self.last_exception = last_exception
        super().__init__(message)


def with_retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        logger: logging.Logger = None
):
    """
    Decorator to add retry logic to functions.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff_factor: Multiplier for delay after each failure
        exceptions: Exception types to retry on
        logger: Logger instance for retry messages

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _logger = logger or logging.getLogger(func.__module__)
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:  # Not the last attempt
                        _logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        _logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}. "
                            f"Final error: {str(e)}"
                        )

            # All attempts failed
            raise RetryError(
                f"Function {func.__name__} failed after {max_attempts} attempts",
                last_exception
            )

        return wrapper

    return decorator
