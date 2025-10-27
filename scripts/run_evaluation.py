#!/usr/bin/env python3
"""Run model evaluation on toy sample.

This script provides a complete evaluation pipeline:
1. Load toy sample
2. Run model on product images
3. Calculate comprehensive metrics
4. Generate reports

Usage:
    python scripts/run_evaluation.py
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from evaluation import SimpleEvaluator, EvaluationConfig


import os

from dotenv import load_dotenv

# Load .env file
load_dotenv()

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")
TRANSLATE_MODEL: str = os.getenv("TRANSLATE_MODEL", "tngtech/deepseek-r1t2-chimera:free")


from src.service.langgraph.langgraph_service import run_langgraph_on_url

def example_model_function(image_url: str) -> List[Dict[str, Any]]:
    """Example model function - replace with your actual model.

    Args:
        image_url: URL of product image

    Returns:
        List of entity dictionaries with 'name' and 'values' keys
    """
    # TODO: Replace this with your actual model implementation
    # This is just a placeholder that returns empty results

    # Example of what your model should return:
    # return [
    #     {"name": "رنگ", "values": ["آبی", "تیره"]},
    #     {"name": "جنس", "values": ["پنبه"]},
    #     {"name": "سایز", "values": ["لارج"]}
    # ]
    output_model = run_langgraph_on_url(image_url)

    return output_model.get('persian').get('entities')


def find_toy_sample():
    """Find available toy sample files.

    Returns:
        Path to toy sample file or None if not found
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Look for toy samples in processed data directory
    processed_dir = project_root / "data" / "processed"

    if not processed_dir.exists():
        return None

    # Priority order for toy samples
    sample_names = [
        "toy_sample_high_entity.json",
        "toy_sample_standard.json",
        "toy_sample_min_10_entities.json"
    ]

    for sample_name in sample_names:
        sample_path = processed_dir / sample_name
        if sample_path.exists():
            return sample_path

    # Look for any toy sample file
    toy_samples = list(processed_dir.glob("toy_sample*.json"))
    if toy_samples:
        return toy_samples[0]

    return None


def main():
    """Run model evaluation pipeline."""

    print("=" * 80)
    print("MODEL EVALUATION PIPELINE")
    print("=" * 80)

    # Find toy sample
    sample_path = find_toy_sample()
    if not sample_path:
        print("❌ No toy sample found!")
        print("Please generate a toy sample first:")
        print("  python scripts/generate_toy_sample.py")
        print("  or")
        print("  python scripts/generate_high_entity_sample.py")
        return False

    print(f"Found toy sample: {sample_path.name}")

    # Load sample to check size
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        print(f"Sample size: {len(sample_data)} products")
    except Exception as e:
        print(f"❌ Error loading sample: {e}")
        return False

    # Setup evaluation configuration
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config = EvaluationConfig(
        results_dir=project_root / "evaluation" / "results",
        model_name=VISION_MODEL,  # Change this to your model name
        precision_digits=4
    )

    # Create evaluator
    evaluator = SimpleEvaluator(config)

    print(f"\nStarting evaluation with model: {config.model_name}")
    print("Note: Using placeholder model function. Replace with your actual model!")

    try:
        # Run evaluation
        results = evaluator.run_evaluation(
            sample_path=sample_path,
            model_function=example_model_function,
            output_name=f"evaluation_{sample_path.stem}"
        )

        print("\n🎉 Evaluation completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
