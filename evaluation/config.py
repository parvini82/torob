"""Simple configuration for evaluation operations.

Contains basic settings for model evaluation and metrics calculation.
"""

from dataclasses import dataclass
from pathlib import Path



import os
import time

from dotenv import load_dotenv

# Load .env file
load_dotenv()

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
TRANSLATE_MODEL: str = os.getenv(
    "TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free"
)




@dataclass
class EvaluationConfig:
    """Simple configuration for evaluation processes."""

    # Output directories
    results_dir: Path = Path("evaluation/results")

    # Model settings
    # Combine both model names into one descriptive string
    model_name: str = f"{VISION_MODEL.split('/')[-1]}__{TRANSLATE_MODEL.split('/')[-1]}"

    # Metrics settings
    precision_digits: int = 4

    # Entity matching settings
    exact_match_threshold: float = 1.0
    partial_match_threshold: float = 0.8

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
