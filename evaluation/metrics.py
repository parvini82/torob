"""Comprehensive metrics for attribute value extraction evaluation.

This module implements standard metrics used in AVE research, particularly
those established in the MAVE dataset and related papers. All metrics follow
exact string matching criteria as used in the literature.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
import re

from .config import EvaluationConfig


class EntityMetrics:
    """Metrics for attribute value extraction evaluation following MAVE standards.

    Implements metrics commonly used in AVE research:
    - Precision, Recall, F1 (both micro and macro averaging)
    - Exact Match (complete attribute-value structure matching)
    - ROUGE-1 (with proper n-gram counting)

    All metrics use exact string matching as per MAVE evaluation protocol.
    """

    def __init__(self, config: EvaluationConfig):
        """Initialize metrics calculator.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison (minimal normalization to preserve exact matching).

        Args:
            text: Input text string

        Returns:
            Normalized text (stripped whitespace only)
        """
        if not text:
            return ""
        return str(text).strip()

    def extract_attribute_value_pairs(self, entities: List[Dict]) -> Set[Tuple[str, str]]:
        """Extract (attribute, value) pairs with exact string matching.

        Args:
            entities: List of entity dictionaries

        Returns:
            Set of (attribute_name, value) tuples
        """
        pairs = set()
        for entity in entities:
            if isinstance(entity, dict):
                name = self.normalize_text(entity.get('name', ''))
                values = entity.get('values', [])
                if isinstance(values, list) and name:
                    for value in values:
                        normalized_value = self.normalize_text(str(value))
                        if normalized_value:
                            pairs.add((name, normalized_value))
        return pairs

    def extract_attribute_values_dict(self, entities: List[Dict]) -> Dict[str, Set[str]]:
        """Extract values grouped by attribute name for per-attribute evaluation.

        Args:
            entities: List of entity dictionaries

        Returns:
            Dictionary mapping attribute names to sets of values
        """
        attr_values = defaultdict(set)
        for entity in entities:
            if isinstance(entity, dict):
                name = self.normalize_text(entity.get('name', ''))
                values = entity.get('values', [])
                if isinstance(values, list) and name:
                    for value in values:
                        normalized_value = self.normalize_text(str(value))
                        if normalized_value:
                            attr_values[name].add(normalized_value)
        return dict(attr_values)

    def exact_match(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate exact match score (complete attribute-value structure matching).

        Following MAVE evaluation: a sample is correct only if ALL predicted
        attribute-value pairs exactly match the ground truth structure.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            1.0 if complete structure matches, 0.0 otherwise
        """
        if not ground_truth:
            return 1.0 if not predicted else 0.0

        pred_pairs = self.extract_attribute_value_pairs(predicted)
        true_pairs = self.extract_attribute_value_pairs(ground_truth)

        return 1.0 if pred_pairs == true_pairs else 0.0

    def calculate_precision_recall_f1(self, predicted_pairs: Set[Tuple[str, str]],
                                    true_pairs: Set[Tuple[str, str]]) -> Dict[str, float]:
        """Calculate P/R/F1 based on exact string matching of attribute-value pairs.

        Following MAVE protocol: TP/FP/FN based on exact string match.

        Args:
            predicted_pairs: Set of predicted (attribute, value) pairs
            true_pairs: Set of ground truth (attribute, value) pairs

        Returns:
            Dictionary with precision, recall, and f1 scores
        """
        if not true_pairs and not predicted_pairs:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

        if not true_pairs:
            return {"precision": 0.0, "recall": 1.0, "f1": 0.0}

        if not predicted_pairs:
            return {"precision": 1.0, "recall": 0.0, "f1": 0.0}

        # Standard TP/FP/FN calculation
        true_positives = len(predicted_pairs & true_pairs)
        false_positives = len(predicted_pairs - true_pairs)
        false_negatives = len(true_pairs - predicted_pairs)

        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, self.config.precision_digits),
            "recall": round(recall, self.config.precision_digits),
            "f1": round(f1, self.config.precision_digits)
        }

    def micro_averaged_metrics(self, predictions: List[List[Dict]],
                             ground_truths: List[List[Dict]]) -> Dict[str, float]:
        """Calculate micro-averaged P/R/F1 across entire dataset.

        Following MAVE standard: aggregate all TP/FP/FN across samples,
        then compute single P/R/F1 values.

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Dictionary with micro-averaged precision, recall, and f1
        """
        # Skip samples with empty ground truth (following research practice)
        valid_pairs = []
        for pred, true in zip(predictions, ground_truths):
            if true:  # Only include samples with non-empty ground truth
                valid_pairs.append((pred, true))

        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Aggregate all pairs across the entire dataset
        all_predicted_pairs = set()
        all_true_pairs = set()

        for pred, true in valid_pairs:
            pred_pairs = self.extract_attribute_value_pairs(pred)
            true_pairs = self.extract_attribute_value_pairs(true)

            all_predicted_pairs.update(pred_pairs)
            all_true_pairs.update(true_pairs)

        # Calculate single micro-averaged metrics
        return self.calculate_precision_recall_f1(all_predicted_pairs, all_true_pairs)

    def macro_averaged_metrics(self, predictions: List[List[Dict]],
                             ground_truths: List[List[Dict]]) -> Dict[str, float]:
        """Calculate macro-averaged P/R/F1 across attributes.

        Following AVE research: calculate P/R/F1 for each attribute separately,
        then average across attributes (giving equal weight to each attribute).

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Dictionary with macro-averaged precision, recall, and f1
        """
        # Skip samples with empty ground truth
        valid_pairs = []
        for pred, true in zip(predictions, ground_truths):
            if true:  # Only include samples with non-empty ground truth
                valid_pairs.append((pred, true))

        if not valid_pairs:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Collect all attribute-value pairs grouped by attribute
        attribute_predictions = defaultdict(set)
        attribute_ground_truths = defaultdict(set)

        for pred, true in valid_pairs:
            # Group predicted pairs by attribute
            pred_attrs = self.extract_attribute_values_dict(pred)
            for attr, values in pred_attrs.items():
                for value in values:
                    attribute_predictions[attr].add((attr, value))

            # Group ground truth pairs by attribute
            true_attrs = self.extract_attribute_values_dict(true)
            for attr, values in true_attrs.items():
                for value in values:
                    attribute_ground_truths[attr].add((attr, value))

        # Get all unique attributes
        all_attributes = set(attribute_predictions.keys()) | set(attribute_ground_truths.keys())

        if not all_attributes:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Calculate P/R/F1 for each attribute separately
        attribute_metrics = []
        for attr in all_attributes:
            attr_pred_pairs = attribute_predictions.get(attr, set())
            attr_true_pairs = attribute_ground_truths.get(attr, set())

            attr_metrics = self.calculate_precision_recall_f1(attr_pred_pairs, attr_true_pairs)
            attribute_metrics.append(attr_metrics)

        # Average across attributes (macro averaging)
        avg_precision = sum(m["precision"] for m in attribute_metrics) / len(attribute_metrics)
        avg_recall = sum(m["recall"] for m in attribute_metrics) / len(attribute_metrics)
        avg_f1 = sum(m["f1"] for m in attribute_metrics) / len(attribute_metrics)

        return {
            "precision": round(avg_precision, self.config.precision_digits),
            "recall": round(avg_recall, self.config.precision_digits),
            "f1": round(avg_f1, self.config.precision_digits)
        }

    def rouge_1(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate ROUGE-1 score with proper n-gram counting.

        Uses bag-of-words approach with frequency counting.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            ROUGE-1 F1 score, or None for empty ground truth
        """
        if not ground_truth:
            return None  # Skip empty ground truth

        def extract_tokens(entities):
            tokens = []
            for entity in entities:
                if isinstance(entity, dict):
                    # Add entity name tokens
                    name = entity.get('name', '')
                    if name:
                        name_tokens = self.normalize_text(name).lower().split()
                        tokens.extend(name_tokens)

                    # Add entity value tokens
                    values = entity.get('values', [])
                    if isinstance(values, list):
                        for value in values:
                            if value:
                                value_tokens = self.normalize_text(str(value)).lower().split()
                                tokens.extend(value_tokens)
            return tokens

        pred_tokens = extract_tokens(predicted)
        true_tokens = extract_tokens(ground_truth)

        if not true_tokens:
            return 1.0 if not pred_tokens else 0.0

        if not pred_tokens:
            return 0.0

        # Count token frequencies
        pred_counts = Counter(pred_tokens)
        true_counts = Counter(true_tokens)

        # Calculate overlap with frequency consideration
        overlap_count = 0
        for token in pred_counts:
            if token in true_counts:
                overlap_count += min(pred_counts[token], true_counts[token])

        # ROUGE-1 metrics
        precision = overlap_count / sum(pred_counts.values()) if pred_counts else 0.0
        recall = overlap_count / sum(true_counts.values()) if true_counts else 0.0

        if precision + recall == 0:
            return 0.0

        rouge_f1 = 2 * precision * recall / (precision + recall)
        return round(rouge_f1, self.config.precision_digits)

    def evaluate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Evaluate single sample with all metrics.

        Args:
            predicted: Predicted entities for one sample
            ground_truth: Ground truth entities for one sample

        Returns:
            Dictionary with all metric scores
        """
        if not ground_truth:
            # For empty ground truth samples, only exact match is meaningful
            return {
                "exact_match": self.exact_match(predicted, ground_truth),
                "precision": None,
                "recall": None,
                "f1": None,
                "rouge_1": None
            }

        # Calculate P/R/F1 for this sample
        pred_pairs = self.extract_attribute_value_pairs(predicted)
        true_pairs = self.extract_attribute_value_pairs(ground_truth)
        prf_metrics = self.calculate_precision_recall_f1(pred_pairs, true_pairs)

        return {
            "exact_match": self.exact_match(predicted, ground_truth),
            "precision": prf_metrics["precision"],
            "recall": prf_metrics["recall"],
            "f1": prf_metrics["f1"],
            "rouge_1": self.rouge_1(predicted, ground_truth)
        }

    def evaluate_batch(self,
                      predictions: List[List[Dict]],
                      ground_truths: List[List[Dict]]) -> Dict[str, Any]:
        """Evaluate batch of predictions following MAVE evaluation standards.

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Dictionary with all metrics following MAVE standards
        """
        if len(predictions) != len(ground_truths):
            raise ValueError("Predictions and ground truths must have same length")

        # Calculate per-sample metrics
        sample_results = []
        valid_samples = 0
        skipped_samples = 0

        for pred, true in zip(predictions, ground_truths):
            sample_result = self.evaluate_single_sample(pred, true)
            sample_results.append(sample_result)

            if not true:
                skipped_samples += 1
            else:
                valid_samples += 1

        # Calculate micro-averaged metrics (primary metrics in MAVE)
        micro_metrics = self.micro_averaged_metrics(predictions, ground_truths)

        # Calculate macro-averaged metrics (for balanced evaluation across attributes)
        macro_metrics = self.macro_averaged_metrics(predictions, ground_truths)

        # Aggregate other metrics
        exact_matches = [r["exact_match"] for r in sample_results]
        exact_match_rate = sum(exact_matches) / len(exact_matches) if exact_matches else 0.0

        rouge_values = [r["rouge_1"] for r in sample_results if r["rouge_1"] is not None]
        rouge_1_avg = sum(rouge_values) / len(rouge_values) if rouge_values else 0.0

        # Compile results following MAVE evaluation format
        results = {
            "total_samples": len(predictions),
            "valid_samples": valid_samples,
            "skipped_samples": skipped_samples,

            # Primary metrics (following MAVE standards)
            "precision": round(micro_metrics["precision"], self.config.precision_digits),
            "recall": round(micro_metrics["recall"], self.config.precision_digits),
            "f1": round(micro_metrics["f1"], self.config.precision_digits),
            "exact_match": round(exact_match_rate, self.config.precision_digits),

            # Additional metrics
            "macro_precision": round(macro_metrics["precision"], self.config.precision_digits),
            "macro_recall": round(macro_metrics["recall"], self.config.precision_digits),
            "macro_f1": round(macro_metrics["f1"], self.config.precision_digits),
            "rouge_1": round(rouge_1_avg, self.config.precision_digits),

            # Detailed breakdown for analysis
            "micro_averaged": micro_metrics,
            "macro_averaged": macro_metrics,
            "per_sample_results": sample_results if self.config.precision_digits else None
        }

        return results

    def format_results_table(self, results: Dict[str, Any]) -> str:
        """Format results in MAVE evaluation table format.

        Args:
            results: Results from evaluate_batch

        Returns:
            Formatted string table following MAVE standards
        """
        table = []
        table.append("Metric\t\tScore")
        table.append("-" * 30)
        table.append(f"Precision\t{results['precision']:.4f}")
        table.append(f"Recall\t\t{results['recall']:.4f}")
        table.append(f"F1\t\t{results['f1']:.4f}")
        table.append(f"Exact Match\t{results['exact_match']:.4f}")
        table.append("")
        table.append("Additional Metrics:")
        table.append(f"Macro-F1\t{results['macro_f1']:.4f}")
        table.append(f"ROUGE-1\t\t{results['rouge_1']:.4f}")

        if results.get('skipped_samples', 0) > 0:
            table.append("")
            table.append(f"Note: {results['skipped_samples']} samples skipped (empty GT)")

        return "\n".join(table)

    # Legacy method names for backward compatibility
    def micro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Legacy method - use micro_averaged_metrics instead."""
        pred_pairs = self.extract_attribute_value_pairs(predicted)
        true_pairs = self.extract_attribute_value_pairs(ground_truth)
        return self.calculate_precision_recall_f1(pred_pairs, true_pairs)

    def macro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Legacy method - use macro_averaged_metrics instead."""
        if not ground_truth:
            return None
        return self.macro_averaged_metrics([predicted], [ground_truth])

    def eighty_percent_accuracy(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Legacy method - not standard in MAVE evaluation."""
        return None  # Not used in standard MAVE evaluation
