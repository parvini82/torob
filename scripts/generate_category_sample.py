#!/usr/bin/env python3
"""Generate category-based sample from existing dataset.

This script generates a sample with 5-10 products from each category,
ensuring valid images and no duplicates.

Usage:
    python scripts/generate_category_sample.py
"""

import json
from pathlib import Path
from data import CategorySampleGenerator, SampleConfig


def load_products():
    """Load products from processed data directory."""
    # Try to find existing downloaded data
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    data_paths = [
        project_root / "data" / "raw" / "extracted",
        # project_root / "data" / "processed"
    ]

    for data_path in data_paths:
        if not data_path.exists():
            continue

        json_files = list(data_path.rglob("*.json"))

        # Skip toy sample files to avoid loading previous outputs
        json_files = [f for f in json_files if "toy_sample" not in f.name.lower()]

        if json_files:
            print(f"Loading data from: {data_path}")
            products = []
            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            products.extend(data)
                        else:
                            products.append(data)
                    print(f"  ✓ Loaded {len(data)} items from {json_file.name}")
                except Exception as e:
                    print(f"  ✗ Error loading {json_file}: {e}")

            if products:
                print(f"Total products available: {len(products)}")
                return products

    print("❌ No product data found. Please run download_data.py first.")
    return None


def main():
    """Generate category-based sample."""

    # Load existing products
    products = load_products()
    if not products:
        return

    # Configuration
    MIN_PER_CATEGORY = 5
    MAX_PER_CATEGORY = 10

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config = SampleConfig(
        processed_data_dir=project_root / "data" / "processed",
    )

    # Generate sample
    generator = CategorySampleGenerator(
        config,
        min_per_cat=MIN_PER_CATEGORY,
        max_per_cat=MAX_PER_CATEGORY
    )

    try:
        output_filename = f"toy_sample_per_category_{MIN_PER_CATEGORY}_{MAX_PER_CATEGORY}.json"
        sample = generator.generate_and_save(
            products=products,
            output_path=config.processed_data_dir / output_filename,
            seed=42,
        )

        if sample:
            print(
                f"\n🎉 Success! Generated category sample with {len(sample)} products"
            )
            print(f"📁 Saved to: data/processed/{output_filename}")

            # Show category breakdown
            print(f"\n📋 Category breakdown:")

            # Group by category for stats
            category_stats = {}
            for product in sample:
                cat = generator._category_of(product)
                if cat not in category_stats:
                    category_stats[cat] = 0
                category_stats[cat] += 1

            # Sort by count for better readability
            sorted_cats = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)

            for cat, count in sorted_cats:
                print(f"   • {cat}: {count} products")

            print(f"\n📊 Total categories: {len(category_stats)}")

        else:
            print("\n❌ No sample generated - no valid products found")

    except Exception as e:
        print(f"\n❌ Error generating sample: {e}")


if __name__ == "__main__":
    main()
