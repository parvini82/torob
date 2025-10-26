"""Configuration classes for data operations.

This module contains separate configuration classes for download and sample generation
operations, allowing independent usage of each component.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

project_root = Path(__file__).resolve().parent.parent


@dataclass
class DownloadConfig:
    """Configuration for data downloading operations.

    Contains settings for downloading data from Google Drive and file extraction.
    """

    # Google Drive settings
    drive_file_id: str

    # Directory paths
    data_dir: Path

    @property
    def raw_data_dir(self) -> Path:
        """Get raw data directory path."""
        return self.data_dir / "raw"

    @property
    def google_drive_url(self) -> str:
        """Generate Google Drive download URL from file ID."""
        return f"https://drive.google.com/uc?id={self.drive_file_id}"

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class SampleConfig:
    """Configuration for toy sample generation.

    Contains all parameters needed for generating balanced toy samples
    from product datasets.
    """

    # Basic sample settings
    target_sample_size: int = 300

    # Group composition targets (must sum to 1.0)
    group_composition: Dict[str, float] = field(default_factory=lambda: {
        "defined": 0.30,
        "rare": 0.30,
        "unknown": 0.40
    })

    # Entity settings
    core_entities: Set[str] = field(default_factory=lambda: {
        "نوع کلی", "رنگ", "جنس", "طرح", "ویژگی‌ها"
    })

    rare_entity_names: Set[str] = field(default_factory=lambda: {
        "نوع یقه", "فصل", "نوع بسته شدن", "نوع آستین"
    })

    noisy_entity_names: Set[str] = field(default_factory=lambda: {
        "مدل سازگار", "tipo de manga", "Estilo", "سبک"
    })

    # Group definitions
    defined_groups: Set[str] = field(default_factory=lambda: {
        "زنانه", "مردانه", "دخترانه", "پسرانه"
    })

    rare_groups: Set[str] = field(default_factory=lambda: {
        "بچگانه", "لوازم خانگی", "لوازم دیجیتال"
    })

    # Title length configuration
    title_length_config: Dict[str, Any] = field(default_factory=lambda: {
        "short_ratio": 0.20,
        "medium_ratio": 0.45,
        "long_ratio": 0.10,
        "short_max": 20,
        "medium_range": (30, 50),
        "long_min": 100,
    })

    # Quality score mapping
    quality_score_bands: List[Tuple[str, int, int]] = field(default_factory=lambda: [
        ("Poor", 0, 59),
        ("Fair", 60, 79),
        ("Good", 80, 89),
        ("Excellent", 90, 100),
    ])

    # Product variety
    head_products: Set[str] = field(default_factory=lambda: {
        "پیراهن", "تیشرت", "کفش", "ساعت مچی", "مانتو"
    })

    tail_products: Set[str] = field(default_factory=lambda: {
        "جاکلیدی", "آینه تاشو", "نیم‌ست", "کیف پول"
    })

    # Image processing
    allowed_image_formats: Set[str] = field(default_factory=lambda: {
        ".jpg", ".jpeg", ".png", ".webp"
    })

    dedupe_by_content_hash: bool = True

    # Outlier detection
    outlier_ratio: float = 0.05
    outlier_rules: Dict[str, int] = field(default_factory=lambda: {
        "min_title_length": 140,
        "min_entity_count": 6
    })

    # Output directory
    processed_data_dir: Path = Path(project_root / "data/processed")

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
