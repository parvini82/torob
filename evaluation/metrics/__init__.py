"""Comprehensive metrics package for attribute value extraction evaluation.

Provides multiple evaluation approaches:
- Exact matching (MAVE standard)
- Similarity-based metrics (Jaccard, Dice, Semantic)
- Flexible evaluation modes (Partial, Lenient)
- Comprehensive reporting and aggregation

Usage:
    # For standard MAVE evaluation
    from evaluation.metrics import EntityMetrics

    # For specific metric types
    from evaluation.metrics import MetricsAggregator
    aggregator = MetricsAggregator(config, enabled_metrics=['exact', 'similarity'])

    # For individual metric modules
    from evaluation.metrics.exact_metrics import ExactMatchingMetrics
    from evaluation.metrics.similarity_metrics import SimilarityMetrics
"""

from .aggregator import MetricsAggregator, EntityMetrics
from .exact_metrics import ExactMatchingMetrics
from .similarity_metrics import SimilarityMetrics
from .evaluation_modes import PartialEvaluationMetrics, LenientEvaluationMetrics

__all__ = [
    'MetricsAggregator',
    'EntityMetrics',  # Legacy compatibility
    'ExactMatchingMetrics',
    'SimilarityMetrics',
    'PartialEvaluationMetrics',
    'LenientEvaluationMetrics'
]
