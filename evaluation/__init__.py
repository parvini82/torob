"""Simple evaluation module for model performance assessment.

This module provides straightforward tools for:
1. Running models on product samples
2. Calculating research-grade metrics
3. Generating comparative reports

Components:
- SimpleEvaluator: Main evaluation orchestrator
- ModelRunner: Model execution interface
- EntityMetrics: Comprehensive metrics calculator
"""

from .config import EvaluationConfig
from .model_runner import ModelRunner
from .metrics import EntityMetrics
from .evaluator import SimpleEvaluator

__all__ = [
    "EvaluationConfig",
    "ModelRunner",
    "EntityMetrics",
    "SimpleEvaluator"
]
