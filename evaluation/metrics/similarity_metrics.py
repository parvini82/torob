"""Similarity-based metrics for more flexible evaluation.

Implements Jaccard, Dice similarity, and semantic similarity metrics
for cases where exact matching is too strict.
"""

from typing import List, Dict, Any, Set
import math

from .base import BaseMetric, EntityProcessor
from sentence_transformers import SentenceTransformer

import os
from dotenv import load_dotenv
load_dotenv()
class SimilarityMetrics(BaseMetric):
    """Similarity-based metrics for flexible evaluation."""

    def __init__(self, config):
        super().__init__(config)
        self._semantic_model = None

    @property
    def metric_name(self) -> str:
        return "similarity"

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity coefficient."""
        if not set1 and not set2:
            return 1.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def dice_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Dice similarity coefficient."""
        if not set1 and not set2:
            return 1.0

        intersection = len(set1 & set2)
        total = len(set1) + len(set2)

        return (2 * intersection) / total if total > 0 else 0.0

    def _get_semantic_model(self):
        """Lazy load semantic similarity model."""
        if self._semantic_model is None:
            try:

                # Use multilingual model for Persian support
                semantic_model_name = os.getenv("SEMANTIC_MODEL",'paraphrase-multilingual-MiniLM-L12-v2')
                self._semantic_model = SentenceTransformer(semantic_model_name)
            except ImportError:
                print("Warning: sentence-transformers not available, semantic similarity disabled")
                return None
        return self._semantic_model

    def semantic_similarity(self, text1: str, text2: str, threshold: float = 0.8) -> float:
        """Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold for binary classification

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 and not text2:
            return 1.0

        if not text1 or not text2:
            return 0.0

        model = self._get_semantic_model()
        if model is None:
            # Fallback to simple string similarity
            return 1.0 if text1.lower() == text2.lower() else 0.0

        try:
            # Normalize texts for semantic comparison
            norm_text1 = EntityProcessor.normalize_text(text1, "semantic")
            norm_text2 = EntityProcessor.normalize_text(text2, "semantic")

            if norm_text1 == norm_text2:
                return 1.0

            # Calculate embeddings and cosine similarity
            embeddings = model.encode([norm_text1, norm_text2])

            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(embeddings[0], embeddings[1]))
            norm_a = math.sqrt(sum(a * a for a in embeddings[0]))
            norm_b = math.sqrt(sum(b * b for b in embeddings[1]))

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            print(f"Warning: Semantic similarity calculation failed: {e}")
            # Fallback to exact match
            return 1.0 if text1.lower().strip() == text2.lower().strip() else 0.0

    def calculate_value_similarities(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, float]:
        """Calculate similarity metrics focusing on attribute values."""
        if not ground_truth:
            return {
                "jaccard": 1.0 if not predicted else 0.0,
                "dice": 1.0 if not predicted else 0.0,
                "semantic_match_rate": 1.0 if not predicted else 0.0
            }

        # Extract values with semantic normalization for similarity
        pred_values = EntityProcessor.extract_values_only(predicted, "semantic")
        true_values = EntityProcessor.extract_values_only(ground_truth, "semantic")

        # Calculate Jaccard and Dice
        jaccard = self.jaccard_similarity(pred_values, true_values)
        dice = self.dice_similarity(pred_values, true_values)

        # Calculate semantic similarity matches
        semantic_matches = 0
        total_comparisons = 0

        for true_val in true_values:
            best_similarity = 0.0
            for pred_val in pred_values:
                similarity = self.semantic_similarity(pred_val, true_val)
                best_similarity = max(best_similarity, similarity)

            if best_similarity >= 0.8:  # Threshold for semantic match
                semantic_matches += 1
            total_comparisons += 1

        semantic_rate = semantic_matches / total_comparisons if total_comparisons > 0 else 0.0

        return {
            "jaccard": round(jaccard, self.config.precision_digits),
            "dice": round(dice, self.config.precision_digits),
            "semantic_match_rate": round(semantic_rate, self.config.precision_digits)
        }

    def calculate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Calculate similarity metrics for single sample."""
        return self.calculate_value_similarities(predicted, ground_truth)

    def aggregate_batch_results(self, sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate similarity results across batch."""
        if not sample_results:
            return {"jaccard": 0.0, "dice": 0.0, "semantic_match_rate": 0.0}

        avg_jaccard = sum(r["jaccard"] for r in sample_results) / len(sample_results)
        avg_dice = sum(r["dice"] for r in sample_results) / len(sample_results)
        avg_semantic = sum(r["semantic_match_rate"] for r in sample_results) / len(sample_results)

        return {
            "jaccard": round(avg_jaccard, self.config.precision_digits),
            "dice": round(avg_dice, self.config.precision_digits),
            "semantic_match_rate": round(avg_semantic, self.config.precision_digits)
        }
