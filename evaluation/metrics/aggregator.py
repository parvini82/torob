"""Metric aggregation and comprehensive reporting.

Orchestrates all metrics and provides unified evaluation interface
with comprehensive reporting capabilities.
"""

from typing import List, Dict, Any, Optional
from collections import Counter

from .base import BaseMetric
from .exact_metrics import ExactMatchingMetrics
from .similarity_metrics import SimilarityMetrics
from .evaluation_modes import PartialEvaluationMetrics, LenientEvaluationMetrics


class MetricsAggregator:
    """Aggregates and manages all evaluation metrics."""

    def __init__(self, config, enabled_metrics: Optional[List[str]] = None):
        """Initialize aggregator with specified metrics.

        Args:
            config: EvaluationConfig instance
            enabled_metrics: List of metric names to enable. If None, enables all.
                           Options: ['exact', 'similarity', 'partial', 'lenient']
        """
        self.config = config

        # Initialize all available metrics
        self.available_metrics = {
            'exact': ExactMatchingMetrics(config),
            'similarity': SimilarityMetrics(config),
            'partial': PartialEvaluationMetrics(config),
            'lenient': LenientEvaluationMetrics(config)
        }

        # Enable specified metrics or all by default
        if enabled_metrics is None:
            self.enabled_metrics = list(self.available_metrics.keys())
        else:
            self.enabled_metrics = [m for m in enabled_metrics if m in self.available_metrics]

        if not self.enabled_metrics:
            raise ValueError("No valid metrics specified")

    def calculate_rouge_1(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Calculate ROUGE-1 score with proper n-gram counting."""
        if not ground_truth:
            return None

        def extract_tokens(entities):
            tokens = []
            for entity in entities:
                if isinstance(entity, dict):
                    name = entity.get('name', '')
                    if name:
                        name_tokens = str(name).lower().strip().split()
                        tokens.extend(name_tokens)

                    values = entity.get('values', [])
                    if isinstance(values, list):
                        for value in values:
                            if value:
                                value_tokens = str(value).lower().strip().split()
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
        """Evaluate single sample with all enabled metrics.

        Args:
            predicted: Predicted entities for one sample
            ground_truth: Ground truth entities for one sample

        Returns:
            Dictionary with all metric results
        """
        results = {}

        # Calculate metrics from each enabled module
        for metric_name in self.enabled_metrics:
            metric = self.available_metrics[metric_name]
            metric_results = metric.calculate_single_sample(predicted, ground_truth)
            results.update(metric_results)

        # Add ROUGE-1
        results['rouge_1'] = self.calculate_rouge_1(predicted, ground_truth)

        return results

    def evaluate_batch(self, predictions: List[List[Dict]],
                       ground_truths: List[List[Dict]]) -> Dict[str, Any]:
        """Evaluate batch of predictions with comprehensive metrics.

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Comprehensive evaluation results
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

        # Aggregate results from each metric module
        aggregated_results = {
            "total_samples": len(predictions),
            "valid_samples": valid_samples,
            "skipped_samples": skipped_samples
        }

        # Process each enabled metric
        for metric_name in self.enabled_metrics:
            metric = self.available_metrics[metric_name]

            if metric_name == 'exact':
                # Add micro and macro averaged results
                micro_results = metric.micro_averaged_metrics(predictions, ground_truths)
                macro_results = metric.macro_averaged_metrics(predictions, ground_truths)

                # Standard MAVE metrics
                aggregated_results.update({
                    "precision": micro_results["precision"],
                    "recall": micro_results["recall"],
                    "f1": micro_results["f1"],
                    "macro_precision": macro_results["precision"],
                    "macro_recall": macro_results["recall"],
                    "macro_f1": macro_results["f1"]
                })

                # Exact match rate
                exact_matches = [r.get("exact_match", 0) for r in sample_results]
                aggregated_results["exact_match"] = sum(exact_matches) / len(exact_matches)

            else:
                # Other metrics: aggregate per-sample results
                metric_sample_results = []
                for result in sample_results:
                    metric_result = {}
                    for key, value in result.items():
                        if any(key.startswith(prefix) for prefix in [
                            metric_name,
                            'jaccard', 'dice', 'semantic',  # similarity
                            'partial', 'lenient'  # evaluation modes
                        ]):
                            if value is not None:
                                metric_result[key] = value

                    if metric_result:
                        metric_sample_results.append(metric_result)

                if metric_sample_results:
                    aggregated_metric_results = metric.aggregate_batch_results(metric_sample_results)
                    aggregated_results.update(aggregated_metric_results)

        # Add ROUGE-1
        rouge_values = [r.get("rouge_1") for r in sample_results if r.get("rouge_1") is not None]
        if rouge_values:
            aggregated_results["rouge_1"] = round(sum(rouge_values) / len(rouge_values), self.config.precision_digits)
        else:
            aggregated_results["rouge_1"] = 0.0

        # Add per-sample results if requested
        if self.config.precision_digits:  # Using this as a flag for detailed results
            aggregated_results["per_sample_results"] = sample_results

        return aggregated_results

    def format_results_table(self, results: Dict[str, Any], mode: str = "comprehensive") -> str:
        """Format results in table format.

        Args:
            results: Results from evaluate_batch
            mode: "mave" (MAVE standard), "comprehensive" (all metrics), "comparison" (key metrics)

        Returns:
            Formatted string table
        """
        if mode == "mave":
            # Standard MAVE format
            table = []
            table.append("Metric\t\tScore")
            table.append("-" * 30)
            table.append(f"Precision\t{results.get('precision', 0.0):.4f}")
            table.append(f"Recall\t\t{results.get('recall', 0.0):.4f}")
            table.append(f"F1\t\t{results.get('f1', 0.0):.4f}")
            table.append(f"Exact Match\t{results.get('exact_match', 0.0):.4f}")

        elif mode == "comparison":
            # Key metrics for comparison
            table = []
            table.append("Metric\t\tScore")
            table.append("-" * 30)
            table.append(f"F1 (Micro)\t{results.get('f1', 0.0):.4f}")
            table.append(f"F1 (Macro)\t{results.get('macro_f1', 0.0):.4f}")
            table.append(f"Exact Match\t{results.get('exact_match', 0.0):.4f}")
            table.append(f"Jaccard\t\t{results.get('jaccard', 0.0):.4f}")
            table.append(f"Lenient F1\t{results.get('lenient_f1', 0.0):.4f}")
            table.append(f"ROUGE-1\t\t{results.get('rouge_1', 0.0):.4f}")

        else:  # comprehensive
            # All available metrics
            table = []
            table.append("COMPREHENSIVE EVALUATION RESULTS")
            table.append("=" * 50)

            # Exact matching metrics
            if 'exact' in self.enabled_metrics:
                table.append("\nExact Matching Metrics:")
                table.append("-" * 25)
                table.append(f"Precision\t\t{results.get('precision', 0.0):.4f}")
                table.append(f"Recall\t\t\t{results.get('recall', 0.0):.4f}")
                table.append(f"F1\t\t\t{results.get('f1', 0.0):.4f}")
                table.append(f"Macro-F1\t\t{results.get('macro_f1', 0.0):.4f}")
                table.append(f"Exact Match Rate\t{results.get('exact_match', 0.0):.4f}")

            # Similarity metrics
            if 'similarity' in self.enabled_metrics:
                table.append("\nSimilarity Metrics:")
                table.append("-" * 19)
                table.append(f"Jaccard Similarity\t{results.get('jaccard', 0.0):.4f}")
                table.append(f"Dice Similarity\t\t{results.get('dice', 0.0):.4f}")
                table.append(f"Semantic Match Rate\t{results.get('semantic_match_rate', 0.0):.4f}")

            # Partial evaluation
            if 'partial' in self.enabled_metrics:
                table.append("\nPartial Evaluation:")
                table.append("-" * 19)
                table.append(f"Partial Precision\t{results.get('partial_precision', 0.0):.4f}")
                table.append(f"Partial Recall\t\t{results.get('partial_recall', 0.0):.4f}")
                table.append(f"Partial F1\t\t{results.get('partial_f1', 0.0):.4f}")

            # Lenient evaluation
            if 'lenient' in self.enabled_metrics:
                table.append("\nLenient Evaluation:")
                table.append("-" * 19)
                table.append(f"Lenient Precision\t{results.get('lenient_precision', 0.0):.4f}")
                table.append(f"Lenient Recall\t\t{results.get('lenient_recall', 0.0):.4f}")
                table.append(f"Lenient F1\t\t{results.get('lenient_f1', 0.0):.4f}")

            # Additional metrics
            table.append("\nAdditional Metrics:")
            table.append("-" * 19)
            table.append(f"ROUGE-1\t\t\t{results.get('rouge_1', 0.0):.4f}")

        # Add sample info
        if results.get('skipped_samples', 0) > 0:
            table.append("")
            table.append(f"Note: {results['skipped_samples']} samples skipped (empty GT)")

        return "\n".join(table)

    def get_metric_summary(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Get summary of key metrics for comparison.

        Args:
            results: Results from evaluate_batch

        Returns:
            Dictionary with key metrics only
        """
        summary = {}

        # Always include these if available
        key_metrics = [
            'f1', 'precision', 'recall', 'exact_match',
            'macro_f1', 'jaccard', 'dice',
            'partial_f1', 'lenient_f1', 'rouge_1',
            'semantic_match_rate'
        ]

        for metric in key_metrics:
            if metric in results:
                summary[metric] = results[metric]

        return summary


# Legacy compatibility class
class EntityMetrics(MetricsAggregator):
    """Legacy EntityMetrics class for backward compatibility."""

    def __init__(self, config):
        super().__init__(config, enabled_metrics=['exact', 'similarity', 'partial', 'lenient'])

    # Legacy method aliases
    def micro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Legacy method."""
        exact_metric = self.available_metrics['exact']
        pred_pairs = exact_metric.calculate_single_sample.__self__.extract_attribute_value_pairs(predicted, "minimal")
        true_pairs = exact_metric.calculate_single_sample.__self__.extract_attribute_value_pairs(ground_truth,
                                                                                                 "minimal")
        return exact_metric.calculate_prf(pred_pairs, true_pairs)

    def macro_f1(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Legacy method."""
        if not ground_truth:
            return None
        return self.available_metrics['exact'].macro_averaged_metrics([predicted], [ground_truth])

    def exact_match(self, predicted: List[Dict], ground_truth: List[Dict]) -> float:
        """Legacy method."""
        return self.available_metrics['exact'].exact_match(predicted, ground_truth)

    def evaluate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Legacy method."""
        return super().evaluate_single_sample(predicted, ground_truth)

    def evaluate_batch(self, predictions: List[List[Dict]], ground_truths: List[List[Dict]]) -> Dict[str, Any]:
        """Legacy method."""
        return super().evaluate_batch(predictions, ground_truths)

    def format_results_table(self, results: Dict[str, Any]) -> str:
        """Legacy method."""
        return super().format_results_table(results, mode="mave")
