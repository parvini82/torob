#!/usr/bin/env python3
"""Test evaluation package functionality.

This script tests the evaluation components with dummy data to ensure
everything works correctly before running on real samples.

Usage:
    python scripts/test_evaluation.py
"""

from pathlib import Path
from typing import List, Dict, Any
import tempfile
import json

from evaluation import EvaluationConfig, EntityMetrics, ModelRunner, SimpleEvaluator


def create_dummy_sample_data() -> List[Dict[str, Any]]:
    """Create dummy sample data for testing.

    Returns:
        List of dummy product dictionaries
    """
    return [
        {
            "title": "پیراهن آبی مردانه",
            "image_url": "https://example.com/image1.jpg",
            "entities": [
                {"name": "رنگ", "values": ["آبی"]},
                {"name": "جنس", "values": ["پنبه"]},
                {"name": "نوع کلی", "values": ["پیراهن"]},
            ],
        },
        {
            "title": "کفش ورزشی زنانه",
            "image_url": "https://example.com/image2.jpg",
            "entities": [
                {"name": "رنگ", "values": ["مشکی", "سفید"]},
                {"name": "نوع کلی", "values": ["کفش"]},
                {"name": "کاربری", "values": ["ورزشی"]},
            ],
        },
        {
            "title": "ساعت مچی طلایی",
            "image_url": "https://example.com/image3.jpg",
            "entities": [
                {"name": "رنگ", "values": ["طلایی"]},
                {"name": "جنس", "values": ["فلز"]},
                {"name": "نوع کلی", "values": ["ساعت مچی"]},
            ],
        },
    ]


def dummy_model_function(image_url: str) -> List[Dict[str, Any]]:
    """Dummy model function that returns predictable results for testing.

    Args:
        image_url: Image URL (used to determine response)

    Returns:
        Dummy entity predictions
    """
    print(f"    [DUMMY MODEL] Processing: {image_url}")

    # Return different predictions based on URL for testing
    if "image1" in image_url:
        return [
            {"name": "رنگ", "values": ["آبی"]},  # Perfect match
            {"name": "جنس", "values": ["پنبه"]},  # Perfect match
            {"name": "نوع کلی", "values": ["لباس"]},  # Different value
        ]
    elif "image2" in image_url:
        return [
            {"name": "رنگ", "values": ["مشکی"]},  # Partial match (missing سفید)
            {"name": "نوع کلی", "values": ["کفش"]},  # Perfect match
            {"name": "برند", "values": ["نایک"]},  # Extra entity
        ]
    elif "image3" in image_url:
        return [
            {"name": "رنگ", "values": ["نقره‌ای"]},  # Wrong value
            {"name": "نوع کلی", "values": ["ساعت مچی"]},  # Perfect match
            # Missing جنس entity
        ]
    else:
        return []


def test_entity_metrics():
    """Test EntityMetrics class functionality."""
    print("\n" + "=" * 50)
    print("TESTING ENTITY METRICS")
    print("=" * 50)

    config = EvaluationConfig()
    metrics = EntityMetrics(config)

    # Test data
    ground_truth = [
        {"name": "رنگ", "values": ["آبی"]},
        {"name": "جنس", "values": ["پنبه"]},
    ]

    # Test cases
    test_cases = [
        {
            "name": "Perfect Match",
            "predicted": [
                {"name": "رنگ", "values": ["آبی"]},
                {"name": "جنس", "values": ["پنبه"]},
            ],
        },
        {
            "name": "Partial Match",
            "predicted": [
                {"name": "رنگ", "values": ["آبی"]},
                {"name": "سایز", "values": ["لارج"]},  # Wrong entity
            ],
        },
        {
            "name": "No Match",
            "predicted": [
                {"name": "برند", "values": ["نایک"]},
                {"name": "قیمت", "values": ["گران"]},
            ],
        },
    ]

    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")

        # Test individual metrics
        exact_match = metrics.exact_match(test_case["predicted"], ground_truth)
        eighty_percent = metrics.eighty_percent_accuracy(
            test_case["predicted"], ground_truth
        )
        micro_f1 = metrics.micro_f1(test_case["predicted"], ground_truth)
        macro_f1 = metrics.macro_f1(test_case["predicted"], ground_truth)
        rouge_1 = metrics.rouge_1(test_case["predicted"], ground_truth)

        print(f"  Exact Match: {exact_match}")
        print(f"  80% Accuracy: {eighty_percent}")
        print(f"  Micro F1: {micro_f1['f1']:.4f}")
        print(f"  Macro F1: {macro_f1['f1']:.4f}")
        print(f"  ROUGE-1: {rouge_1:.4f}")

    print("\n✓ EntityMetrics tests completed")


def test_model_runner():
    """Test ModelRunner class functionality."""
    print("\n" + "=" * 50)
    print("TESTING MODEL RUNNER")
    print("=" * 50)

    # Create temporary sample file
    sample_data = create_dummy_sample_data()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
        sample_path = Path(f.name)

    try:
        # Test ModelRunner
        config = EvaluationConfig()
        runner = ModelRunner(config)

        print(f"Loading sample from: {sample_path}")
        products = runner.load_sample(sample_path)
        print(f"✓ Loaded {len(products)} products")

        print("Extracting image URLs...")
        image_urls = runner.extract_images(products)
        print(f"✓ Extracted {len([url for url in image_urls if url])} valid URLs")

        print("Testing model execution...")
        results = runner.run_model_on_sample(
            sample_path=sample_path, model_function=dummy_model_function
        )

        print(f"✓ Model execution completed")
        print(
            f"  Successful predictions: {results['performance']['successful_predictions']}"
        )
        print(f"  Failed predictions: {results['performance']['failed_predictions']}")

    finally:
        # Cleanup
        sample_path.unlink()

    print("\n✓ ModelRunner tests completed")


def test_simple_evaluator():
    """Test SimpleEvaluator class functionality."""
    print("\n" + "=" * 50)
    print("TESTING SIMPLE EVALUATOR")
    print("=" * 50)

    # Create temporary sample file
    sample_data = create_dummy_sample_data()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
        sample_path = Path(f.name)

    # Create temporary results directory
    with tempfile.TemporaryDirectory() as temp_dir:
        results_dir = Path(temp_dir)

        try:
            # Test SimpleEvaluator
            config = EvaluationConfig(results_dir=results_dir, model_name="test_model")

            evaluator = SimpleEvaluator(config)

            print("Running complete evaluation...")
            results = evaluator.run_evaluation(
                sample_path=sample_path,
                model_function=dummy_model_function,
                output_name="test_evaluation",
            )

            print(f"✓ Evaluation completed")

            # Check results structure
            required_keys = ["evaluation_metadata", "model_execution", "metrics"]
            for key in required_keys:
                if key in results:
                    print(f"  ✓ {key}: present")
                else:
                    print(f"  ✗ {key}: missing")

            # Display key metrics
            metrics = results["metrics"]
            print(f"\nMetrics Summary:")
            print(f"  80% Accuracy: {metrics['eighty_percent_accuracy']:.4f}")
            print(f"  Macro F1: {metrics['macro_f1']:.4f}")
            print(f"  Micro F1: {metrics['micro_f1']:.4f}")
            print(f"  ROUGE-1: {metrics['rouge_1']:.4f}")
            print(f"  Exact Match Rate: {metrics['exact_match_rate']:.4f}")

            # Check if files were created
            result_files = list(results_dir.glob("*.json"))
            report_files = list(results_dir.glob("*.txt"))

            print(f"\nGenerated Files:")
            print(f"  JSON results: {len(result_files)} files")
            print(f"  Text reports: {len(report_files)} files")

        finally:
            # Cleanup
            sample_path.unlink()

    print("\n✓ SimpleEvaluator tests completed")


def test_batch_metrics():
    """Test batch evaluation with multiple samples."""
    print("\n" + "=" * 50)
    print("TESTING BATCH METRICS")
    print("=" * 50)

    config = EvaluationConfig()
    metrics = EntityMetrics(config)

    # Create batch data
    predictions = [
        [{"name": "رنگ", "values": ["آبی"]}, {"name": "جنس", "values": ["پنبه"]}],
        [{"name": "رنگ", "values": ["قرمز"]}],
        [],  # Empty prediction
    ]

    ground_truths = [
        [{"name": "رنگ", "values": ["آبی"]}, {"name": "جنس", "values": ["پنبه"]}],
        [{"name": "رنگ", "values": ["قرمز"]}, {"name": "سایز", "values": ["متوسط"]}],
        [{"name": "برند", "values": ["سامسونگ"]}],
    ]

    print("Testing batch evaluation...")
    batch_results = metrics.evaluate_batch(predictions, ground_truths)

    print(f"✓ Batch evaluation completed")
    print(f"  Total samples: {batch_results['total_samples']}")
    print(f"  Average Macro F1: {batch_results['macro_f1']:.4f}")
    print(f"  Average Micro F1: {batch_results['micro_f1']:.4f}")

    # Test results table formatting
    print("\nFormatted Results Table:")
    print(metrics.format_results_table(batch_results))

    print("\n✓ Batch metrics tests completed")


def main():
    """Run all evaluation package tests."""

    print("🧪 EVALUATION PACKAGE TEST SUITE")
    print("=" * 80)

    try:
        # Run individual component tests
        test_entity_metrics()
        test_model_runner()
        test_batch_metrics()
        test_simple_evaluator()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("Evaluation package is working correctly.")
        print("=" * 80)

        print("\nYou can now run:")
        print("  python scripts/run_evaluation.py")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
