"""Evaluation module for model performance assessment.

This module provides comprehensive evaluation capabilities including:
- Metric calculation and analysis
- Sample validation
- Performance reporting
- Evaluation pipeline orchestration
- Entity extraction evaluation with multiple metrics
"""

from .config import EvaluationConfig
from .entity_evaluator import EntityTagEvaluator
from .evaluator import ModelEvaluator
from .metrics import EvaluationMetrics

__all__ = [
    "EvaluationMetrics",
    "ModelEvaluator",
    "EvaluationConfig",
    "EntityTagEvaluator",
]
