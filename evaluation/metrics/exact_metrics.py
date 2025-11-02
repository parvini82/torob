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
        """
        Calculate precision, recall, and F1 score based on exact string matching
        of attribute–value pairs. Follows a robust and logical handling of edge cases.

        Args:
            predicted_pairs: Set of predicted (attribute, value) pairs
            true_pairs: Set of ground truth (attribute, value) pairs

        Returns:
            Dictionary with precision, recall, and f1 scores
        """

        # Case 1: both sets are empty → perfect match (no info to predict)
        if not true_pairs and not predicted_pairs:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

        # Case 2: ground truth empty but predictions exist → meaningless recall
        if not true_pairs and predicted_pairs:
            # Model produced outputs when nothing existed → penalize recall too
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Case 3: ground truth exists but no predictions → missed everything
        if true_pairs and not predicted_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # --- Standard TP/FP/FN calculation ---
        true_positives = len(predicted_pairs & true_pairs)
        false_positives = len(predicted_pairs - true_pairs)
        false_negatives = len(true_pairs - predicted_pairs)

        # --- Compute precision, recall, f1 ---
        precision = true_positives / (true_positives + false_positives) if (
                                                                                       true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
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

    def weighted_macro_averaged_metrics(self, predictions: List[List[Dict]],
                                        ground_truths: List[List[Dict]],
                                        categories: List[str] = None) -> Dict[str, float]:
        """
        Calculate weighted macro-averaged metrics based on entity frequencies.

        Args:
            predictions: List of prediction lists
            ground_truths: List of ground truth lists
            categories: List of categories for each sample (optional)
        """
        if not self.config.enable_weighted_macro or not self.config.entity_weights_path:
            # Fallback to regular macro averaging
            return self.macro_averaged_metrics(predictions, ground_truths)

        # Load entity weights
        entity_weights = EntityProcessor.load_entity_weights(self.config.entity_weights_path)
        if not entity_weights:
            return self.macro_averaged_metrics(predictions, ground_truths)

        valid_pairs = [(p, t, c) for (p, t), c in
                       zip(zip(predictions, ground_truths), categories or ['unknown'] * len(predictions)) if t]

        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Group by attribute and calculate weighted metrics
        weighted_precision_sum = 0.0
        weighted_recall_sum = 0.0
        weighted_f1_sum = 0.0
        total_weight = 0.0

        # Collect attribute metrics with weights
        attr_metrics_with_weights = []

        for pred, true, category in valid_pairs:
            pred_pairs = EntityProcessor.extract_attribute_value_pairs(pred, "minimal")
            true_pairs = EntityProcessor.extract_attribute_value_pairs(true, "minimal")

            # Group by attribute
            pred_by_attr = defaultdict(set)
            true_by_attr = defaultdict(set)

            for attr, val in pred_pairs:
                pred_by_attr[attr].add((attr, val))
            for attr, val in true_pairs:
                true_by_attr[attr].add((attr, val))

            all_attrs = set(pred_by_attr.keys()) | set(true_by_attr.keys())

            for attr in all_attrs:
                # Calculate metrics for this attribute
                attr_prf = self.calculate_prf(
                    pred_by_attr.get(attr, set()),
                    true_by_attr.get(attr, set())
                )

                # Get weight for this attribute in this category
                weight = EntityProcessor.get_entity_weight(attr, category, entity_weights)

                attr_metrics_with_weights.append({
                    'precision': attr_prf['precision'],
                    'recall': attr_prf['recall'],
                    'f1': attr_prf['f1'],
                    'weight': weight
                })

        # Calculate weighted averages
        if attr_metrics_with_weights:
            total_weight = sum(m['weight'] for m in attr_metrics_with_weights)
            if total_weight > 0:
                weighted_precision_sum = sum(m['precision'] * m['weight'] for m in attr_metrics_with_weights)
                weighted_recall_sum = sum(m['recall'] * m['weight'] for m in attr_metrics_with_weights)
                weighted_f1_sum = sum(m['f1'] * m['weight'] for m in attr_metrics_with_weights)

                return {
                    "precision": round(weighted_precision_sum / total_weight, self.config.precision_digits),
                    "recall": round(weighted_recall_sum / total_weight, self.config.precision_digits),
                    "f1": round(weighted_f1_sum / total_weight, self.config.precision_digits)
                }

        # Fallback to uniform weighting
        return self.macro_averaged_metrics(predictions, ground_truths)
