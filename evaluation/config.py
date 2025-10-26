"""Simple configuration for evaluation operations.

Contains basic settings for model evaluation and metrics calculation.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List


@dataclass
class EvaluationConfig:
    """Simple configuration for evaluation processes."""

    # Output directories
    results_dir: Path = Path("evaluation/results")

    # Model settings
    model_name: str = "default_model"

    # Metrics settings
    precision_digits: int = 4

    # Entity matching settings
    exact_match_threshold: float = 1.0
    partial_match_threshold: float = 0.8

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
