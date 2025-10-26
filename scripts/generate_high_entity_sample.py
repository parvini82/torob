#!/usr/bin/env python3
"""Generate toy sample with minimum entity count requirement.

This script generates a toy sample where each product has at least
a specified number of entities.

Usage:
    python scripts/generate_high_entity_sample.py
"""

import json
from pathlib import Path
from data import HighEntitySampleGenerator, SampleConfig


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
                    with open(json_file, 'r', encoding='utf-8') as f:
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
    """Generate high entity count toy sample."""

    # Load existing products
    products = load_products()
    if not products:
        return

    # Configuration
    MIN_ENTITIES = 10
    TARGET_SIZE = 300

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config = SampleConfig(
        target_sample_size=TARGET_SIZE,
        processed_data_dir=project_root / "data" / "processed"
    )

    # Generate sample
    generator = HighEntitySampleGenerator(config, min_entities=MIN_ENTITIES)

    try:
        output_filename = f"toy_sample_min_{MIN_ENTITIES}_entities.json"
        sample = generator.generate_and_save(
            products=products,
            output_path=config.processed_data_dir / output_filename,
            seed=42
        )

        if sample:
            print(f"\n🎉 Success! Generated high-entity sample with {len(sample)} products")
            print(f"📁 Saved to: data/processed/{output_filename}")

            # Show some examples
            print(f"\n📋 Sample preview (first 3 products):")
            for i, product in enumerate(sample[:3]):
                entity_count = generator._count_entities(product)
                title = (product.get('title', 'No title'))[:50] + "..."
                print(f"   {i + 1}. [{entity_count:2d} entities] {title}")

        else:
            print(f"\n❌ No sample generated - not enough products with ≥{MIN_ENTITIES} entities")

    except Exception as e:
        print(f"\n❌ Error generating sample: {e}")


if __name__ == "__main__":
    main()
