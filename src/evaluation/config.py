"""Configuration for evaluation metrics and processes.

This module defines evaluation settings, thresholds, and parameters
for comprehensive model assessment.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class EvaluationConfig:
    """Configuration class for evaluation processes.

    Contains settings for:
    - Metric calculation parameters
    - Quality thresholds
    - Output formatting
    - File paths for results
    """

    # Output paths
    results_dir: Path = Path("evaluation/results")
    reports_dir: Path = Path("evaluation/reports")

    # Metric calculation settings
    similarity_threshold: float = 0.8
    precision_digits: int = 4

    # Quality assessment bands
    quality_bands: List[str] = None
    quality_weights: Dict[str, float] = None

    # Entity evaluation settings
    core_entity_weight: float = 1.5
    rare_entity_weight: float = 1.0

    # Coverage requirements
    min_coverage_threshold: float = 0.7
    target_diversity_score: float = 0.8

    # Report formatting
    include_detailed_breakdown: bool = True
    generate_visualizations: bool = False

    # Sampling validation
    validate_sample_composition: bool = True
    tolerance_margin: float = 0.05  # 5% tolerance for quotas

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.quality_bands is None:
            self.quality_bands = ["Poor", "Fair", "Good", "Excellent"]

        if self.quality_weights is None:
            self.quality_weights = {
                "Poor": 0.5,
                "Fair": 1.0,
                "Good": 1.2,
                "Excellent": 1.5,
            }

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
