"""Base classes for evaluation metrics.

Provides abstract interfaces and common utilities for all metric implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple, Optional
from pathlib import Path
import re
import json

class BaseMetric(ABC):
    """Abstract base class for all evaluation metrics."""

    def __init__(self, config):
        """Initialize metric with configuration.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config

    @abstractmethod
    def calculate_single_sample(self, predicted: List[Dict], ground_truth: List[Dict]) -> Dict[str, Any]:
        """Calculate metric for a single sample.

        Args:
            predicted: Predicted entities for one sample
            ground_truth: Ground truth entities for one sample

        Returns:
            Dictionary with metric results
        """
        pass

    @abstractmethod
    def aggregate_batch_results(self, sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results across batch.

        Args:
            sample_results: List of per-sample results

        Returns:
            Aggregated results
        """
        pass

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """Return the name of this metric."""
        pass


class EntityProcessor:
    """Common utilities for processing entity structures."""

    @staticmethod
    def normalize_text(text: str, mode: str = "minimal") -> str:
        """Normalize text based on specified mode.

        Args:
            text: Input text
            mode: "minimal" (just strip), "standard" (lower+strip+spaces),
                  "semantic" (for similarity matching)
        """
        if not text:
            return ""

        text = str(text)

        if mode == "minimal":
            return text.strip()
        elif mode == "standard":
            return re.sub(r'\s+', ' ', text.lower().strip())
        elif mode == "semantic":
            # More aggressive normalization for semantic similarity
            text = re.sub(r'[^\w\s]', ' ', text.lower())  # Remove punctuation
            text = re.sub(r'\s+', ' ', text.strip())
            return text

        return text.strip()

    @staticmethod
    def extract_attribute_value_pairs(entities: List[Dict],
                                      normalize_mode: str = "minimal") -> Set[Tuple[str, str]]:
        """Extract (attribute, value) pairs with specified normalization."""
        pairs = set()
        for entity in entities:
            if isinstance(entity, dict):
                name = EntityProcessor.normalize_text(entity.get('name', ''), normalize_mode)
                values = entity.get('values', [])
                if isinstance(values, list) and name:
                    for value in values:
                        normalized_value = EntityProcessor.normalize_text(str(value), normalize_mode)
                        if normalized_value:
                            pairs.add((name, normalized_value))
        return pairs

    @staticmethod
    def extract_values_only(entities: List[Dict], normalize_mode: str = "minimal") -> Set[str]:
        """Extract only values (ignoring attributes) for certain metrics."""
        values = set()
        for entity in entities:
            if isinstance(entity, dict):
                entity_values = entity.get('values', [])
                if isinstance(entity_values, list):
                    for value in entity_values:
                        normalized_value = EntityProcessor.normalize_text(str(value), normalize_mode)
                        if normalized_value:
                            values.add(normalized_value)
        return values

    @staticmethod
    def load_entity_weights(weights_path: Path) -> Dict[str, Dict[str, float]]:
        """Load entity weights from JSON file."""
        try:
            with open(weights_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load entity weights from {weights_path}: {e}")
            return {}

    @staticmethod
    def get_entity_weight(entity_name: str, category: str,
                          entity_weights: Dict[str, Dict[str, float]]) -> float:
        """Get weight for specific entity in category."""
        category_weights = entity_weights.get(category, {})
        return category_weights.get(entity_name.lower().strip(), 1.0)

    @staticmethod
    def detect_best_category(sample_entities: List[Dict], entity_weights: Dict[str, Dict[str, float]]) -> str:
        """
        Detect the best matching category for a sample based on its attributes.

        Args:
            sample_entities: List of entity dictionaries for one sample
            entity_weights: Loaded entity weights dictionary

        Returns:
            str: Best matching category name
        """
        if not sample_entities or not entity_weights:
            return list(entity_weights.keys())[0] if entity_weights else "unknown"

        # Extract attribute names from the sample
        sample_attributes = set()
        for entity in sample_entities:
            if isinstance(entity, dict):
                attr_name = entity.get('name', '').strip().lower()
                if attr_name:
                    sample_attributes.add(attr_name)

        if not sample_attributes:
            return list(entity_weights.keys())[0] if entity_weights else "unknown"

        # Calculate match score for each category
        best_category = None
        best_score = -1

        for category, category_weights in entity_weights.items():
            # Calculate overlap between sample attributes and category attributes
            category_attributes = set(attr.lower() for attr in category_weights.keys())

            # Calculate Jaccard similarity
            intersection = len(sample_attributes & category_attributes)
            union = len(sample_attributes | category_attributes)

            if union > 0:
                jaccard_score = intersection / union
            else:
                jaccard_score = 0

            # Also consider weighted importance of matched attributes
            weighted_score = 0
            total_weight = 0
            for attr in sample_attributes:
                if attr in category_attributes:
                    # Find the original case attribute name
                    for orig_attr, weight in category_weights.items():
                        if orig_attr.lower() == attr:
                            weighted_score += weight
                            total_weight += weight
                            break

            # Combine Jaccard and weighted scores
            if total_weight > 0:
                final_score = jaccard_score * 0.3 + (weighted_score / total_weight) * 0.7
            else:
                final_score = jaccard_score

            if final_score > best_score:
                best_score = final_score
                best_category = category

        return best_category if best_category else list(entity_weights.keys())[0]

    @staticmethod
    def get_categories_for_samples(ground_truths: List[List[Dict]], entity_weights: Dict[str, Dict[str, float]]) -> \
    List[str]:
        """
        Get categories for all samples in a batch.

        Args:
            ground_truths: List of ground truth samples
            entity_weights: Loaded entity weights dictionary

        Returns:
            List[str]: Category for each sample
        """
        categories = []
        for gt_sample in ground_truths:
            category = EntityProcessor.detect_best_category(gt_sample, entity_weights)
            categories.append(category)

        return categories
