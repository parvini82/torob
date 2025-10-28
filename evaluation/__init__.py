"""Simple evaluation module for model performance assessment.

This module provides comprehensive tools for:
1. Running models on product samples
2. Calculating research-grade metrics (multiple approaches)
3. Generating comparative reports

Components:
- ModelRunner: Model execution interface
- MetricsAggregator: Comprehensive metrics calculator
- EntityMetrics: Legacy interface (backward compatibility)
"""

from .config import EvaluationConfig
from .model_runner import ModelRunner
from .metrics import MetricsAggregator, EntityMetrics

__all__ = [
    "EvaluationConfig",
    "ModelRunner",
    "MetricsAggregator",
    "EntityMetrics"  # Legacy compatibility
]
