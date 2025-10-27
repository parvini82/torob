"""Toy sample generation for evaluation purposes.

This module provides sophisticated sampling strategies to create balanced
toy samples from product datasets. Operates independently from data downloading.
"""

import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .config import SampleConfig


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

    def __init__(self, config: SampleConfig):
        """Initialize generator with configuration.

        Args:
            config: SampleConfig instance with sampling parameters
        """
        self.config = config
        self.config.ensure_directories()

    # Product analysis utilities
    def _get_title_length(self, product: Dict[str, Any]) -> int:
        """Get title length in characters safely.

        Args:
            product: Product dictionary

        Returns:
            int: Title length, 0 if no title
        """
        title = product.get("title") or ""
        return len(title)

    def _count_entities(self, product: Dict[str, Any]) -> int:
        """Count number of entity objects in product.

        Args:
            product: Product dictionary

        Returns:
            int: Number of entities
        """
        entities = product.get("entities") or []
        return len(entities)

    def _get_entity_names(self, product: Dict[str, Any]) -> Set[str]:
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

    def _get_group_name(self, product: Dict[str, Any]) -> str:
        """Get normalized group name with fallback.

        Args:
            product: Product dictionary

        Returns:
            str: Group name or 'نامشخص' if missing
        """
        group = (product.get("group") or "").strip()
        return group if group else "نامشخص"

    def _get_product_type(self, product: Dict[str, Any]) -> str:
        """Get normalized product type.

        Args:
            product: Product dictionary

        Returns:
            str: Normalized product type or empty string
        """
        return (product.get("product") or "").strip()

    def _infer_quality_band(self, product: Dict[str, Any]) -> str:
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

    def _is_image_url_valid(self, product: Dict[str, Any]) -> bool:
        """Check if product has valid image URL.

        Args:
            product: Product dictionary

        Returns:
            bool: True if image URL is valid
        """
        url = product.get("image_url") or ""
        if not url.startswith("http"):
            return False

        # Extract file extension
        match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", url)
        if not match:
            return True  # Assume valid if no extension found

        ext = f".{match.group(1).lower()}"
        return ext in self.config.allowed_image_formats

    def _get_image_content_hash(self, product: Dict[str, Any]) -> str:
        """Generate hash of image URL for deduplication.

        Args:
            product: Product dictionary

        Returns:
            str: MD5 hash of normalized URL
        """
        url = (product.get("image_url") or "").strip().lower()
        return hashlib.md5(url.encode("utf-8")).hexdigest() if url else ""

    def _is_outlier(self, product: Dict[str, Any]) -> bool:
        """Check if product meets outlier criteria.

        Args:
            product: Product dictionary

        Returns:
            bool: True if product is considered an outlier
        """
        rules = self.config.outlier_rules
        return (
            self._get_title_length(product) >= rules["min_title_length"]
            or self._count_entities(product) >= rules["min_entity_count"]
        )

    def _contains_any_entity(
        self, product: Dict[str, Any], entity_names: Set[str]
    ) -> bool:
        """Check if product contains any of the specified entities.

        Args:
            product: Product dictionary
            entity_names: Set of entity names to check for

        Returns:
            bool: True if product has any of the specified entities
        """
        product_entities = self._get_entity_names(product)
        return len(product_entities.intersection(entity_names)) > 0

    def _get_product_id(self, product: Dict[str, Any]) -> str:
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

    # Indexing and filtering
    def _index_products(
        self, products: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
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
            group = self._get_group_name(product)
            if group == "نامشخص":
                indices["by_group_unknown"].append(product)
            elif group in self.config.defined_groups:
                indices["by_group_defined"].append(product)
            else:
                indices["by_group_rare"].append(product)

            # Entity categorization
            entity_names = self._get_entity_names(product)
            entity_count = len(entity_names)

            if entity_count == 0:
                indices["zero_entities"].append(product)
            if entity_count >= 4:
                indices["four_plus_entities"].append(product)

            if self._contains_any_entity(product, self.config.core_entities):
                indices["has_core_entities"].append(product)
            if self._contains_any_entity(product, self.config.rare_entity_names):
                indices["has_rare_entities"].append(product)
            if self._contains_any_entity(product, self.config.noisy_entity_names):
                indices["noisy_entities"].append(product)

            # Title length categorization
            title_length = self._get_title_length(product)
            if title_length < short_max:
                indices["by_title_short"].append(product)
            if med_lo <= title_length <= med_hi:
                indices["by_title_medium"].append(product)
            if title_length > long_min:
                indices["by_title_long"].append(product)

            # Quality categorization
            quality_band = self._infer_quality_band(product)
            if quality_band == "Poor":
                indices["quality_poor"].append(product)
            elif quality_band == "Fair":
                indices["quality_fair"].append(product)
            elif quality_band == "Good":
                indices["quality_good"].append(product)
            elif quality_band == "Excellent":
                indices["quality_excellent"].append(product)

            # Product variety
            product_type = self._get_product_type(product)
            if product_type in self.config.head_products:
                indices["head_products"].append(product)
            if product_type in self.config.tail_products:
                indices["tail_products"].append(product)

            # Image validity
            if self._is_image_url_valid(product):
                indices["images_valid"].append(product)

            # Outliers
            if self._is_outlier(product):
                indices["outliers"].append(product)

        return indices

    def _dedupe_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            image_hash = self._get_image_content_hash(product)
            if image_hash and image_hash not in seen_hashes:
                seen_hashes.add(image_hash)
                result.append(product)
        return result

    def _proportional_quota(
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

    # Main generation methods
    def generate(
        self, products: List[Dict[str, Any]], seed: int = 42
    ) -> List[Dict[str, Any]]:
        """Generate balanced toy sample from product list.

        Args:
            products: List of all available products
            seed: Random seed for reproducible results

        Returns:
            List of products in the toy sample
        """
        print("=" * 60)
        print("TOY SAMPLE GENERATION")
        print("=" * 60)

        rng = random.Random(seed)

        # Step 1: Filter valid images
        valid_products = [p for p in products if self._is_image_url_valid(p)]
        print(f"Valid image products: {len(valid_products)}")

        # Step 2: Deduplicate
        unique_products = self._dedupe_images(valid_products)
        print(f"After deduplication: {len(unique_products)}")

        # Step 3: Index products
        indices = self._index_products(unique_products)

        # Step 4: Generate sample
        sample = []
        used_ids = set()
        target_size = self.config.target_sample_size

        def add_products_to_sample(
            candidates: List[Dict[str, Any]], quota: int
        ) -> None:
            """Add products to sample while avoiding duplicates."""
            added = 0
            available = [
                p for p in candidates if self._get_product_id(p) not in used_ids
            ]

            for product in rng.sample(available, min(quota, len(available))):
                product_id = self._get_product_id(product)
                if product_id not in used_ids:
                    sample.append(product)
                    used_ids.add(product_id)
                    added += 1
                    if added >= quota:
                        break

        # Apply sampling strategy
        group_quotas = self._proportional_quota(
            target_size, self.config.group_composition
        )
        add_products_to_sample(indices["by_group_defined"], group_quotas["defined"])
        add_products_to_sample(indices["by_group_rare"], group_quotas["rare"])
        add_products_to_sample(indices["by_group_unknown"], group_quotas["unknown"])

        # Quality distribution
        quality_mix = {"good_excellent": 0.60, "fair": 0.30, "poor": 0.10}
        quality_quotas = self._proportional_quota(target_size, quality_mix)

        good_excellent_pool = indices["quality_good"] + indices["quality_excellent"]
        add_products_to_sample(good_excellent_pool, quality_quotas["good_excellent"])
        add_products_to_sample(indices["quality_fair"], quality_quotas["fair"])
        add_products_to_sample(indices["quality_poor"], quality_quotas["poor"])

        # Other quotas
        add_products_to_sample(indices["zero_entities"], int(target_size * 0.05))
        add_products_to_sample(indices["four_plus_entities"], int(target_size * 0.20))
        add_products_to_sample(
            indices["outliers"], int(target_size * self.config.outlier_ratio)
        )
        add_products_to_sample(indices["has_rare_entities"], int(target_size * 0.10))
        add_products_to_sample(
            indices["noisy_entities"], max(5, int(target_size * 0.02))
        )

        # Fill remaining slots
        while len(sample) < target_size:
            remaining_candidates = [
                p for p in unique_products if self._get_product_id(p) not in used_ids
            ]
            if not remaining_candidates:
                break

            needed = target_size - len(sample)
            add_products_to_sample(remaining_candidates, needed)

        final_sample = sample[:target_size]
        print(f"✓ Generated sample with {len(final_sample)} products")
        return final_sample

    def save(self, sample: List[Dict[str, Any]], output_path: Path) -> None:
        """Save toy sample to JSON file.

        Args:
            sample: List of product dictionaries
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved toy sample to {output_path}")

    def generate_and_save(
        self, products: List[Dict[str, Any]], output_path: Path = None, seed: int = 42
    ) -> List[Dict[str, Any]]:
        """Complete pipeline to generate and save toy sample.

        Args:
            products: List of all available products
            output_path: Optional path to save sample
            seed: Random seed for reproducible results

        Returns:
            Generated toy sample
        """
        if output_path is None:
            output_path = self.config.processed_data_dir / "toy_sample.json"

        sample = self.generate(products, seed)
        self.save(sample, output_path)
        return sample
