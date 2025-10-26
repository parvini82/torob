"""Configuration settings for data processing and toy sample generation.

This module contains all configuration parameters used throughout the data pipeline,
including sampling strategies, quality thresholds, and file paths.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ---- Define the root of the project (absolute path) ----
# Go up two levels: from /src/config → /src → / (project root)
ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class DataConfig:
    """Configuration class for data processing and toy sample generation.

    This class encapsulates all configuration parameters needed for:
    - Data downloading and extraction
    - Toy sample generation with balanced composition
    - Quality assessment and filtering
    - Evaluation setup
    """

    # Data paths
    data_dir: Path = ROOT_DIR / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"

    # Google Drive settings
    google_drive_file_id: str = "1Coixw-ZELOorizi4K-RSBtzDnRAQ2c_g"

    # Toy sample configuration
    target_sample_size: int = 300

    # Group composition targets (must sum to 1.0)
    group_composition: Dict[str, float] = None

    # Entity and quality settings
    core_entities: Set[str] = None
    rare_entity_names: Set[str] = None
    defined_groups: Set[str] = None
    rare_groups: Set[str] = None

    # Title length configuration
    title_length_config: Dict[str, Any] = None

    # Quality mapping
    quality_score_bands: List[Tuple[str, int, int]] = None

    # Product variety
    head_products: Set[str] = None
    tail_products: Set[str] = None

    # Image processing
    allowed_image_formats: Set[str] = None
    dedupe_by_content_hash: bool = True

    # Outlier detection
    outlier_ratio: float = 0.05
    outlier_rules: Dict[str, int] = None

    # Noisy entities
    noisy_entity_names: Set[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.group_composition is None:
            self.group_composition = {"defined": 0.30, "rare": 0.30, "unknown": 0.40}

        if self.core_entities is None:
            self.core_entities = {"نوع کلی", "رنگ", "جنس", "طرح", "ویژگی‌ها"}

        if self.rare_entity_names is None:
            self.rare_entity_names = {"نوع یقه", "فصل", "نوع بسته شدن", "نوع آستین"}

        if self.defined_groups is None:
            self.defined_groups = {"زنانه", "مردانه", "دخترانه", "پسرانه"}

        if self.rare_groups is None:
            self.rare_groups = {"بچگانه", "لوازم خانگی", "لوازم دیجیتال"}

        if self.title_length_config is None:
            self.title_length_config = {
                "short_ratio": 0.20,
                "medium_ratio": 0.45,
                "long_ratio": 0.10,
                "short_max": 20,
                "medium_range": (30, 50),
                "long_min": 100,
            }

        if self.quality_score_bands is None:
            self.quality_score_bands = [
                ("Poor", 0, 59),
                ("Fair", 60, 79),
                ("Good", 80, 89),
                ("Excellent", 90, 100),
            ]

        if self.head_products is None:
            self.head_products = {"پیراهن", "تیشرت", "کفش", "ساعت مچی", "مانتو"}

        if self.tail_products is None:
            self.tail_products = {"جاکلیدی", "آینه تاشو", "نیم‌ست", "کیف پول"}

        if self.allowed_image_formats is None:
            self.allowed_image_formats = {".jpg", ".jpeg", ".png", ".webp"}

        if self.outlier_rules is None:
            self.outlier_rules = {"min_title_length": 140, "min_entity_count": 6}

        if self.noisy_entity_names is None:
            self.noisy_entity_names = {"مدل سازگار", "tipo de manga", "Estilo", "سبک"}

    @property
    def google_drive_url(self) -> str:
        """Generate Google Drive download URL from file ID."""
        return f"https://drive.google.com/uc?id={self.google_drive_file_id}"

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
