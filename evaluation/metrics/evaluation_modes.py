"""Different evaluation modes: Partial and Lenient evaluation.

Implements more flexible evaluation approaches that are less strict
than exact matching but more structured than pure similarity.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from .base import BaseMetric, EntityProcessor


class PartialEvaluationMetrics(BaseMetric):
    """Partial evaluation: credit for partially correct predictions."""

    @property
    def metric_name(self) -> str:
        return "partial"

    def calculate_partial_matches(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Calculate partial matches at attribute level.

        Gives partial credit when some values for an attribute are correct,
        even if not all values match.
        """
        if not ground_truth:
            return {"partial_precision": 1.0 if not predicted else 0.0,
                    "partial_recall": 1.0, "partial_f1": 1.0 if not predicted else 0.0}

        # Group by attributes
        pred_attrs = defaultdict(set)
        true_attrs = defaultdict(set)

        for entity in predicted:
            if isinstance(entity, dict):
                name = EntityProcessor.normalize_text(entity.get('name', ''), "standard")
                values = entity.get('values', [])
                if isinstance(values, list) and name:
                    for value in values:
                        norm_val = EntityProcessor.normalize_text(str(value), "standard")
                        if norm_val:
                            pred_attrs[name].add(norm_val)

        for entity in ground_truth:
            if isinstance(entity, dict):
                name = EntityProcessor.normalize_text(entity.get('name', ''), "standard")
                values = entity.get('values', [])
                if isinstance(values, list) and name:
                    for value in values:
                        norm_val = EntityProcessor.normalize_text(str(value), "standard")
                        if norm_val:
                            true_attrs[name].add(norm_val)

        if not true_attrs:
            return {"partial_precision": 0.0, "partial_recall": 0.0, "partial_f1": 0.0}

        # Calculate partial matches per attribute
        total_precision_score = 0.0
        total_recall_score = 0.0

        all_attrs = set(pred_attrs.keys()) | set(true_attrs.keys())

        for attr in all_attrs:
            pred_vals = pred_attrs.get(attr, set())
            true_vals = true_attrs.get(attr, set())

            if true_vals:
                # Partial recall: how many true values were predicted
                recall_score = len(pred_vals & true_vals) / len(true_vals)
                total_recall_score += recall_score

            if pred_vals:
                # Partial precision: how many predicted values were correct
                precision_score = len(pred_vals & true_vals) / len(pred_vals)
                total_precision_score += precision_score

        # Average across attributes
        num_true_attrs = len(true_attrs)
        num_pred_attrs = len(pred_attrs)

        avg_recall = total_recall_score / num_true_attrs if num_true_attrs > 0 else 0.0
        avg_precision = total_precision_score / num_pred_attrs if num_pred_attrs > 0 else 0.0

        partial_f1 = 2 * avg_precision * avg_recall / (avg_precision + avg_recall) if (
                                                                                                  avg_precision + avg_recall) > 0 else 0.0

        return {
            "partial_precision": round(avg_precision, self.config.precision_digits),
            "partial_recall": round(avg_recall, self.config.precision_digits),
            "partial_f1": round(partial_f1, self.config.precision_digits)
        }

    def calculate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Calculate partial evaluation metrics for single sample."""
        return self.calculate_partial_matches(predicted, ground_truth)

    def aggregate_batch_results(self, sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate partial evaluation results across batch."""
        if not sample_results:
            return {"partial_precision": 0.0, "partial_recall": 0.0, "partial_f1": 0.0}

        avg_precision = sum(r["partial_precision"] for r in sample_results) / len(sample_results)
        avg_recall = sum(r["partial_recall"] for r in sample_results) / len(sample_results)
        avg_f1 = sum(r["partial_f1"] for r in sample_results) / len(sample_results)

        return {
            "partial_precision": round(avg_precision, self.config.precision_digits),
            "partial_recall": round(avg_recall, self.config.precision_digits),
            "partial_f1": round(avg_f1, self.config.precision_digits)
        }


class LenientEvaluationMetrics(BaseMetric):
    """Lenient evaluation: more flexible matching with normalization."""

    @property
    def metric_name(self) -> str:
        return "lenient"

    def lenient_match(self, pred_val: str, true_val: str) -> bool:
        """Check if two values match under lenient criteria.

        Applies various normalization and matching strategies:
        - Case insensitive
        - Whitespace normalization
        - Partial substring matching
        - Common abbreviation handling
        """
        if not pred_val or not true_val:
            return pred_val == true_val

        # Normalize both values
        pred_norm = EntityProcessor.normalize_text(pred_val, "standard")
        true_norm = EntityProcessor.normalize_text(true_val, "standard")

        # Exact match after normalization
        if pred_norm == true_norm:
            return True

        # Substring matching (both directions)
        if pred_norm in true_norm or true_norm in pred_norm:
            return True

        # Common Persian abbreviations/variations
        persian_equivalents = {
            "آبی": ["blue", "ابی"],
            "قرمز": ["red", "قمز"],
            "سبز": ["green", "سز"],
            "زرد": ["yellow"],
            "مشکی": ["black", "سیاه"],
            "سفید": ["white", "سپید"],
            "طلایی": ["gold", "طلای"],
            "نقره": ["silver", "نقرای"],
            "بزرگ": ["large", "لارج", "xl", "l"],
            "متوسط": ["medium", "m", "mid"],
            "کوچک": ["small", "s", "sm"],
            "پنبه": ["cotton", "کتان"],
            "ابریشم": ["silk"],
            "چرم": ["leather"],
        }

        # Check equivalents
        for standard, variants in persian_equivalents.items():
            if (pred_norm == standard and true_norm in variants) or \
                    (true_norm == standard and pred_norm in variants) or \
                    (pred_norm in variants and true_norm in variants):
                return True

        return False

    def calculate_lenient_matches(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Calculate lenient matching metrics."""
        if not ground_truth:
            return {"lenient_precision": 1.0 if not predicted else 0.0,
                    "lenient_recall": 1.0, "lenient_f1": 1.0 if not predicted else 0.0}

        # Extract all attribute-value pairs
        pred_pairs = EntityProcessor.extract_attribute_value_pairs(predicted, "minimal")
        true_pairs = EntityProcessor.extract_attribute_value_pairs(ground_truth, "minimal")

        if not true_pairs and not pred_pairs:
            return {"lenient_precision": 1.0, "lenient_recall": 1.0, "lenient_f1": 1.0}

        if not true_pairs:
            return {"lenient_precision": 0.0, "lenient_recall": 1.0, "lenient_f1": 0.0}

        if not pred_pairs:
            return {"lenient_precision": 1.0, "lenient_recall": 0.0, "lenient_f1": 0.0}

        # Find lenient matches
        lenient_tp = 0

        matched_true_pairs = set()
        for pred_attr, pred_val in pred_pairs:
            for true_attr, true_val in true_pairs:
                if (true_attr, true_val) not in matched_true_pairs:
                    # Check if attribute matches and value matches leniently
                    if (EntityProcessor.normalize_text(pred_attr, "standard") ==
                            EntityProcessor.normalize_text(true_attr, "standard") and
                            self.lenient_match(pred_val, true_val)):
                        lenient_tp += 1
                        matched_true_pairs.add((true_attr, true_val))
                        break

        lenient_fp = len(pred_pairs) - lenient_tp
        lenient_fn = len(true_pairs) - lenient_tp

        precision = lenient_tp / (lenient_tp + lenient_fp) if (lenient_tp + lenient_fp) > 0 else 0.0
        recall = lenient_tp / (lenient_tp + lenient_fn) if (lenient_tp + lenient_fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "lenient_precision": round(precision, self.config.precision_digits),
            "lenient_recall": round(recall, self.config.precision_digits),
            "lenient_f1": round(f1, self.config.precision_digits)
        }

    def calculate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Calculate lenient evaluation metrics for single sample."""
        return self.calculate_lenient_matches(predicted, ground_truth)

    def aggregate_batch_results(self, sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate lenient evaluation results across batch."""
        if not sample_results:
            return {"lenient_precision": 0.0, "lenient_recall": 0.0, "lenient_f1": 0.0}

        avg_precision = sum(r["lenient_precision"] for r in sample_results) / len(sample_results)
        avg_recall = sum(r["lenient_recall"] for r in sample_results) / len(sample_results)
        avg_f1 = sum(r["lenient_f1"] for r in sample_results) / len(sample_results)

        return {
            "lenient_precision": round(avg_precision, self.config.precision_digits),
            "lenient_recall": round(avg_recall, self.config.precision_digits),
            "lenient_f1": round(avg_f1, self.config.precision_digits)
        }
# Partial, Lenient evaluation
