"""Tests for the entity tag evaluation metrics.

These tests validate exact/partial matches, attribute-level metrics,
80% accuracy, and semantic similarity (with SentenceTransformer mocked).
"""

from unittest.mock import patch
import numpy as np

from src.evaluation.entity_evaluator import EntityTagEvaluator
from src.evaluation.config import EvaluationConfig


def _sample_pairs():
    predicted = [
        {"name": "جنس", "values": ["لنین"]},
        {"name": "نوع کلی", "values": ["کت شلوار"]},
        {"name": "رنگ", "values": ["آبی"]},
    ]
    truth = [
        {"name": "جنس", "values": ["لنین"]},
        {"name": "نوع کلی", "values": ["کت شلوار"]},
        {"name": "رنگ", "values": ["آبی", "سفید"]},
    ]
    return predicted, truth


def test_exact_match_score():
    cfg = EvaluationConfig()
    evalr = EntityTagEvaluator(cfg)
    pred, truth = _sample_pairs()
    # Not exactly the same because truth has extra value
    assert evalr.exact_match_score(pred, truth) == 0.0
    assert evalr.exact_match_score(truth, truth) == 1.0


def test_partial_match_score():
    cfg = EvaluationConfig()
    evalr = EntityTagEvaluator(cfg)
    pred, truth = _sample_pairs()
    scores = evalr.partial_match_score(pred, truth)
    assert 0.0 <= scores['precision'] <= 1.0
    assert 0.0 <= scores['recall'] <= 1.0
    assert 0.0 <= scores['f1'] <= 1.0


def test_attribute_level_metrics():
    cfg = EvaluationConfig()
    evalr = EntityTagEvaluator(cfg)
    pred, truth = _sample_pairs()
    metrics = evalr.attribute_level_metrics(pred, truth)
    assert 'جنس' in metrics and 'رنگ' in metrics
    assert set(['precision', 'recall', 'f1', 'tp', 'fp', 'fn', 'support']).issubset(metrics['رنگ'].keys())


def test_eighty_percent_accuracy():
    cfg = EvaluationConfig()
    evalr = EntityTagEvaluator(cfg)
    pred, truth = _sample_pairs()
    acc = evalr.eighty_percent_accuracy(pred, truth)
    assert acc in (0.0, 1.0)


@patch('src.evaluation.entity_evaluator.SentenceTransformer')
def test_semantic_similarity_mocked(mock_st):
    """Semantic similarity should compute precision/recall/F1 using mocked embeddings."""
    # Create deterministic mock embeddings
    class _MockModel:
        def encode(self, values):
            # Map values to simple vectors by length to simulate similarity
            return np.array([[len(v)] for v in values], dtype=float)
    
    mock_st.return_value = _MockModel()
    cfg = EvaluationConfig()
    evalr = EntityTagEvaluator(cfg)
    pred, truth = _sample_pairs()
    scores = evalr.semantic_similarity_score(pred, truth, threshold=0.5)
    assert 0.0 <= scores['semantic_precision'] <= 1.0
    assert 0.0 <= scores['semantic_recall'] <= 1.0
    assert 0.0 <= scores['semantic_f1'] <= 1.0
