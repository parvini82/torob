#!/usr/bin/env python3
"""Evaluate model predictions with comprehensive metrics.

This script loads prediction results and ground truth data,
calculates comprehensive metrics using multiple evaluation approaches,
and generates detailed evaluation reports.

Usage:
    python scripts/evaluate_predictions.py [prediction_file] [options]

Examples:
    # Use most recent prediction file with all metrics
    python scripts/evaluate_predictions.py

    # Specify prediction file with all metrics
    python scripts/evaluate_predictions.py evaluation/predictions/predictions_model_sample.json

    # Use only specific metrics
    python scripts/evaluate_predictions.py --metrics exact similarity

    # Generate comparison report
    python scripts/evaluate_predictions.py --report-mode comparison

    # Enable semantic similarity (requires sentence-transformers)
    python scripts/evaluate_predictions.py --enable-semantic
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from evaluation import EvaluationConfig
from evaluation.metrics import MetricsAggregator


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Comprehensive evaluation of model predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available metrics:
  exact      - Standard MAVE exact matching (P/R/F1, Exact Match)
  similarity - Jaccard, Dice, and semantic similarity 
  partial    - Partial matching with credit for incomplete predictions
  lenient    - Lenient matching with normalization and abbreviations

Report modes:
  mave           - Standard MAVE format (P/R/F1, Exact Match)
  comprehensive  - All enabled metrics with detailed breakdown
  comparison     - Key metrics suitable for model comparison
        """
    )

    parser.add_argument(
        'prediction_file',
        nargs='?',
        help='Path to prediction JSON file (uses most recent if not specified)'
    )

    parser.add_argument(
        '--metrics',
        nargs='+',
        choices=['exact', 'similarity', 'partial', 'lenient'],
        default=['exact', 'similarity', 'partial', 'lenient'],
        help='Metrics to calculate (default: all)'
    )

    parser.add_argument(
        '--report-mode',
        choices=['mave', 'comprehensive', 'comparison'],
        default='comprehensive',
        help='Report format mode (default: comprehensive)'
    )

    parser.add_argument(
        '--enable-semantic',
        action='store_true',
        help='Enable semantic similarity (requires sentence-transformers)'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for results (default: evaluation/results)'
    )

    parser.add_argument(
        '--precision-digits',
        type=int,
        default=4,
        help='Number of decimal places for metrics (default: 4)'
    )

    parser.add_argument(
        '--save-detailed',
        action='store_true',
        help='Save detailed per-sample results'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output'
    )

    return parser.parse_args()


def find_prediction_files():
    """Find available prediction result files.

    Returns:
        List of paths to prediction files, sorted by modification time (newest first)
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
    """Load and validate prediction data from file.

    Args:
        prediction_path: Path to prediction JSON file

    Returns:
        Prediction data dictionary

    Raises:
        ValueError: If required fields are missing
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


def check_semantic_similarity_availability(enable_semantic: bool) -> bool:
    """Check if semantic similarity can be enabled.

    Args:
        enable_semantic: Whether user requested semantic similarity

    Returns:
        Whether semantic similarity is available
    """
    if not enable_semantic:
        return False

    try:
        import sentence_transformers
        return True
    except ImportError:
        print("Warning: sentence-transformers not installed, semantic similarity disabled")
        print("Install with: pip install sentence-transformers")
        return False


def safe_get_numeric_value(result_dict: Dict[str, Any], key: str, default: float = 0.0) -> float:
    """Safely get numeric value from result dictionary, handling None values.

    Args:
        result_dict: Dictionary containing results
        key: Key to look up
        default: Default value if key is missing or None

    Returns:
        Numeric value or default
    """
    value = result_dict.get(key, default)
    return value if value is not None else default


def analyze_sample_results(sample_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze per-sample results with safe handling of None values.

    Args:
        sample_results: List of per-sample result dictionaries

    Returns:
        Analysis summary
    """
    if not sample_results:
        return {
            "best_sample": None,
            "worst_sample": None,
            "exact_matches": 0,
            "high_f1_samples": 0,
            "valid_f1_samples": 0
        }

    # Find samples with valid F1 scores
    samples_with_f1 = []
    for i, result in enumerate(sample_results):
        f1_score = safe_get_numeric_value(result, "f1", None)
        if f1_score is not None:
            samples_with_f1.append((i, result, f1_score))

    analysis = {
        "valid_f1_samples": len(samples_with_f1),
        "total_samples": len(sample_results)
    }

    # Best and worst samples
    if samples_with_f1:
        samples_by_f1 = sorted(samples_with_f1, key=lambda x: x[2], reverse=True)

        best_idx, best_result, best_f1 = samples_by_f1[0]
        worst_idx, worst_result, worst_f1 = samples_by_f1[-1]

        analysis["best_sample"] = {
            "index": best_idx,
            "f1": best_f1
        }
        analysis["worst_sample"] = {
            "index": worst_idx,
            "f1": worst_f1
        }
    else:
        analysis["best_sample"] = None
        analysis["worst_sample"] = None

    # Count exact matches (handle None values)
    exact_matches = 0
    for result in sample_results:
        exact_match = safe_get_numeric_value(result, "exact_match", 0.0)
        if exact_match == 1.0:
            exact_matches += 1

    analysis["exact_matches"] = exact_matches

    # Count high F1 samples (F1 > 0.8, excluding None)
    high_f1_samples = 0
    for result in sample_results:
        f1_score = safe_get_numeric_value(result, "f1", 0.0)
        if f1_score > 0.8:
            high_f1_samples += 1

    analysis["high_f1_samples"] = high_f1_samples

    return analysis


def generate_evaluation_report(metrics_results: Dict[str, Any],
                               prediction_data: Dict[str, Any],
                               args: argparse.Namespace,
                               output_path: Path) -> None:
    """Generate comprehensive evaluation report.

    Args:
        metrics_results: Results from metrics calculation
        prediction_data: Original prediction data
        args: Command line arguments
        output_path: Path to save report
    """
    metadata = prediction_data["metadata"]
    performance = prediction_data["performance"]

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("COMPREHENSIVE MODEL EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Evaluation info
    report_lines.append("EVALUATION CONFIGURATION")
    report_lines.append("-" * 40)
    report_lines.append(f"Evaluation Date: {datetime.now().isoformat()}")
    report_lines.append(f"Enabled Metrics: {', '.join(args.metrics)}")
    report_lines.append(f"Report Mode: {args.report_mode}")
    report_lines.append(f"Semantic Similarity: {'Enabled' if 'similarity' in args.metrics else 'Disabled'}")
    report_lines.append("")

    # Prediction metadata
    report_lines.append("PREDICTION METADATA")
    report_lines.append("-" * 40)
    report_lines.append(f"Model Name: {metadata['model_name']}")
    report_lines.append(f"Sample Path: {metadata['sample_path']}")
    report_lines.append(f"Total Samples: {metadata['sample_size']}")
    report_lines.append(f"Prediction Time: {metadata['execution_time']:.2f} seconds")
    report_lines.append(f"Prediction Date: {metadata['timestamp']}")
    report_lines.append("")

    # Model performance
    report_lines.append("MODEL EXECUTION PERFORMANCE")
    report_lines.append("-" * 40)
    report_lines.append(f"Successful Predictions: {performance['successful_predictions']}")
    report_lines.append(f"Failed Predictions: {performance['failed_predictions']}")
    report_lines.append(
        f"Success Rate: {performance['successful_predictions'] / performance['total_products'] * 100:.1f}%")
    report_lines.append(f"Average Time per Product: {performance['avg_time_per_product']:.3f}s")
    report_lines.append("")

    # Evaluation results
    report_lines.append("EVALUATION RESULTS")
    report_lines.append("-" * 40)

    # Create aggregator for table formatting
    config = EvaluationConfig(precision_digits=args.precision_digits)
    aggregator = MetricsAggregator(config, enabled_metrics=args.metrics)

    report_lines.append(aggregator.format_results_table(metrics_results, mode=args.report_mode))
    report_lines.append("")

    # Sample analysis if detailed results available
    if metrics_results.get("per_sample_results"):
        sample_results = metrics_results["per_sample_results"]
        analysis = analyze_sample_results(sample_results)

        if analysis["total_samples"] > 0:
            report_lines.append("SAMPLE ANALYSIS")
            report_lines.append("-" * 40)

            # Best and worst samples
            if analysis["best_sample"] and analysis["worst_sample"]:
                best = analysis["best_sample"]
                worst = analysis["worst_sample"]

                report_lines.append(f"Best Sample (F1): Sample #{best['index'] + 1} - F1: {best['f1']:.4f}")
                report_lines.append(f"Worst Sample (F1): Sample #{worst['index'] + 1} - F1: {worst['f1']:.4f}")

            # Distribution analysis
            total_samples = analysis["total_samples"]
            report_lines.append(
                f"Perfect Matches: {analysis['exact_matches']}/{total_samples} ({analysis['exact_matches'] / total_samples * 100:.1f}%)")
            report_lines.append(
                f"High F1 (>0.8): {analysis['high_f1_samples']}/{total_samples} ({analysis['high_f1_samples'] / total_samples * 100:.1f}%)")
            report_lines.append(
                f"Valid F1 Scores: {analysis['valid_f1_samples']}/{total_samples} ({analysis['valid_f1_samples'] / total_samples * 100:.1f}%)")
            report_lines.append("")

    # Metric interpretations
    report_lines.append("METRIC INTERPRETATIONS")
    report_lines.append("-" * 40)

    if 'exact' in args.metrics:
        report_lines.append("Exact Matching:")
        report_lines.append("  - Standard MAVE evaluation with exact string matching")
        report_lines.append("  - Precision/Recall/F1 based on complete attribute-value pairs")
        report_lines.append("")

    if 'similarity' in args.metrics:
        report_lines.append("Similarity Metrics:")
        report_lines.append("  - Jaccard: Set intersection over union")
        report_lines.append("  - Dice: 2 * intersection over sum of sets")
        report_lines.append("  - Semantic: Deep similarity using multilingual embeddings")
        report_lines.append("")

    if 'partial' in args.metrics:
        report_lines.append("Partial Evaluation:")
        report_lines.append("  - Credit for partially correct attribute predictions")
        report_lines.append("  - Useful for understanding per-attribute performance")
        report_lines.append("")

    if 'lenient' in args.metrics:
        report_lines.append("Lenient Evaluation:")
        report_lines.append("  - Flexible matching with normalization")
        report_lines.append("  - Handles abbreviations and common variations")
        report_lines.append("  - Better for real-world deployment scenarios")
        report_lines.append("")

    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    if not args.quiet:
        print(f"✓ Comprehensive report saved to: {output_path}")


def print_console_summary(results: Dict[str, Any], args: argparse.Namespace):
    """Print evaluation summary to console.

    Args:
        results: Evaluation results
        args: Command line arguments
    """
    if args.quiet:
        return

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    # Create aggregator for formatting
    config = EvaluationConfig(precision_digits=args.precision_digits)
    aggregator = MetricsAggregator(config, enabled_metrics=args.metrics)

    print(f"\nResults using metrics: {', '.join(args.metrics)}")
    print(aggregator.format_results_table(results, mode=args.report_mode))

    # Key insights
    print(f"\nSample Info:")
    print(f"Total samples: {results['total_samples']}")
    print(f"Valid samples: {results['valid_samples']}")
    if results.get('skipped_samples', 0) > 0:
        print(f"Skipped samples: {results['skipped_samples']} (empty ground truth)")


def main():
    """Main evaluation function."""
    args = parse_arguments()

    if not args.quiet:
        print("=" * 80)
        print("COMPREHENSIVE PREDICTION EVALUATION")
        print("=" * 80)

    # Find prediction file
    if args.prediction_file:
        prediction_file = Path(args.prediction_file)
        if not prediction_file.exists():
            print(f"❌ Prediction file not found: {prediction_file}")
            return False
    else:
        prediction_files = find_prediction_files()
        if not prediction_files:
            print("❌ No prediction files found!")
            print("Please run model predictions first:")
            print("  python scripts/run_model_predictions.py")
            return False

        prediction_file = prediction_files[0]
        if not args.quiet:
            print(f"Using most recent prediction file: {prediction_file.name}")

    try:
        # Load prediction data
        prediction_data = load_prediction_data(prediction_file)

        # Check semantic similarity availability
        if 'similarity' in args.metrics:
            semantic_available = check_semantic_similarity_availability(args.enable_semantic)
            if not semantic_available and not args.quiet:
                print("Note: Semantic similarity will use fallback exact matching")

        # Setup configuration
        if args.output_dir:
            output_dir = args.output_dir
        else:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            output_dir = project_root / "evaluation" / "results"

        config = EvaluationConfig(
            results_dir=output_dir,
            model_name=prediction_data["metadata"]["model_name"],
            precision_digits=args.precision_digits
        )
        config.ensure_directories()

        # Create metrics aggregator
        aggregator = MetricsAggregator(config, enabled_metrics=args.metrics)

        # Calculate metrics
        if not args.quiet:
            print(f"\nCalculating evaluation metrics: {', '.join(args.metrics)}...")

        # Enable detailed results if requested
        original_precision = config.precision_digits
        if args.save_detailed:
            config.precision_digits = args.precision_digits  # Ensure detailed results

        metrics_results = aggregator.evaluate_batch(
            prediction_data["predictions"],
            prediction_data["ground_truths"]
        )

        # Restore original setting
        config.precision_digits = original_precision

        # Print console summary
        print_console_summary(metrics_results, args)

        # Generate output files
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
                "enabled_metrics": args.metrics,
                "report_mode": args.report_mode,
                "semantic_enabled": args.enable_semantic,
                "total_samples": len(prediction_data["predictions"])
            },
            "prediction_metadata": prediction_data["metadata"],
            "model_performance": prediction_data["performance"],
            "metrics": metrics_results,
            "metric_summary": aggregator.get_metric_summary(metrics_results)
        }

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=2)

        # Generate comprehensive report
        report_filename = f"evaluation_{model_name}_{timestamp}_report.txt"
        report_path = config.results_dir / report_filename

        generate_evaluation_report(metrics_results, prediction_data, args, report_path)

        if not args.quiet:
            print(f"\n🎉 Evaluation completed successfully!")
            print(f"📊 Report: {report_path}")
            print(f"📁 Results: {results_path}")

            # Show key metrics for quick reference
            summary = aggregator.get_metric_summary(metrics_results)
            if summary:
                print(f"\nKey Metrics Summary:")
                for metric, value in summary.items():
                    if value is not None:
                        print(f"  {metric}: {value:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
