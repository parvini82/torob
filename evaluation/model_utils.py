"""Utility functions for model execution with robust error handling.

This module provides retry mechanisms and error handling for model functions,
including rate limiting, timeout handling, and other common API issues.
"""

import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import random


class RetryStrategy(Enum):
    """Retry strategies for different types of errors."""
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    NO_RETRY = "no_retry"


class ModelExecutionError(Exception):
    """Custom exception for model execution errors."""

    def __init__(self, message: str, retry_strategy: RetryStrategy = RetryStrategy.NO_RETRY):
        super().__init__(message)
        self.retry_strategy = retry_strategy


def classify_error(error: Exception) -> RetryStrategy:
    """Classify error and determine appropriate retry strategy.

    Args:
        error: Exception that occurred during model execution

    Returns:
        Appropriate retry strategy for the error type
    """
    error_message = str(error).lower()

    # Rate limiting errors
    if any(keyword in error_message for keyword in [
        "rate limit", "too many requests", "quota exceeded",
        "429", "rate_limit_exceeded"
    ]):
        return RetryStrategy.RATE_LIMIT

    # Network/connection errors
    if any(keyword in error_message for keyword in [
        "connection", "network", "timeout", "unreachable",
        "connection refused", "name resolution", "ssl"
    ]):
        return RetryStrategy.NETWORK_ERROR

    # Timeout errors
    if any(keyword in error_message for keyword in [
        "timeout", "timed out", "read timeout", "request timeout"
    ]):
        return RetryStrategy.TIMEOUT

    # Server errors (5xx)
    if any(keyword in error_message for keyword in [
        "500", "502", "503", "504", "server error",
        "internal server error", "bad gateway", "service unavailable"
    ]):
        return RetryStrategy.SERVER_ERROR

    # Client errors (4xx) - usually no retry
    if any(keyword in error_message for keyword in [
        "400", "401", "403", "404", "bad request",
        "unauthorized", "forbidden", "not found"
    ]):
        return RetryStrategy.NO_RETRY

    # Default: try network error strategy for unknown errors
    return RetryStrategy.NETWORK_ERROR


def get_retry_config(strategy: RetryStrategy) -> Dict[str, Any]:
    """Get retry configuration for a given strategy.

    Args:
        strategy: Retry strategy

    Returns:
        Configuration dictionary with max_retries, delays, and backoff
    """
    configs = {
        RetryStrategy.RATE_LIMIT: {
            "max_retries": 5,
            "base_delay": 30,  # Start with 30 seconds
            "max_delay": 300,  # Cap at 5 minutes
            "backoff_factor": 2.0,
            "jitter": True
        },
        RetryStrategy.NETWORK_ERROR: {
            "max_retries": 3,
            "base_delay": 5,
            "max_delay": 60,
            "backoff_factor": 2.0,
            "jitter": True
        },
        RetryStrategy.TIMEOUT: {
            "max_retries": 3,
            "base_delay": 10,
            "max_delay": 120,
            "backoff_factor": 1.5,
            "jitter": False
        },
        RetryStrategy.SERVER_ERROR: {
            "max_retries": 4,
            "base_delay": 15,
            "max_delay": 180,
            "backoff_factor": 2.0,
            "jitter": True
        },
        RetryStrategy.NO_RETRY: {
            "max_retries": 0,
            "base_delay": 0,
            "max_delay": 0,
            "backoff_factor": 1.0,
            "jitter": False
        }
    }

    return configs.get(strategy, configs[RetryStrategy.NO_RETRY])


def calculate_delay(attempt: int, config: Dict[str, Any]) -> float:
    """Calculate delay for retry attempt.

    Args:
        attempt: Current attempt number (0-based)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    base_delay = config["base_delay"]
    backoff_factor = config["backoff_factor"]
    max_delay = config["max_delay"]
    jitter = config["jitter"]

    # Calculate exponential backoff
    delay = base_delay * (backoff_factor ** attempt)
    delay = min(delay, max_delay)

    # Add jitter if enabled
    if jitter:
        jitter_amount = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)

    return max(0, delay)


def robust_model_execution(model_function: Callable[[str], List[Dict[str, Any]]],
                           image_url: str,
                           base_delay: float = 20.0) -> List[Dict[str, Any]]:
    """Execute model function with robust error handling and retry logic.

    Args:
        model_function: Function that takes image_url and returns entities
        image_url: URL of the image to process
        base_delay: Base delay between requests (in seconds)

    Returns:
        List of entity dictionaries, empty list if all attempts fail
    """
    print(f"    Processing: {image_url[:60]}...")

    # Initial delay to prevent rate limiting
    time.sleep(base_delay)

    start_time = time.time()
    total_attempts = 0
    last_error = None

    try:
        result = model_function(image_url)

        # Validate result
        if not isinstance(result, list):
            print(f"    Warning: Model returned non-list result: {type(result)}")
            return []

        print(f"    ✓ Success: {len(result)} entities")
        return result

    except Exception as initial_error:
        last_error = initial_error
        strategy = classify_error(initial_error)
        config = get_retry_config(strategy)

        print(f"    ⚠ Initial attempt failed: {str(initial_error)[:100]}...")
        print(f"    Strategy: {strategy.value}, Max retries: {config['max_retries']}")

        # If no retry strategy, return immediately
        if strategy == RetryStrategy.NO_RETRY:
            print(f"    ✗ No retry for this error type")
            return []

        # Retry loop
        for attempt in range(config["max_retries"]):
            total_attempts += 1

            # Calculate delay for this attempt
            retry_delay = calculate_delay(attempt, config)

            print(f"    Retry {attempt + 1}/{config['max_retries']} after {retry_delay:.1f}s...")
            time.sleep(retry_delay)

            try:
                result = model_function(image_url)

                # Validate result
                if not isinstance(result, list):
                    print(f"    Warning: Model returned non-list result: {type(result)}")
                    return []

                elapsed_time = time.time() - start_time
                print(f"    ✓ Success on retry {attempt + 1}! ({elapsed_time:.1f}s total)")
                return result

            except Exception as retry_error:
                last_error = retry_error
                retry_strategy = classify_error(retry_error)

                print(f"    ✗ Retry {attempt + 1} failed: {str(retry_error)[:100]}...")

                # If error type changed, we might need different strategy
                if retry_strategy != strategy:
                    print(f"    Strategy changed: {strategy.value} → {retry_strategy.value}")
                    strategy = retry_strategy
                    config = get_retry_config(strategy)

        # All retries exhausted
        elapsed_time = time.time() - start_time
        print(f"    ✗ All attempts failed after {total_attempts + 1} tries in {elapsed_time:.1f}s")
        print(f"    Final error: {str(last_error)[:200]}...")
        return []


def create_robust_model_function(original_model_function: Callable[[str], List[Dict[str, Any]]],
                                 base_delay: float = 20.0) -> Callable[[str], List[Dict[str, Any]]]:
    """Create a robust wrapper around a model function.

    Args:
        original_model_function: Original model function to wrap
        base_delay: Base delay between requests

    Returns:
        Wrapped function with retry logic
    """

    def wrapped_function(image_url: str) -> List[Dict[str, Any]]:
        return robust_model_execution(original_model_function, image_url, base_delay)

    return wrapped_function
