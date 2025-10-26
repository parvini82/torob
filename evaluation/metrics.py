"""Comprehensive metrics for entity extraction evaluation.

This module provides metrics commonly used in research papers for comparing
entity extraction performance, including those from academic literature.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re

from .config import EvaluationConfig


class EntityMetrics:
    """Comprehensive metrics for entity extraction evaluation.

    Includes standard metrics and research paper metrics like:
    - 80% Accuracy (from "Visual Zero-Shot E-Commerce Product Attribute Value Extraction")
    - Macro-F1, Micro-F1
    - ROUGE-1
    - Standard precision, recall, F1
    """

    def __init__(self, config: EvaluationConfig):
        """Initialize metrics calculator.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Input text string

        Returns:
            Normalized text (lowercase, stripped, no extra spaces)
        """
        if not text:
            return ""
        return re.sub(r'\s+', ' ', str(text).lower().strip())

    def extract_entity_values(self, entities: List[Dict]) -> Set[str]:
        """Extract all entity values from entity list.

        Args:
            entities: List of entity dictionaries

        Returns:
            Set of normalized entity values
        """
        values = set()
        for entity in entities:
            if isinstance(entity, dict):
                entity_values = entity.get('values', [])
                if isinstance(entity_values, list):
                    for value in entity_values:
                        normalized = self.normalize_text(str(value))
                        if normalized:
                            values.add(normalized)
        return values

    def extract_entity_pairs(self, entities: List[Dict]) -> Set[Tuple[str, str]]:
        """Extract (attribute, value) pairs from entities.

        Args:
            entities: List of entity dictionaries

        Returns:
            Set of (normalized_name, normalized_value) tuples
        """
        pairs = set()
        for entity in entities:
            if isinstance(entity, dict):
                name = self.normalize_text(entity.get('name', ''))
                values = entity.get('values', [])
                if isinstance(values, list):
                    for value in values:
                        normalized_value = self.normalize_text(str(value))
                        if name and normalized_value:
                            pairs.add((name, normalized_value))
        return pairs

    def exact_match(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate exact match score for complete entity structure.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            Exact match score (0.0 or 1.0)
        """
        if not ground_truth:
            return 1.0 if not predicted else 0.0

        pred_pairs = self.extract_entity_pairs(predicted)
        true_pairs = self.extract_entity_pairs(ground_truth)

        return 1.0 if pred_pairs == true_pairs else 0.0

    def eighty_percent_accuracy(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate 80% accuracy metric (from research paper).

        This metric considers a sample correct if at least 80% of ground truth
        entity values are correctly predicted.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            1.0 if ≥80% of ground truth values are predicted, 0.0 otherwise
        """
        if not ground_truth:
            return 1.0  # No ground truth to match

        true_values = self.extract_entity_values(ground_truth)
        pred_values = self.extract_entity_values(predicted)

        if not true_values:
            return 1.0

        # Calculate overlap
        correct_values = len(true_values & pred_values)
        accuracy = correct_values / len(true_values)

        return 1.0 if accuracy >= 0.8 else 0.0

    def micro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Calculate Micro-F1 score.

        Micro-F1 aggregates contributions of all classes to compute average metric.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            Dictionary with precision, recall, and F1 scores
        """
        true_values = self.extract_entity_values(ground_truth)
        pred_values = self.extract_entity_values(predicted)

        if not true_values and not pred_values:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

        true_positives = len(pred_values & true_values)
        false_positives = len(pred_values - true_values)
        false_negatives = len(true_values - pred_values)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, self.config.precision_digits),
            "recall": round(recall, self.config.precision_digits),
            "f1": round(f1, self.config.precision_digits)
        }

    def macro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Calculate Macro-F1 score.

        Macro-F1 calculates metrics for each attribute separately and then averages.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            Dictionary with precision, recall, and F1 scores
        """
        # Get all unique attribute names
        pred_pairs = self.extract_entity_pairs(predicted)
        true_pairs = self.extract_entity_pairs(ground_truth)

        all_attributes = set()
        for name, _ in pred_pairs:
            all_attributes.add(name)
        for name, _ in true_pairs:
            all_attributes.add(name)

        if not all_attributes:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        attribute_metrics = []

        for attr in all_attributes:
            # Get values for this attribute
            pred_attr_values = {value for name, value in pred_pairs if name == attr}
            true_attr_values = {value for name, value in true_pairs if name == attr}

            # Calculate metrics for this attribute
            if not true_attr_values and not pred_attr_values:
                attr_precision = attr_recall = attr_f1 = 1.0
            elif not true_attr_values:
                attr_precision = attr_recall = attr_f1 = 0.0
            elif not pred_attr_values:
                attr_precision = attr_recall = attr_f1 = 0.0
            else:
                tp = len(pred_attr_values & true_attr_values)
                fp = len(pred_attr_values - true_attr_values)
                fn = len(true_attr_values - pred_attr_values)

                attr_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                attr_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                attr_f1 = 2 * attr_precision * attr_recall / (attr_precision + attr_recall) if (attr_precision + attr_recall) > 0 else 0.0

            attribute_metrics.append({
                "precision": attr_precision,
                "recall": attr_recall,
                "f1": attr_f1
            })

        # Average across attributes
        avg_precision = sum(m["precision"] for m in attribute_metrics) / len(attribute_metrics)
        avg_recall = sum(m["recall"] for m in attribute_metrics) / len(attribute_metrics)
        avg_f1 = sum(m["f1"] for m in attribute_metrics) / len(attribute_metrics)

        return {
            "precision": round(avg_precision, self.config.precision_digits),
            "recall": round(avg_recall, self.config.precision_digits),
            "f1": round(avg_f1, self.config.precision_digits)
        }

    def rouge_1(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate ROUGE-1 score for entity extraction.

        ROUGE-1 measures overlap of unigrams between predicted and ground truth.

        Args:
            predicted: List of predicted entity dictionaries
            ground_truth: List of ground truth entity dictionaries

        Returns:
            ROUGE-1 F1 score
        """
        # Extract all text content from entities
        pred_text = []
        for entity in predicted:
            if isinstance(entity, dict):
                # Add entity name
                name = entity.get('name', '')
                if name:
                    pred_text.append(str(name))

                # Add entity values
                values = entity.get('values', [])
                if isinstance(values, list):
                    for value in values:
                        if value:
                            pred_text.append(str(value))

        true_text = []
        for entity in ground_truth:
            if isinstance(entity, dict):
                # Add entity name
                name = entity.get('name', '')
                if name:
                    true_text.append(str(name))

                # Add entity values
                values = entity.get('values', [])
                if isinstance(values, list):
                    for value in values:
                        if value:
                            true_text.append(str(value))

        # Tokenize and normalize
        pred_tokens = set()
        for text in pred_text:
            tokens = self.normalize_text(text).split()
            pred_tokens.update(tokens)

        true_tokens = set()
        for text in true_text:
            tokens = self.normalize_text(text).split()
            true_tokens.update(tokens)

        if not true_tokens:
            return 1.0 if not pred_tokens else 0.0

        if not pred_tokens:
            return 0.0

        # Calculate ROUGE-1 F1
        overlap = len(pred_tokens & true_tokens)
        precision = overlap / len(pred_tokens)
        recall = overlap / len(true_tokens)

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
        return {
            "exact_match": self.exact_match(predicted, ground_truth),
            "eighty_percent_accuracy": self.eighty_percent_accuracy(predicted, ground_truth),
            "micro_f1": self.micro_f1(predicted, ground_truth),
            "macro_f1": self.macro_f1(predicted, ground_truth),
            "rouge_1": self.rouge_1(predicted, ground_truth)
        }

    def evaluate_batch(self,
                      predictions: List[List[Dict]],
                      ground_truths: List[List[Dict]]) -> Dict[str, Any]:
        """Evaluate batch of predictions with comprehensive metrics.

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Dictionary with aggregated metrics and per-sample results
        """
        if len(predictions) != len(ground_truths):
            raise ValueError("Predictions and ground truths must have same length")

        # Calculate per-sample metrics
        sample_results = []
        for pred, true in zip(predictions, ground_truths):
            sample_result = self.evaluate_single_sample(pred, true)
            sample_results.append(sample_result)

        # Aggregate results
        num_samples = len(predictions)

        # Average single-value metrics
        exact_match_rate = sum(r["exact_match"] for r in sample_results) / num_samples
        eighty_percent_acc = sum(r["eighty_percent_accuracy"] for r in sample_results) / num_samples
        rouge_1_avg = sum(r["rouge_1"] for r in sample_results) / num_samples

        # Average F1 metrics
        micro_f1_scores = [r["micro_f1"]["f1"] for r in sample_results]
        micro_precision_scores = [r["micro_f1"]["precision"] for r in sample_results]
        micro_recall_scores = [r["micro_f1"]["recall"] for r in sample_results]

        macro_f1_scores = [r["macro_f1"]["f1"] for r in sample_results]
        macro_precision_scores = [r["macro_f1"]["precision"] for r in sample_results]
        macro_recall_scores = [r["macro_f1"]["recall"] for r in sample_results]

        # Compile final results
        results = {
            "total_samples": num_samples,

            # Primary metrics (matching research paper format)
            "exact_match_rate": round(exact_match_rate, self.config.precision_digits),
            "eighty_percent_accuracy": round(eighty_percent_acc, self.config.precision_digits),
            "macro_f1": round(sum(macro_f1_scores) / num_samples, self.config.precision_digits),
            "micro_f1": round(sum(micro_f1_scores) / num_samples, self.config.precision_digits),
            "rouge_1": round(rouge_1_avg, self.config.precision_digits),

            # Additional detailed metrics
            "detailed_metrics": {
                "macro_precision": round(sum(macro_precision_scores) / num_samples, self.config.precision_digits),
                "macro_recall": round(sum(macro_recall_scores) / num_samples, self.config.precision_digits),
                "micro_precision": round(sum(micro_precision_scores) / num_samples, self.config.precision_digits),
                "micro_recall": round(sum(micro_recall_scores) / num_samples, self.config.precision_digits),
            },

            # Per-sample breakdown (for detailed analysis)
            "per_sample_results": sample_results if self.config.precision_digits else None
        }

        return results

    def format_results_table(self, results: Dict[str, Any]) -> str:
        """Format results in research paper table format.

        Args:
            results: Results from evaluate_batch

        Returns:
            Formatted string table
        """
        table = []
        table.append("Metric\t\tScore")
        table.append("-" * 30)
        table.append(f"80%Acc.\t\t{results['eighty_percent_accuracy']:.2f}")
        table.append(f"Macro-F1\t{results['macro_f1']:.2f}")
        table.append(f"Micro-F1\t{results['micro_f1']:.2f}")
        table.append(f"ROUGE-1\t\t{results['rouge_1']:.2f}")
        table.append(f"Exact Match\t{results['exact_match_rate']:.2f}")

        return "\n".join(table)
