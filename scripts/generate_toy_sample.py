#!/usr/bin/env python3
"""Generate toy sample from existing dataset.

Usage:
    python scripts/generate_toy_sample.py
"""

import json
from pathlib import Path
from data import ToySampleGenerator, SampleConfig

project_root = Path(__file__).resolve().parent.parent


def load_products():
    """Load products from processed data directory."""
    # Try to find existing downloaded data
    data_paths = [
        Path(project_root / "data/raw/extracted"),
        # Path("data/processed")
    ]

    for data_path in data_paths:
        json_files = list(data_path.rglob("*.json"))
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
                return products

    print("❌ No product data found. Please run download_data.py first.")
    return None


def main():
    """Generate standard toy sample."""

    # Load existing products
    products = load_products()
    if not products:
        return

    # Configuration for standard sample
    config = SampleConfig(
        target_sample_size=300,
        # processed_data_dir=Path(project_root / "data/processed")
    )

    # Generate sample
    generator = ToySampleGenerator(config)
    try:
        sample = generator.generate_and_save(
            products=products,
            output_path=Path(project_root / "data/processed/toy_sample_standard.json"),
            seed=42,
        )
        print(f"\n🎉 Success! Generated toy sample with {len(sample)} products")
        print(f"📁 Saved to:{project_root}/data/processed/toy_sample_standard.json")

    except Exception as e:
        print(f"\n❌ Error generating sample: {e}")


if __name__ == "__main__":
    main()
