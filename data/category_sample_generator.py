# File: data/category_sample_generator.py
# Purpose: Build a very simple per-category sample: 5–10 items per product category.
# Style: Keep it minimal, similar to existing generators but without extra knobs.

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import SampleConfig


class CategorySampleGenerator:
    """
    Simple per-category sampler:
    - Valid image filtering
    - Image deduplication
    - Group by 'product' (fallback to 'group' or 'unknown')
    - Sample 5–10 items per category (or all available if less)
    """

    def __init__(self, config: SampleConfig, min_per_cat: int = 5, max_per_cat: int = 5):
        self.config = config
        self.min_per_cat = min_per_cat
        self.max_per_cat = max_per_cat
        self.config.ensure_directories()

    # --- Utilities (minimal, similar to other generators) ---

    def _category_of(self, product: Dict[str, Any]) -> str:
        cat = (product.get("product") or product.get("group") or "unknown")
        return str(cat).strip()

    def _is_image_url_valid(self, product: Dict[str, Any]) -> bool:
        url = product.get("image_url") or ""
        if not url.startswith("http"):
            return False
        # simple extension check like others
        match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", url)
        if not match:
            return True
        ext = f".{match.group(1).lower()}"
        return ext in self.config.allowed_image_formats

    def _dedupe_by_image_url(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for p in products:
            url = (p.get("image_url") or "").strip().lower()
            if url and url not in seen:
                seen.add(url)
                out.append(p)
        return out

    # --- Core ---

    def _group_by_category(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for p in products:
            cat = self._category_of(p)
            if cat not in buckets:
                buckets[cat] = []
            buckets[cat].append(p)
        return buckets

    # Updated version with intelligent filtering

    def generate(self, products: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
        """
        Build a sample with intelligent category filtering and sampling
        """
        rng = random.Random(seed)

        # 1) valid images
        valid = [p for p in products if self._is_image_url_valid(p)]
        print(f"Products with valid images: {len(valid)}")

        # 2) dedupe by image url
        unique = self._dedupe_by_image_url(valid)
        print(f"Products after deduplication: {len(unique)}")

        # 3) group by category
        by_cat = self._group_by_category(unique)
        print(f"Initial categories found: {len(by_cat)}")

        # 4) Smart filtering - NEW!
        filtered_cats = self._filter_categories_intelligently(by_cat)

        # 5) sample per category
        sample: List[Dict[str, Any]] = []
        category_stats = {}

        for cat, items in filtered_cats.items():
            if not items:
                continue

            available_count = len(items)

            if available_count <= self.min_per_cat:
                chosen = items
                k = available_count
            else:
                k = min(self.max_per_cat, available_count)
                k = max(k, self.min_per_cat)
                chosen = rng.sample(items, k)

            sample.extend(chosen)
            category_stats[cat] = len(chosen)

        # Print stats
        print(f"\n📊 Final sample statistics:")
        print(f"   Categories used: {len(category_stats)}")
        print(f"   Total products: {len(sample)}")

        # Show top categories
        sorted_cats = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
        print(f"\n🔝 Top 10 categories:")
        for cat, count in sorted_cats[:10]:
            print(f"   • {cat}: {count} products")

        return sample

    def _filter_categories_intelligently(self, by_cat: Dict[str, List]) -> Dict[str, List]:
        """Multi-stage intelligent filtering"""

        # Stage 1: Remove tiny categories
        MIN_THRESHOLD = 100
        step1 = {cat: items for cat, items in by_cat.items()
                 if len(items) >= MIN_THRESHOLD}
        print(f"   After min threshold (≥{MIN_THRESHOLD}): {len(step1)} categories")

        # Stage 2: Coverage-based filtering (keep 85% of data)
        total_items = sum(len(items) for items in step1.values())
        sorted_cats = sorted(step1.items(), key=lambda x: len(x[1]), reverse=True)

        cumulative = 0
        coverage_cats = {}
        for cat, items in sorted_cats:
            cumulative += len(items)
            coverage_cats[cat] = items
            if cumulative >= total_items * 0.85:
                break

        print(f"   After coverage filter (85%): {len(coverage_cats)} categories")

        # Stage 3: Hard limit
        MAX_CATEGORIES = 500
        if len(coverage_cats) > MAX_CATEGORIES:
            final_cats = dict(sorted(coverage_cats.items(),
                                     key=lambda x: len(x[1]),
                                     reverse=True)[:MAX_CATEGORIES])
            print(f"   After hard limit (≤{MAX_CATEGORIES}): {len(final_cats)} categories")
            return final_cats

        return coverage_cats

    def save(self, sample: List[Dict[str, Any]], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved category sample to: {output_path}")

    def generate_and_save(self, products: List[Dict[str, Any]], output_path: Optional[Path] = None, seed: int = 42) -> \
    List[Dict[str, Any]]:
        if output_path is None:
            output_path = self.config.processed_data_dir / "toy_sample_per_category.json"
        sample = self.generate(products, seed)
        self.save(sample, output_path)
        return sample
