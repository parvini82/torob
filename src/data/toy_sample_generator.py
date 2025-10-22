"""Toy sample generation for evaluation purposes.

This module provides sophisticated sampling strategies to create balanced
toy samples from product datasets for evaluation and testing.
"""

import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .config import DataConfig

# Type alias for better readability
Product = Dict[str, Any]


class ToySampleGenerator:
    """Generates balanced toy samples from product datasets.

    This class implements a sophisticated sampling strategy that ensures:
    - Balanced representation across different product groups
    - Coverage of core and rare entities
    - Diverse title lengths and entity counts
    - Quality distribution control
    - Image deduplication
    - Outlier inclusion for robustness testing
    """

    def __init__(self, config: DataConfig):
        """Initialize generator with configuration.

        Args:
            config: DataConfig instance with sampling parameters
        """
        self.config = config

    # Utility methods for product analysis
    def get_title_length(self, product: Product) -> int:
        """Get title length in characters safely.

        Args:
            product: Product dictionary

        Returns:
            int: Title length, 0 if no title
        """
        title = product.get("title") or ""
        return len(title)

    def count_entities(self, product: Product) -> int:
        """Count number of entity objects in product.

        Args:
            product: Product dictionary

        Returns:
            int: Number of entities
        """
        entities = product.get("entities") or []
        return len(entities)

    def get_entity_names(self, product: Product) -> Set[str]:
        """Extract set of entity names from product.

        Args:
            product: Product dictionary

        Returns:
            Set[str]: Set of entity name strings
        """
        entities = product.get("entities") or []
        return {
            e.get("name") for e in entities if isinstance(e, dict) and e.get("name")
        }

    def get_product_type(self, product: Product) -> str:
        """Get normalized product type.

        Args:
            product: Product dictionary

        Returns:
            str: Normalized product type or empty string
        """
        return (product.get("product") or "").strip()

    def get_group_name(self, product: Product) -> str:
        """Get normalized group name with fallback.

        Args:
            product: Product dictionary

        Returns:
            str: Group name or 'نامشخص' if missing
        """
        group = (product.get("group") or "").strip()
        return group if group else "نامشخص"

    def infer_quality_band(self, product: Product) -> str:
        """Map quality score to quality band.

        Args:
            product: Product dictionary with quality_score or quality_band

        Returns:
            str: Quality band (Poor, Fair, Good, Excellent)
        """
        # Check if quality band already exists
        band = product.get("quality_band")
        if band:
            return band

        # Map from numeric score
        score = product.get("quality_score")
        if isinstance(score, (int, float)):
            for name, low, high in self.config.quality_score_bands:
                if low <= score <= high:
                    return name

        # Default to Fair if no quality info
        return "Fair"

    def get_url_extension(self, url: str) -> str:
        """Extract file extension from URL.

        Args:
            url: Image URL string

        Returns:
            str: Lowercase file extension (e.g., '.jpg')
        """
        match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", url or "")
        return f".{match.group(1).lower()}" if match else ""

    def is_image_url_valid(self, product: Product) -> bool:
        """Check if product has valid image URL.

        Args:
            product: Product dictionary

        Returns:
            bool: True if image URL is valid
        """
        url = product.get("image_url") or ""
        if not url.startswith("http"):
            return False

        ext = self.get_url_extension(url)
        return (ext in self.config.allowed_image_formats) if ext else True

    def get_image_content_hash(self, product: Product) -> str:
        """Generate hash of image URL for deduplication.

        Args:
            product: Product dictionary

        Returns:
            str: MD5 hash of normalized URL
        """
        url = (product.get("image_url") or "").strip().lower()
        return hashlib.md5(url.encode("utf-8")).hexdigest() if url else ""

    def is_outlier(self, product: Product) -> bool:
        """Check if product meets outlier criteria.

        Args:
            product: Product dictionary

        Returns:
            bool: True if product is considered an outlier
        """
        rules = self.config.outlier_rules
        return (
            self.get_title_length(product) >= rules["min_title_length"]
            or self.count_entities(product) >= rules["min_entity_count"]
        )

    def contains_any_entity(self, product: Product, entity_names: Set[str]) -> bool:
        """Check if product contains any of the specified entities.

        Args:
            product: Product dictionary
            entity_names: Set of entity names to check for

        Returns:
            bool: True if product has any of the specified entities
        """
        product_entities = self.get_entity_names(product)
        return len(product_entities.intersection(entity_names)) > 0

    # Indexing and filtering methods
    def index_products(self, products: List[Product]) -> Dict[str, List[Product]]:
        """Create indices for efficient sampling by different criteria.

        Args:
            products: List of product dictionaries

        Returns:
            Dict with categorized product lists
        """
        indices = {
            "by_group_defined": [],
            "by_group_rare": [],
            "by_group_unknown": [],
            "has_core_entities": [],
            "has_rare_entities": [],
            "zero_entities": [],
            "four_plus_entities": [],
            "by_title_short": [],
            "by_title_medium": [],
            "by_title_long": [],
            "quality_poor": [],
            "quality_fair": [],
            "quality_good": [],
            "quality_excellent": [],
            "head_products": [],
            "tail_products": [],
            "images_valid": [],
            "outliers": [],
            "noisy_entities": [],
        }

        title_config = self.config.title_length_config
        short_max = title_config["short_max"]
        med_lo, med_hi = title_config["medium_range"]
        long_min = title_config["long_min"]

        for product in products:
            # Group categorization
            group = self.get_group_name(product)
            if group == "نامشخص":
                indices["by_group_unknown"].append(product)
            elif group in self.config.defined_groups:
                indices["by_group_defined"].append(product)
            else:
                # Treat as rare (including explicitly rare and long-tail groups)
                indices["by_group_rare"].append(product)

            # Entity categorization
            entity_names = self.get_entity_names(product)
            entity_count = len(entity_names)

            if entity_count == 0:
                indices["zero_entities"].append(product)
            if entity_count >= 4:
                indices["four_plus_entities"].append(product)

            if self.contains_any_entity(product, self.config.core_entities):
                indices["has_core_entities"].append(product)
            if self.contains_any_entity(product, self.config.rare_entity_names):
                indices["has_rare_entities"].append(product)
            if self.contains_any_entity(product, self.config.noisy_entity_names):
                indices["noisy_entities"].append(product)

            # Title length categorization
            title_length = self.get_title_length(product)
            if title_length < short_max:
                indices["by_title_short"].append(product)
            if med_lo <= title_length <= med_hi:
                indices["by_title_medium"].append(product)
            if title_length > long_min:
                indices["by_title_long"].append(product)

            # Quality categorization
            quality_band = self.infer_quality_band(product)
            if quality_band == "Poor":
                indices["quality_poor"].append(product)
            elif quality_band == "Fair":
                indices["quality_fair"].append(product)
            elif quality_band == "Good":
                indices["quality_good"].append(product)
            elif quality_band == "Excellent":
                indices["quality_excellent"].append(product)

            # Product variety
            product_type = self.get_product_type(product)
            if product_type in self.config.head_products:
                indices["head_products"].append(product)
            if product_type in self.config.tail_products:
                indices["tail_products"].append(product)

            # Image validity
            if self.is_image_url_valid(product):
                indices["images_valid"].append(product)

            # Outliers
            if self.is_outlier(product):
                indices["outliers"].append(product)

        return indices

    def dedupe_images(self, products: List[Product]) -> List[Product]:
        """Remove products with duplicate image URLs.

        Args:
            products: List of product dictionaries

        Returns:
            List of products with unique images
        """
        if not self.config.dedupe_by_content_hash:
            # Simple URL deduplication
            seen_urls = set()
            result = []
            for product in products:
                url = (product.get("image_url") or "").strip().lower()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result.append(product)
            return result

        # Content hash deduplication
        seen_hashes = set()
        result = []
        for product in products:
            image_hash = self.get_image_content_hash(product)
            if image_hash and image_hash not in seen_hashes:
                seen_hashes.add(image_hash)
                result.append(product)
        return result

    # Sampling utilities
    def sample_from_pool(
        self, pool: List[Product], k: int, rng: random.Random
    ) -> List[Product]:
        """Sample k items from pool without replacement.

        Args:
            pool: List of products to sample from
            k: Number of items to sample
            rng: Random number generator

        Returns:
            List of sampled products
        """
        if k <= 0 or not pool:
            return []
        if k >= len(pool):
            return pool.copy()
        return rng.sample(pool, k)

    def proportional_quota(
        self, count: int, ratios: Dict[str, float]
    ) -> Dict[str, int]:
        """Convert ratios to integer quotas that sum to count.

        Args:
            count: Total count to distribute
            ratios: Dictionary of ratios (should sum to ~1.0)

        Returns:
            Dictionary of integer quotas
        """
        # Calculate raw allocations
        raw_allocations = {k: count * v for k, v in ratios.items()}
        base_allocations = {k: int(math.floor(x)) for k, x in raw_allocations.items()}

        # Distribute remainder based on fractional parts
        remainder = count - sum(base_allocations.values())
        if remainder > 0:
            # Sort by fractional part (descending)
            fractional_parts = sorted(
                (
                    (k, raw_allocations[k] - base_allocations[k])
                    for k in raw_allocations
                ),
                key=lambda x: x[1],
                reverse=True,
            )

            for i in range(remainder):
                key = fractional_parts[i % len(fractional_parts)][0]
                base_allocations[key] += 1

        return base_allocations

    def get_product_id(self, product: Product) -> str:
        """Generate stable ID for product deduplication.

        Args:
            product: Product dictionary

        Returns:
            str: Unique product identifier
        """
        # Use random_key if available
        if "random_key" in product and product["random_key"]:
            return product["random_key"]

        # Generate hash from title and URL
        title = product.get("title") or ""
        url = product.get("image_url") or ""
        key_string = f"{title}|{url}"
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()

    # Main sampling algorithm
    def generate_toy_sample(
        self, products: List[Product], seed: int = 42
    ) -> List[Product]:
        """Generate balanced toy sample from product list.

        Args:
            products: List of all available products
            seed: Random seed for reproducible results

        Returns:
            List of products in the toy sample
        """
        rng = random.Random(seed)

        # Step 1: Basic filtering (valid images only)
        valid_products = [p for p in products if self.is_image_url_valid(p)]
        print(f"Filtered to {len(valid_products)} products with valid images")

        # Step 2: Deduplicate images
        unique_products = self.dedupe_images(valid_products)
        print(f"After deduplication: {len(unique_products)} unique products")

        # Step 3: Index products by categories
        indices = self.index_products(unique_products)

        # Initialize sample and tracking
        sample = []
        used_ids = set()
        target_size = self.config.target_sample_size

        def add_products(candidates: List[Product], quota: int) -> None:
            """Add products to sample while avoiding duplicates."""
            added = 0
            for product in rng.sample(candidates, min(quota, len(candidates))):
                product_id = self.get_product_id(product)
                if product_id in used_ids:
                    continue
                sample.append(product)
                used_ids.add(product_id)
                added += 1
                if added >= quota:
                    break

        # Step 4: Apply sampling quotas

        # Group composition
        group_quotas = self.proportional_quota(
            target_size, self.config.group_composition
        )
        add_products(indices["by_group_defined"], group_quotas["defined"])
        add_products(indices["by_group_rare"], group_quotas["rare"])
        add_products(indices["by_group_unknown"], group_quotas["unknown"])

        # Quality distribution
        quality_mix = {"good_excellent": 0.60, "fair": 0.30, "poor": 0.10}
        quality_quotas = self.proportional_quota(target_size, quality_mix)

        # Combine good and excellent for quota
        good_excellent_pool = indices["quality_good"] + indices["quality_excellent"]
        add_products(good_excellent_pool, quality_quotas["good_excellent"])
        add_products(indices["quality_fair"], quality_quotas["fair"])
        add_products(indices["quality_poor"], quality_quotas["poor"])

        # Entity count extremes
        min_zero_entities = int(math.ceil(target_size * 0.05))  # 5%
        min_four_plus_entities = int(math.ceil(target_size * 0.20))  # 20%
        add_products(indices["zero_entities"], min_zero_entities)
        add_products(indices["four_plus_entities"], min_four_plus_entities)

        # Title length distribution
        title_quotas = self.proportional_quota(
            target_size,
            {
                "short": self.config.title_length_config["short_ratio"],
                "medium": self.config.title_length_config["medium_ratio"],
                "long": self.config.title_length_config["long_ratio"],
            },
        )
        add_products(indices["by_title_short"], title_quotas["short"])
        add_products(indices["by_title_medium"], title_quotas["medium"])
        add_products(indices["by_title_long"], title_quotas["long"])

        # Outliers (5%)
        outlier_quota = int(math.ceil(target_size * self.config.outlier_ratio))
        add_products(indices["outliers"], outlier_quota)

        # Rare entities (minimum 10%)
        rare_entity_quota = int(math.ceil(target_size * 0.10))
        add_products(indices["has_rare_entities"], rare_entity_quota)

        # Noisy entities (minimum 2% or 5 items)
        noisy_quota = max(5, int(0.02 * target_size))
        add_products(indices["noisy_entities"], noisy_quota)

        # Product variety
        head_quota = max(10, int(0.10 * target_size))
        tail_quota = max(6, int(0.06 * target_size))
        add_products(indices["head_products"], head_quota)
        add_products(indices["tail_products"], tail_quota)

        # Step 5: Fill remaining slots with balanced selection
        while len(sample) < target_size:
            # Prioritize products with core entities, then others
            core_candidates = [
                p
                for p in indices["has_core_entities"]
                if self.get_product_id(p) not in used_ids
            ]
            other_candidates = [
                p for p in unique_products if self.get_product_id(p) not in used_ids
            ]

            # Interleave core and other products for diversity
            remaining_pool = []
            i = j = 0
            while i < len(core_candidates) or j < len(other_candidates):
                if i < len(core_candidates):
                    remaining_pool.append(core_candidates[i])
                    i += 1
                if j < len(other_candidates):
                    remaining_pool.append(other_candidates[j])
                    j += 1

            if not remaining_pool:
                break

            needed = target_size - len(sample)
            add_products(remaining_pool, needed)

        final_sample = sample[:target_size]
        print(f"Generated toy sample with {len(final_sample)} products")
        return final_sample

    def save_toy_sample(self, sample: List[Product], output_path: Path) -> None:
        """Save toy sample to JSON file.

        Args:
            sample: List of product dictionaries
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)

        print(f"Saved toy sample to {output_path}")

    def generate_and_save_sample(
        self, products: List[Product], output_path: Path = None
    ) -> List[Product]:
        """Complete pipeline to generate and save toy sample.

        Args:
            products: List of all available products
            output_path: Optional path to save sample (defaults to processed_data_dir)

        Returns:
            Generated toy sample
        """
        if output_path is None:
            output_path = self.config.processed_data_dir / "toy_sample.json"

        print("=" * 80)
        print("TOY SAMPLE GENERATION PIPELINE")
        print("=" * 80)

        sample = self.generate_toy_sample(products)
        self.save_toy_sample(sample, output_path)

        return sample
