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
from typing import Dict, Any, Optional, Tuple, List

from evaluation import EntityMetrics, EvaluationConfig


def find_latest_prediction_pair() -> Optional[Tuple[Path, Path]]:
    """Find the latest matching (predictions, ground_truth) pair.

    Returns:
        Tuple of (predictions_path, ground_truth_path) or None if not found
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    predictions_dir = project_root / "evaluation" / "predictions"

    if not predictions_dir.exists():
        return None

    # predictions_<MODEL>_<SAMPLE>.json
    pred_files: List[Path] = sorted(
        predictions_dir.glob("predictions_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    for pred in pred_files:
        # Derive ground truth filename by replacing the leading token
        stem = pred.name[len("predictions_") :]
        gt = predictions_dir / f"ground_truth_{stem}"
        if gt.exists():
            return pred, gt

    return None


def load_pair(predictions_path: Path, ground_truth_path: Path) -> Tuple[List[Any], List[Any]]:
    """Load predictions and ground truths lists.

    Returns:
        (predictions, ground_truths)
    """
    print(f"Loading predictions from: {predictions_path.name}")
    print(f"Loading ground truth from: {ground_truth_path.name}")

    with open(predictions_path, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truths = json.load(f)

    if not isinstance(predictions, list) or not isinstance(ground_truths, list):
        raise ValueError("Predictions and ground truths must be lists")
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths list sizes do not match")

    print(f"✓ Loaded {len(predictions)} prediction/ground-truth pairs")
    return predictions, ground_truths


def generate_evaluation_report(metrics_results: Dict[str, Any],
                               evaluation_metadata: Dict[str, Any],
                               output_path: Path) -> None:
    """Generate human-readable evaluation report.

    Args:
        metrics_results: Results from metrics calculation
        evaluation_metadata: Metadata from evaluation (model name, files, etc.)
        output_path: Path to save report
    """
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("MODEL EVALUATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Metadata
    report_lines.append("EVALUATION METADATA")
    report_lines.append("-" * 40)
    report_lines.append(f"Model Name: {evaluation_metadata.get('model_name', 'unknown')}")
    report_lines.append(f"Predictions File: {evaluation_metadata.get('predictions_file', 'unknown')}")
    report_lines.append(f"Ground Truth File: {evaluation_metadata.get('ground_truth_file', 'unknown')}")
    report_lines.append(f"Total Samples: {evaluation_metadata.get('total_samples', 0)}")
    report_lines.append(f"Evaluation Date: {evaluation_metadata.get('evaluation_timestamp', 'unknown')}")
    report_lines.append("")

    # Evaluation Metrics
    report_lines.append("EVALUATION METRICS")
    report_lines.append("-" * 40)

    # Create metrics instance for table formatting
    config = EvaluationConfig()
    metrics = EntityMetrics(config)
    report_lines.append(metrics.format_results_table(metrics_results))
    report_lines.append("")

    # Detailed Metrics (macro and micro averaged)
    if "macro_averaged" in metrics_results and "micro_averaged" in metrics_results:
        macro = metrics_results["macro_averaged"]
        micro = metrics_results["micro_averaged"]
        report_lines.append("DETAILED METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Macro Precision: {macro.get('precision', 0.0):.4f}")
        report_lines.append(f"Macro Recall: {macro.get('recall', 0.0):.4f}")
        report_lines.append(f"Macro F1: {macro.get('f1', 0.0):.4f}")
        report_lines.append(f"Micro Precision: {micro.get('precision', 0.0):.4f}")
        report_lines.append(f"Micro Recall: {micro.get('recall', 0.0):.4f}")
        report_lines.append(f"Micro F1: {micro.get('f1', 0.0):.4f}")
        report_lines.append("")

    # Sample Analysis
    if metrics_results.get("per_sample_results"):
        sample_results = metrics_results["per_sample_results"]

        # Best and worst samples by F1
        samples_by_f1 = sorted(enumerate(sample_results),
                               key=lambda x: x[1].get("f1", 0.0) if x[1].get("f1") is not None else 0.0,
                               reverse=True)

        report_lines.append("SAMPLE ANALYSIS")
        report_lines.append("-" * 40)
        if samples_by_f1:
            best_f1 = samples_by_f1[0][1].get("f1", 0.0) or 0.0
            worst_f1 = samples_by_f1[-1][1].get("f1", 0.0) or 0.0
            report_lines.append(
                f"Best Sample (F1): Sample #{samples_by_f1[0][0] + 1} - {best_f1:.4f}")
            report_lines.append(
                f"Worst Sample (F1): Sample #{samples_by_f1[-1][0] + 1} - {worst_f1:.4f}")

        # Distribution analysis
        exact_matches = sum(1 for r in sample_results if r.get("exact_match", 0.0) == 1.0)
        high_f1_matches = sum(1 for r in sample_results if (r.get("f1") or 0.0) >= 0.8)

        report_lines.append(
            f"Perfect Matches (Exact Match=1.0): {exact_matches}/{len(sample_results)} ({exact_matches / len(sample_results) * 100:.1f}%)")
        report_lines.append(
            f"High Quality (F1 >= 0.8): {high_f1_matches}/{len(sample_results)} ({high_f1_matches / len(sample_results) * 100:.1f}%)")

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

    # Optional CLI: allow passing explicit files
    predictions_file: Optional[Path] = None
    ground_truth_file: Optional[Path] = None
    if len(sys.argv) == 3:
        predictions_file = Path(sys.argv[1])
        ground_truth_file = Path(sys.argv[2])
        if not predictions_file.exists() or not ground_truth_file.exists():
            print("❌ Provided prediction/ground-truth file not found")
            return False
    else:
        # Auto-detect the latest matching pair
        pair = find_latest_prediction_pair()
        if not pair:
            print("❌ No matching predictions/ground-truth pair found!")
            print("Please run: python scripts/run_model_predictions.py")
            return False
        predictions_file, ground_truth_file = pair
        print(f"Using most recent pair: {predictions_file.name} + {ground_truth_file.name}")

    print("=" * 80)
    print("PREDICTION EVALUATION")
    print("=" * 80)

    try:
        # Load pair
        predictions, ground_truths = load_pair(predictions_file, ground_truth_file)

        # Setup metrics calculator
        # Derive model name from filename: predictions_<MODEL>_<SAMPLE>.json
        # Fallback to 'unknown_model' if cannot parse
        try:
            name_part = predictions_file.stem[len("predictions_"):]
            model_name = name_part.split("_")[0] if "_" in name_part else name_part
        except Exception:
            model_name = "unknown_model"

        config = EvaluationConfig(
            results_dir=predictions_file.parent.parent / "results",
            model_name=model_name
        )
        config.ensure_directories()

        metrics = EntityMetrics(config)

        # Calculate metrics
        print("\nCalculating evaluation metrics...")
        metrics_results = metrics.evaluate_batch(
            predictions,
            ground_truths
        )

        # Print summary to console
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)

        print("\nRESEARCH PAPER METRICS:")
        print(metrics.format_results_table(metrics_results))

        # Performance overview
        # Execution performance is not available from separate files; skip aggregate run stats

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = model_name

        # Save JSON results (detailed)
        results_filename = f"evaluation_{model_name}_{timestamp}.json"
        results_path = config.results_dir / results_filename

        evaluation_results = {
            "evaluation_metadata": {
                "predictions_file": str(predictions_file),
                "ground_truth_file": str(ground_truth_file),
                "model_name": model_name,
                "evaluation_timestamp": datetime.now().isoformat(),
                "total_samples": len(predictions)
            },
            "prediction_metadata": None,
            "model_performance": None,
            "metrics": metrics_results
        }

        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=2)

        print(f"✓ Detailed results saved to: {results_path}")

        # Save concise summary JSON for quick consumption
        summary = {
            "model": model_name,
            "total_samples": metrics_results.get("total_samples"),
            "valid_samples": metrics_results.get("valid_samples"),
            "precision": metrics_results.get("precision"),
            "recall": metrics_results.get("recall"),
            "f1": metrics_results.get("f1"),
            "exact_match": metrics_results.get("exact_match"),
            "macro_f1": metrics_results.get("macro_f1"),
            "rouge_1": metrics_results.get("rouge_1"),
        }
        summary_filename = f"evaluation_{model_name}_{timestamp}_summary.json"
        summary_path = config.results_dir / summary_filename
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✓ Summary saved to: {summary_path}")

        # Generate report
        report_filename = f"evaluation_{model_name}_{timestamp}_report.txt"
        report_path = config.results_dir / report_filename

        generate_evaluation_report(metrics_results, evaluation_results["evaluation_metadata"], report_path)

        print(f"\n🎉 Evaluation completed successfully!")
        print(f"📊 Report: {report_path}")
        print(f"📁 Results: {results_path}")
        print(f"📄 Summary: {summary_path}")

        # Print metrics JSON to stdout for immediate consumption (e.g., CI)
        print("\nMETRICS_JSON:")
        print(json.dumps(summary, ensure_ascii=False))

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
