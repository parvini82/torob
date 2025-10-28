"""Exact matching metrics following MAVE standards.

Implements standard precision/recall/F1 and exact match metrics
used in attribute value extraction research.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from .base import BaseMetric, EntityProcessor


class ExactMatchingMetrics(BaseMetric):
    """Standard exact matching metrics for AVE evaluation."""

    @property
    def metric_name(self) -> str:
        return "exact_matching"

    def calculate_prf(self, predicted_pairs: Set[Tuple[str, str]],
                      true_pairs: Set[Tuple[str, str]]) -> Dict[str, float]:
        """Calculate precision, recall, F1 for exact matching."""
        if not true_pairs and not predicted_pairs:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

        if not true_pairs:
            return {"precision": 0.0, "recall": 1.0, "f1": 0.0}

        if not predicted_pairs:
            return {"precision": 1.0, "recall": 0.0, "f1": 0.0}

        tp = len(predicted_pairs & true_pairs)
        fp = len(predicted_pairs - true_pairs)
        fn = len(true_pairs - predicted_pairs)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, self.config.precision_digits),
            "recall": round(recall, self.config.precision_digits),
            "f1": round(f1, self.config.precision_digits)
        }

    def exact_match(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Complete structure exact match."""
        if not ground_truth:
            return 1.0 if not predicted else 0.0

        pred_pairs = EntityProcessor.extract_attribute_value_pairs(predicted, "minimal")
        true_pairs = EntityProcessor.extract_attribute_value_pairs(ground_truth, "minimal")

        return 1.0 if pred_pairs == true_pairs else 0.0

    def calculate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Calculate exact matching metrics for single sample."""
        if not ground_truth:
            return {
                "exact_match": self.exact_match(predicted, ground_truth),
                "precision": None,
                "recall": None,
                "f1": None
            }

        pred_pairs = EntityProcessor.extract_attribute_value_pairs(predicted, "minimal")
        true_pairs = EntityProcessor.extract_attribute_value_pairs(ground_truth, "minimal")
        prf = self.calculate_prf(pred_pairs, true_pairs)

        return {
            "exact_match": self.exact_match(predicted, ground_truth),
            "precision": prf["precision"],
            "recall": prf["recall"],
            "f1": prf["f1"]
        }

    def micro_averaged_metrics(self, predictions: List[List[Dict]],
                               ground_truths: List[List[Dict]]) -> Dict[str, float]:
        """Calculate micro-averaged metrics across dataset."""
        valid_pairs = [(p, t) for p, t in zip(predictions, ground_truths) if t]

        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        all_pred_pairs = set()
        all_true_pairs = set()

        for pred, true in valid_pairs:
            pred_pairs = EntityProcessor.extract_attribute_value_pairs(pred, "minimal")
            true_pairs = EntityProcessor.extract_attribute_value_pairs(true, "minimal")
            all_pred_pairs.update(pred_pairs)
            all_true_pairs.update(true_pairs)

        return self.calculate_prf(all_pred_pairs, all_true_pairs)

    def macro_averaged_metrics(self, predictions: List[List[Dict]],
                               ground_truths: List[List[Dict]]) -> Dict[str, float]:
        """Calculate macro-averaged metrics by attribute."""
        valid_pairs = [(p, t) for p, t in zip(predictions, ground_truths) if t]

        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Group by attribute
        attr_pred = defaultdict(set)
        attr_true = defaultdict(set)

        for pred, true in valid_pairs:
            pred_pairs = EntityProcessor.extract_attribute_value_pairs(pred, "minimal")
            true_pairs = EntityProcessor.extract_attribute_value_pairs(true, "minimal")

            for attr, val in pred_pairs:
                attr_pred[attr].add((attr, val))
            for attr, val in true_pairs:
                attr_true[attr].add((attr, val))

        all_attrs = set(attr_pred.keys()) | set(attr_true.keys())
        if not all_attrs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        attr_metrics = []
        for attr in all_attrs:
            attr_prf = self.calculate_prf(attr_pred.get(attr, set()),
                                          attr_true.get(attr, set()))
            attr_metrics.append(attr_prf)

        return {
            "precision": round(sum(m["precision"] for m in attr_metrics) / len(attr_metrics),
                               self.config.precision_digits),
            "recall": round(sum(m["recall"] for m in attr_metrics) / len(attr_metrics), self.config.precision_digits),
            "f1": round(sum(m["f1"] for m in attr_metrics) / len(attr_metrics), self.config.precision_digits)
        }

    def aggregate_batch_results(self, sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate exact matching results across batch."""
        valid_results = [r for r in sample_results if r.get("precision") is not None]

        if not valid_results:
            return {
                "exact_match_rate": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            }

        # Calculate exact match rate
        all_exact_matches = [r["exact_match"] for r in sample_results]
        exact_match_rate = sum(all_exact_matches) / len(all_exact_matches)

        # Average P/R/F1 across valid samples
        avg_precision = sum(r["precision"] for r in valid_results) / len(valid_results)
        avg_recall = sum(r["recall"] for r in valid_results) / len(valid_results)
        avg_f1 = sum(r["f1"] for r in valid_results) / len(valid_results)

        return {
            "exact_match_rate": round(exact_match_rate, self.config.precision_digits),
            "precision": round(avg_precision, self.config.precision_digits),
            "recall": round(avg_recall, self.config.precision_digits),
            "f1": round(avg_f1, self.config.precision_digits)
        }
