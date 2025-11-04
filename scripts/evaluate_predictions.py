#!/usr/bin/env python3
"""Evaluate model predictions and generate metrics.

This script loads prediction results and ground truth data,
calculates comprehensive metrics, and generates evaluation reports.

Usage:
    python scripts/evaluate_predictions.py [prediction_file]
    python scripts/evaluate_predictions.py evaluation/predictions/predictions_model_sample.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from pathlib import Path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from evaluation import EntityMetrics, EvaluationConfig


def find_prediction_files():
    """Find available prediction result files.

    Returns:
        List of paths to prediction files
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    predictions_dir = project_root / "evaluation" / "predictions"

    if not predictions_dir.exists():
        return []

    # Find JSON files with predictions
    prediction_files = list(predictions_dir.glob("predictions_*.json"))
    return sorted(prediction_files, key=lambda x: x.stat().st_mtime, reverse=True)


def load_prediction_data(prediction_path: Path) -> Dict[str, Any]:
    """Load prediction data from file.

    Args:
        prediction_path: Path to prediction JSON file

    Returns:
        Prediction data dictionary
    """
    print(f"Loading predictions from: {prediction_path.name}")

    with open(prediction_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Verify required fields
    required_fields = ["predictions", "ground_truths", "metadata"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    print(f"✓ Loaded {len(data['predictions'])} predictions")
    return data


def generate_evaluation_report(metrics_results: Dict[str, Any],
                               prediction_data: Dict[str, Any],
                               output_path: Path) -> None:
    """Generate human-readable evaluation report.

    Args:
        metrics_results: Results from metrics calculation
        prediction_data: Original prediction data
        output_path: Path to save report
    """
    metadata = prediction_data["metadata"]
    performance = prediction_data["performance"]

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("MODEL EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Metadata
    report_lines.append("PREDICTION METADATA")
    report_lines.append("-" * 40)
    report_lines.append(f"Model Name: {metadata['model_name']}")
    report_lines.append(f"Sample Path: {metadata['sample_path']}")
    report_lines.append(f"Total Samples: {metadata['sample_size']}")
    report_lines.append(f"Prediction Time: {metadata['execution_time']:.2f} seconds")
    report_lines.append(f"Prediction Date: {metadata['timestamp']}")
    report_lines.append("")

    # Model Performance
    report_lines.append("MODEL EXECUTION PERFORMANCE")
    report_lines.append("-" * 40)
    report_lines.append(f"Successful Predictions: {performance['successful_predictions']}")
    report_lines.append(f"Failed Predictions: {performance['failed_predictions']}")
    report_lines.append(
        f"Success Rate: {performance['successful_predictions'] / performance['total_products'] * 100:.1f}%")
    report_lines.append(f"Average Time per Product: {performance['avg_time_per_product']:.3f}s")
    report_lines.append("")

    # Evaluation Metrics
    report_lines.append("EVALUATION METRICS")
    report_lines.append("-" * 40)

    # Create metrics instance for table formatting
    config = EvaluationConfig()
    metrics = EntityMetrics(config)
    report_lines.append(metrics.format_results_table(metrics_results))
    report_lines.append("")

    # Detailed Metrics
    if "detailed_metrics" in metrics_results:
        detailed = metrics_results["detailed_metrics"]
        report_lines.append("DETAILED METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Macro Precision: {detailed['macro_precision']:.4f}")
        report_lines.append(f"Macro Recall: {detailed['macro_recall']:.4f}")
        report_lines.append(f"Micro Precision: {detailed['micro_precision']:.4f}")
        report_lines.append(f"Micro Recall: {detailed['micro_recall']:.4f}")
        report_lines.append("")

    # Sample Analysis
    if metrics_results.get("per_sample_results"):
        sample_results = metrics_results["per_sample_results"]

        # Best and worst samples
        samples_by_f1 = sorted(enumerate(sample_results),
                               key=lambda x: x[1]["micro_f1"]["f1"], reverse=True)

        report_lines.append("SAMPLE ANALYSIS")
        report_lines.append("-" * 40)
        if samples_by_f1:
            report_lines.append(
                f"Best Sample (Micro-F1): Sample #{samples_by_f1[0][0] + 1} - {samples_by_f1[0][1]['micro_f1']['f1']:.4f}")
            report_lines.append(
                f"Worst Sample (Micro-F1): Sample #{samples_by_f1[-1][0] + 1} - {samples_by_f1[-1][1]['micro_f1']['f1']:.4f}")

        # Distribution analysis
        exact_matches = sum(1 for r in sample_results if r["exact_match"] == 1.0)
        eighty_percent_matches = sum(1 for r in sample_results if r["eighty_percent_accuracy"] == 1.0)

        report_lines.append(
            f"Perfect Matches: {exact_matches}/{len(sample_results)} ({exact_matches / len(sample_results) * 100:.1f}%)")
        report_lines.append(
            f"80%+ Accuracy: {eighty_percent_matches}/{len(sample_results)} ({eighty_percent_matches / len(sample_results) * 100:.1f}%)")

    # Add evaluation timestamp
    report_lines.append("")
    report_lines.append("EVALUATION INFO")
    report_lines.append("-" * 40)
    report_lines.append(f"Evaluation Date: {datetime.now().isoformat()}")

    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"✓ Report saved to: {output_path}")


def main():
    """Evaluate model predictions and generate metrics."""

    # Check for command line argument
    if len(sys.argv) > 1:
        prediction_file = Path(sys.argv[1])
        if not prediction_file.exists():
            print(f"❌ Prediction file not found: {prediction_file}")
            return False
    else:
        # Find most recent prediction file
        prediction_files = find_prediction_files()
        if not prediction_files:
            print("❌ No prediction files found!")
            print("Please run model predictions first:")
            print("  python scripts/run_model_predictions.py")
            return False

        prediction_file = prediction_files[0]
        print(f"Using most recent prediction file: {prediction_file.name}")

    print("=" * 80)
    print("PREDICTION EVALUATION")
    print("=" * 80)

    try:
        # Load prediction data
        prediction_data = load_prediction_data(prediction_file)

        # Setup metrics calculator
        config = EvaluationConfig(
            results_dir=prediction_file.parent.parent / "results",
            model_name=prediction_data["metadata"]["model_name"]
        )
        config.ensure_directories()

        metrics = EntityMetrics(config)

        # Calculate metrics
        print("\nCalculating evaluation metrics...")
        metrics_results = metrics.evaluate_batch(
            prediction_data["predictions"],
            prediction_data["ground_truths"]
        )

        # Print summary to console
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)

        print("\nRESEARCH PAPER METRICS:")
        print(metrics.format_results_table(metrics_results))

        # Performance overview
        performance = prediction_data["performance"]
        total = performance["total_products"]
        success_rate = performance["successful_predictions"] / total * 100 if total > 0 else 0

        print(f"\nMODEL EXECUTION:")
        print(f"Success Rate: {success_rate:.1f}% ({performance['successful_predictions']}/{total})")
        print(f"Avg Time/Product: {performance['avg_time_per_product']:.3f}s")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = prediction_data["metadata"]["model_name"]

        # Save JSON results
        results_filename = f"evaluation_{model_name}_{timestamp}.json"
        results_path = config.results_dir / results_filename

        evaluation_results = {
            "evaluation_metadata": {
                "prediction_file": str(prediction_file),
                "model_name": model_name,
                "evaluation_timestamp": datetime.now().isoformat(),
                "total_samples": len(prediction_data["predictions"])
            },
            "prediction_metadata": prediction_data["metadata"],
            "model_performance": prediction_data["performance"],
            "metrics": metrics_results
        }

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=2)

        print(f"✓ Detailed results saved to: {results_path}")

        # Generate report
        report_filename = f"evaluation_{model_name}_{timestamp}_report.txt"
        report_path = config.results_dir / report_filename

        generate_evaluation_report(metrics_results, prediction_data, report_path)

        print(f"\n🎉 Evaluation completed successfully!")
        print(f"📊 Report: {report_path}")
        print(f"📁 Results: {results_path}")

        return True

    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
