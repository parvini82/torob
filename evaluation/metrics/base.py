"""Base classes for evaluation metrics.

Provides abstract interfaces and common utilities for all metric implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple, Optional
from pathlib import Path

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
            import re
            return re.sub(r'\s+', ' ', text.lower().strip())
        elif mode == "semantic":
            import re
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
