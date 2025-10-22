"""Entity tag evaluation module for model performance assessment.

This module provides comprehensive evaluation metrics for entity extraction
and tagging tasks, including exact match, partial match, semantic similarity,
and attribute-level analysis.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .config import EvaluationConfig


class EntityTagEvaluator:
    """Comprehensive evaluator for entity extraction and tagging tasks.

    This class provides various evaluation metrics including:
    - Exact match scoring
    - Partial match with token overlap
    - Attribute-level precision/recall/F1
    - Semantic similarity using embeddings
    - 80% accuracy threshold evaluation
    """

    def __init__(
        self, config: EvaluationConfig, embedding_model_name: str = "all-MiniLM-L6-v2"
    ):
        """Initialize evaluator with embedding model for semantic similarity.

        Args:
            config: EvaluationConfig instance with evaluation settings
            embedding_model_name: Name of the sentence transformer model for embeddings
        """
        self.config = config
        self.embedding_model_name = embedding_model_name
        self._embedding_model = None

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy loading of embedding model to avoid initialization overhead."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def exact_match_score(
        self, predicted_entities: List[Dict], true_entities: List[Dict]
    ) -> float:
        """Calculate exact match score between predicted and true entities.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries

        Returns:
            float: 1.0 if all entities match exactly, 0.0 otherwise
        """
        # Convert to comparable format (sorted tuples of name-value pairs)
        pred_set = set()
        true_set = set()

        for entity in predicted_entities:
            entity_name = entity.get("name", "")
            for value in entity.get("values", []):
                pred_set.add((entity_name, str(value).strip()))

        for entity in true_entities:
            entity_name = entity.get("name", "")
            for value in entity.get("values", []):
                true_set.add((entity_name, str(value).strip()))

        return 1.0 if pred_set == true_set else 0.0

    def partial_match_score(
        self, predicted_entities: List[Dict], true_entities: List[Dict]
    ) -> Dict[str, float]:
        """Calculate partial match scores using token overlap.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries

        Returns:
            Dict with precision, recall, and F1 scores for partial matching
        """
        pred_tokens = set()
        true_tokens = set()

        # Extract all tokens from predicted entities with attribute context
        for entity in predicted_entities:
            attr_name = entity.get("name", "")
            for value in entity.get("values", []):
                tokens = self._tokenize(str(value))
                for token in tokens:
                    pred_tokens.add((attr_name, token))

        # Extract all tokens from true entities with attribute context
        for entity in true_entities:
            attr_name = entity.get("name", "")
            for value in entity.get("values", []):
                tokens = self._tokenize(str(value))
                for token in tokens:
                    true_tokens.add((attr_name, token))

        # Calculate precision, recall, F1
        if len(pred_tokens) == 0:
            precision = 0.0
        else:
            precision = len(pred_tokens.intersection(true_tokens)) / len(pred_tokens)

        if len(true_tokens) == 0:
            recall = 0.0
        else:
            recall = len(pred_tokens.intersection(true_tokens)) / len(true_tokens)

        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        return {
            "precision": round(precision, self.config.precision_digits),
            "recall": round(recall, self.config.precision_digits),
            "f1": round(f1, self.config.precision_digits),
        }

    def attribute_level_metrics(
        self, predicted_entities: List[Dict], true_entities: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate precision, recall, F1 for each attribute separately.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries

        Returns:
            Dict mapping attribute names to their metrics
        """
        # Group values by attribute name
        pred_attrs = defaultdict(set)
        true_attrs = defaultdict(set)

        for entity in predicted_entities:
            attr_name = entity.get("name", "")
            for value in entity.get("values", []):
                pred_attrs[attr_name].add(str(value).strip())

        for entity in true_entities:
            attr_name = entity.get("name", "")
            for value in entity.get("values", []):
                true_attrs[attr_name].add(str(value).strip())

        results = {}
        all_attrs = set(list(pred_attrs.keys()) + list(true_attrs.keys()))

        for attr_name in all_attrs:
            pred_values = pred_attrs[attr_name]
            true_values = true_attrs[attr_name]

            # Calculate TP, FP, FN for this attribute
            tp = len(pred_values.intersection(true_values))
            fp = len(pred_values - true_values)
            fn = len(true_values - pred_values)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * (precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            results[attr_name] = {
                "precision": round(precision, self.config.precision_digits),
                "recall": round(recall, self.config.precision_digits),
                "f1": round(f1, self.config.precision_digits),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "support": len(
                    true_values
                ),  # Number of true instances for this attribute
            }

        return results

    def semantic_similarity_score(
        self,
        predicted_entities: List[Dict],
        true_entities: List[Dict],
        threshold: Optional[float] = None,
    ) -> Dict[str, float]:
        """Calculate semantic similarity-based scores using sentence embeddings.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries
            threshold: Similarity threshold for matching (defaults to config value)

        Returns:
            Dict with semantic precision, recall, and F1 scores
        """
        if threshold is None:
            threshold = self.config.similarity_threshold

        # Group values by attribute
        pred_by_attr = defaultdict(list)
        true_by_attr = defaultdict(list)

        for entity in predicted_entities:
            attr_name = entity.get("name", "")
            pred_by_attr[attr_name].extend([str(v) for v in entity.get("values", [])])

        for entity in true_entities:
            attr_name = entity.get("name", "")
            true_by_attr[attr_name].extend([str(v) for v in entity.get("values", [])])

        all_attrs = set(list(pred_by_attr.keys()) + list(true_by_attr.keys()))

        total_matches = 0
        total_predicted = 0
        total_true = 0

        for attr_name in all_attrs:
            pred_values = pred_by_attr[attr_name]
            true_values = true_by_attr[attr_name]

            if not pred_values or not true_values:
                total_predicted += len(pred_values)
                total_true += len(true_values)
                continue

            # Calculate embeddings
            try:
                pred_embeddings = self.embedding_model.encode(pred_values)
                true_embeddings = self.embedding_model.encode(true_values)

                # Ensure 2D arrays
                if pred_embeddings.ndim == 1:
                    pred_embeddings = pred_embeddings.reshape(1, -1)
                if true_embeddings.ndim == 1:
                    true_embeddings = true_embeddings.reshape(1, -1)

                # Calculate similarity matrix
                similarity_matrix = cosine_similarity(pred_embeddings, true_embeddings)

                # Count matches above threshold
                matches = 0
                for i in range(len(pred_values)):
                    max_similarity = np.max(similarity_matrix[i])
                    if max_similarity >= threshold:
                        matches += 1

                total_matches += matches

            except Exception as e:
                print(
                    f"Warning: Error calculating embeddings for attribute '{attr_name}': {e}"
                )
                # Fall back to exact string matching for this attribute
                pred_set = set(pred_values)
                true_set = set(true_values)
                total_matches += len(pred_set.intersection(true_set))

            total_predicted += len(pred_values)
            total_true += len(true_values)

        precision = total_matches / total_predicted if total_predicted > 0 else 0.0
        recall = total_matches / total_true if total_true > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "semantic_precision": round(precision, self.config.precision_digits),
            "semantic_recall": round(recall, self.config.precision_digits),
            "semantic_f1": round(f1, self.config.precision_digits),
            "threshold_used": threshold,
        }

    def eighty_percent_accuracy(
        self, predicted_entities: List[Dict], true_entities: List[Dict]
    ) -> float:
        """Calculate 80% accuracy as used in ViOC-AG paper.

        Considers prediction correct if 80% of generated output matches golden label.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries

        Returns:
            float: 1.0 if accuracy >= 80%, 0.0 otherwise
        """
        # Flatten all values to tokens
        pred_tokens = []
        true_tokens = []

        for entity in predicted_entities:
            for value in entity.get("values", []):
                pred_tokens.extend(self._tokenize(str(value)))

        for entity in true_entities:
            for value in entity.get("values", []):
                true_tokens.extend(self._tokenize(str(value)))

        if len(pred_tokens) == 0:
            return 0.0

        # Calculate overlap
        pred_set = set(pred_tokens)
        true_set = set(true_tokens)
        overlap = len(pred_set.intersection(true_set))

        accuracy = overlap / len(pred_set)
        return 1.0 if accuracy >= 0.8 else 0.0

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization helper.

        Args:
            text: Input text to tokenize

        Returns:
            List of lowercase tokens
        """
        # Convert to lowercase and split by whitespace and punctuation
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return [token for token in text.split() if token.strip()]

    def evaluate_single_sample(
        self, predicted_entities: List[Dict], true_entities: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate a single sample and return all metrics.

        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries

        Returns:
            Dict containing all evaluation metrics for the sample
        """
        results = {
            "exact_match": self.exact_match_score(predicted_entities, true_entities),
            "partial_match": self.partial_match_score(
                predicted_entities, true_entities
            ),
            "attribute_metrics": self.attribute_level_metrics(
                predicted_entities, true_entities
            ),
            "semantic_similarity": self.semantic_similarity_score(
                predicted_entities, true_entities
            ),
            "eighty_percent_accuracy": self.eighty_percent_accuracy(
                predicted_entities, true_entities
            ),
        }
        return results

    def evaluate_batch(
        self, predictions: List[List[Dict]], ground_truths: List[List[Dict]]
    ) -> Dict[str, Any]:
        """Evaluate a batch of predictions and return macro/micro averages.

        Args:
            predictions: List of prediction lists (one per sample)
            ground_truths: List of ground truth lists (one per sample)

        Returns:
            Dict containing macro averages, micro averages, and per-sample results
        """
        if len(predictions) != len(ground_truths):
            raise ValueError("Number of predictions must match number of ground truths")

        sample_results = []

        # Evaluate each sample
        for i, (pred, true) in enumerate(zip(predictions, ground_truths)):
            try:
                sample_result = self.evaluate_single_sample(pred, true)
                sample_result["sample_index"] = i
                sample_results.append(sample_result)
            except Exception as e:
                print(f"Warning: Error evaluating sample {i}: {e}")
                # Add empty result for failed sample
                sample_results.append(
                    {
                        "sample_index": i,
                        "error": str(e),
                        "exact_match": 0.0,
                        "partial_match": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                        "semantic_similarity": {
                            "semantic_precision": 0.0,
                            "semantic_recall": 0.0,
                            "semantic_f1": 0.0,
                        },
                        "eighty_percent_accuracy": 0.0,
                    }
                )

        # Calculate macro averages (average across samples)
        valid_results = [r for r in sample_results if "error" not in r]

        if not valid_results:
            raise RuntimeError("No valid samples could be evaluated")

        macro_results = {
            "exact_match": np.mean([r["exact_match"] for r in valid_results]),
            "partial_match_precision": np.mean(
                [r["partial_match"]["precision"] for r in valid_results]
            ),
            "partial_match_recall": np.mean(
                [r["partial_match"]["recall"] for r in valid_results]
            ),
            "partial_match_f1": np.mean(
                [r["partial_match"]["f1"] for r in valid_results]
            ),
            "semantic_precision": np.mean(
                [r["semantic_similarity"]["semantic_precision"] for r in valid_results]
            ),
            "semantic_recall": np.mean(
                [r["semantic_similarity"]["semantic_recall"] for r in valid_results]
            ),
            "semantic_f1": np.mean(
                [r["semantic_similarity"]["semantic_f1"] for r in valid_results]
            ),
            "eighty_percent_accuracy": np.mean(
                [r["eighty_percent_accuracy"] for r in valid_results]
            ),
            "num_valid_samples": len(valid_results),
            "num_failed_samples": len(sample_results) - len(valid_results),
        }

        # Round macro results
        for key in macro_results:
            if isinstance(macro_results[key], (float, np.floating)):
                macro_results[key] = round(
                    macro_results[key], self.config.precision_digits
                )

        # Calculate micro averages (pool all predictions together)
        try:
            all_pred_flat = [entity for sample in predictions for entity in sample]
            all_true_flat = [entity for sample in ground_truths for entity in sample]

            micro_partial = self.partial_match_score(all_pred_flat, all_true_flat)
            micro_semantic = self.semantic_similarity_score(
                all_pred_flat, all_true_flat
            )

            micro_results = {
                "partial_match_precision": micro_partial["precision"],
                "partial_match_recall": micro_partial["recall"],
                "partial_match_f1": micro_partial["f1"],
                "semantic_precision": micro_semantic["semantic_precision"],
                "semantic_recall": micro_semantic["semantic_recall"],
                "semantic_f1": micro_semantic["semantic_f1"],
            }
        except Exception as e:
            print(f"Warning: Error calculating micro averages: {e}")
            micro_results = {
                "error": str(e),
                "partial_match_precision": 0.0,
                "partial_match_recall": 0.0,
                "partial_match_f1": 0.0,
                "semantic_precision": 0.0,
                "semantic_recall": 0.0,
                "semantic_f1": 0.0,
            }

        return {
            "macro_averages": macro_results,
            "micro_averages": micro_results,
            "per_sample_results": sample_results,
            "summary": {
                "total_samples": len(sample_results),
                "valid_samples": len(valid_results),
                "failed_samples": len(sample_results) - len(valid_results),
                "success_rate": (
                    len(valid_results) / len(sample_results) if sample_results else 0.0
                ),
            },
        }

    def calculate_attribute_summary(
        self, batch_results: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics across all attributes from batch results.

        Args:
            batch_results: Results from evaluate_batch method

        Returns:
            Dict mapping attribute names to their aggregated metrics
        """
        attribute_stats = defaultdict(
            lambda: {"precision": [], "recall": [], "f1": [], "support": []}
        )

        # Collect metrics for each attribute across all samples
        for sample_result in batch_results["per_sample_results"]:
            if "error" in sample_result:
                continue

            attr_metrics = sample_result.get("attribute_metrics", {})
            for attr_name, metrics in attr_metrics.items():
                attribute_stats[attr_name]["precision"].append(metrics["precision"])
                attribute_stats[attr_name]["recall"].append(metrics["recall"])
                attribute_stats[attr_name]["f1"].append(metrics["f1"])
                attribute_stats[attr_name]["support"].append(metrics["support"])

        # Calculate summary statistics for each attribute
        summary = {}
        for attr_name, stats in attribute_stats.items():
            summary[attr_name] = {
                "mean_precision": round(
                    np.mean(stats["precision"]), self.config.precision_digits
                ),
                "mean_recall": round(
                    np.mean(stats["recall"]), self.config.precision_digits
                ),
                "mean_f1": round(np.mean(stats["f1"]), self.config.precision_digits),
                "std_precision": round(
                    np.std(stats["precision"]), self.config.precision_digits
                ),
                "std_recall": round(
                    np.std(stats["recall"]), self.config.precision_digits
                ),
                "std_f1": round(np.std(stats["f1"]), self.config.precision_digits),
                "total_support": sum(stats["support"]),
                "num_samples": len(stats["precision"]),
            }

        return summary
