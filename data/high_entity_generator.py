"""High entity count toy sample generation.

This module provides specialized sampling for products with high entity counts,
operating independently from the standard toy sample generator.
"""

import hashlib
import json
import math
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from .config import SampleConfig


class HighEntitySampleGenerator:
    """Generator for toy samples with minimum entity count requirements.

    This class focuses specifically on creating samples where each product
    meets a minimum entity count threshold, using simplified sampling logic.
    """

    def __init__(self, config: SampleConfig, min_entities: int = 10):
        """Initialize high entity generator.

        Args:
            config: SampleConfig instance with basic parameters
            min_entities: Minimum number of entities required per product
        """
        self.config = config
        self.min_entities = min_entities
        self.config.ensure_directories()

    # Basic product utilities
    def _count_entities(self, product: Dict[str, Any]) -> int:
        """Count number of entity objects in product.

        Args:
            product: Product dictionary

        Returns:
            int: Number of entities
        """
        entities = product.get("entities") or []
        return len(entities)

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

    # Core filtering and analysis methods
    def filter_by_entity_count(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter products by minimum entity count requirement.

        Args:
            products: List of product dictionaries to filter

        Returns:
            List of products meeting entity count requirement
        """
        return [p for p in products if self._count_entities(p) >= self.min_entities]

    def filter_valid_images(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter products with valid image URLs.

        Args:
            products: List of product dictionaries

        Returns:
            List of products with valid images
        """
        return [p for p in products if self._is_image_url_valid(p)]

    def deduplicate_by_image(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    def analyze_entity_distribution(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze entity count distribution in product dataset.

        Args:
            products: List of product dictionaries

        Returns:
            Dictionary with distribution statistics
        """
        entity_counts = [self._count_entities(p) for p in products]

        if not entity_counts:
            return {"error": "No products to analyze"}

        # Calculate statistics
        stats = {
            "total_products": len(products),
            "min_entities": min(entity_counts),
            "max_entities": max(entity_counts),
            "avg_entities": sum(entity_counts) / len(entity_counts),
            "products_with_min_requirement": sum(1 for c in entity_counts if c >= self.min_entities)
        }

        # Calculate percentiles
        sorted_counts = sorted(entity_counts)
        n = len(sorted_counts)
        if n > 0:
            stats["percentiles"] = {
                "25th": sorted_counts[n // 4] if n > 4 else sorted_counts[0],
                "50th": sorted_counts[n // 2],
                "75th": sorted_counts[3 * n // 4] if n > 4 else sorted_counts[-1],
                "90th": sorted_counts[9 * n // 10] if n > 10 else sorted_counts[-1],
            }

        return stats

    def validate_sample(self, sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all products in sample meet entity requirements.

        Args:
            sample: List of sample products to validate

        Returns:
            Validation results with statistics and any violations
        """
        validation_result = {
            "valid_products": [],
            "invalid_products": [],
            "statistics": {}
        }

        for product in sample:
            entity_count = self._count_entities(product)
            product_info = {
                "title": (product.get("title") or "No title")[:50],
                "entity_count": entity_count,
                "product_id": self._get_product_id(product)
            }

            if entity_count >= self.min_entities:
                validation_result["valid_products"].append(product_info)
            else:
                validation_result["invalid_products"].append(product_info)

        # Calculate statistics
        valid_counts = [p["entity_count"] for p in validation_result["valid_products"]]
        if valid_counts:
            validation_result["statistics"] = {
                "total_valid": len(valid_counts),
                "total_invalid": len(validation_result["invalid_products"]),
                "min_entities": min(valid_counts),
                "max_entities": max(valid_counts),
                "avg_entities": sum(valid_counts) / len(valid_counts),
                "validation_rate": len(valid_counts) / len(sample) if sample else 0
            }

        return validation_result

    # Main generation method
    def generate(self, products: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
        """Generate toy sample with high entity count requirement.

        Args:
            products: List of all available products
            seed: Random seed for reproducible results

        Returns:
            List of products meeting entity count requirement
        """
        print("=" * 60)
        print(f"HIGH ENTITY SAMPLE GENERATION (Min: {self.min_entities} entities)")
        print("=" * 60)

        rng = random.Random(seed)

        # Step 1: Basic filtering
        print(f"Original dataset: {len(products)} products")

        # Filter by image validity
        valid_image_products = self.filter_valid_images(products)
        print(f"Valid images: {len(valid_image_products)} products")

        # Deduplicate images
        unique_products = self.deduplicate_by_image(valid_image_products)
        print(f"After deduplication: {len(unique_products)} products")

        # Filter by entity count
        high_entity_products = self.filter_by_entity_count(unique_products)
        print(f"High entity products (≥{self.min_entities}): {len(high_entity_products)} products")

        if not high_entity_products:
            print(f"❌ No products meet minimum entity requirement ({self.min_entities})")
            return []

        # Step 2: Analyze distribution
        distribution = self.analyze_entity_distribution(high_entity_products)
        if "error" not in distribution:
            print(f"Entity distribution in filtered set:")
            print(f"  Min: {distribution['min_entities']}, Max: {distribution['max_entities']}")
            print(f"  Average: {distribution['avg_entities']:.1f}")

        # Step 3: Determine sample size
        target_size = min(self.config.target_sample_size, len(high_entity_products))
        if target_size < self.config.target_sample_size:
            print(f"⚠️  Adjusting target size from {self.config.target_sample_size} to {target_size}")

        # Step 4: Random sampling
        sample = rng.sample(high_entity_products, target_size)

        # Step 5: Validate results
        validation = self.validate_sample(sample)

        # Step 6: Report statistics
        if validation["statistics"]:
            stats = validation["statistics"]
            print(f"✓ Final sample: {stats['total_valid']} products")
            print(f"📊 Entity statistics:")
            print(f"   Min: {stats['min_entities']} entities")
            print(f"   Max: {stats['max_entities']} entities")
            print(f"   Average: {stats['avg_entities']:.1f} entities")
            print(f"   Validation rate: {stats['validation_rate']:.1%}")

        return sample

    def save(self, sample: List[Dict[str, Any]], output_path: Path) -> None:
        """Save sample to JSON file.

        Args:
            sample: List of product dictionaries
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved sample to: {output_path}")

    def generate_and_save(self,
                         products: List[Dict[str, Any]],
                         output_path: Optional[Path] = None,
                         seed: int = 42) -> List[Dict[str, Any]]:
        """Complete pipeline for high entity sample generation and saving.

        Args:
            products: List of all available products
            output_path: Optional path to save sample
            seed: Random seed for reproducible results

        Returns:
            Generated high entity sample
        """
        if output_path is None:
            filename = f"toy_sample_min_{self.min_entities}_entities.json"
            output_path = self.config.processed_data_dir / filename

        sample = self.generate(products, seed)

        if sample:
            self.save(sample, output_path)
        else:
            print("❌ No sample to save")

        return sample
