#!/usr/bin/env python3
"""Compare multiple evaluation results.

This script loads multiple evaluation result files and compares their metrics,
generating comparison tables and rankings with support for the new weighted metrics.

Usage:
    python scripts/compare_evaluations.py
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from evaluation import EvaluationConfig, MetricsAggregator


def find_evaluation_results() -> List[Path]:
    """Find available evaluation result files.

    Returns:
        List of paths to evaluation result files
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    results_dir = project_root / "evaluation" / "results"

    if not results_dir.exists():
        return []

    # Find JSON files that contain evaluation results (not reports or weights)
    result_files = []
    for json_file in results_dir.glob("*.json"):
        # Skip report files and entity weights
        if "_report" not in json_file.name and json_file.name != "entity_weights.json":
            result_files.append(json_file)

    return sorted(result_files)


def load_evaluation_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a single evaluation result file.

    Args:
        file_path: Path to evaluation result JSON file

    Returns:
        Dictionary containing evaluation data or None if loading failed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            evaluation = json.load(f)

        # Validate required structure
        if "metrics" not in evaluation:
            print(f"⚠️  Invalid format in {file_path.name}: missing 'metrics' section")
            return None

        return {
            "file": file_path.name,
            "model": evaluation.get("evaluation_metadata", {}).get("model_name", "Unknown"),
            "timestamp": evaluation.get("evaluation_metadata", {}).get("evaluation_timestamp", "Unknown"),
            "total_samples": evaluation.get("evaluation_metadata", {}).get("total_samples", 0),
            "metrics": evaluation["metrics"],
            "full_data": evaluation
        }

    except Exception as e:
        print(f"✗ Failed to load {file_path.name}: {e}")
        return None


def create_comparison_table(evaluations: List[Dict[str, Any]]) -> str:
    """Create formatted comparison table.

    Args:
        evaluations: List of evaluation data dictionaries

    Returns:
        Formatted table string
    """
    if not evaluations:
        return "No evaluations to compare"

    # Define metrics to display
    display_metrics = [
        ("F1", "f1"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Exact Match", "exact_match"),
        ("Macro-F1", "macro_f1"),
        ("Jaccard", "jaccard"),
        ("Semantic", "semantic_match_rate"),
        ("ROUGE-1", "rouge_1")
    ]

    # Add weighted metrics if available
    weighted_metrics = []
    first_eval = evaluations[0]["metrics"]
    if "weighted_macro_f1" in first_eval:
        weighted_metrics.extend([
            ("W-Macro-F1", "weighted_macro_f1"),
            ("W-Macro-P", "weighted_macro_precision"),
            ("W-Macro-R", "weighted_macro_recall")
        ])
    if "weighted_semantic_match_rate" in first_eval:
        weighted_metrics.append(("W-Semantic", "weighted_semantic_match_rate"))

    all_metrics = display_metrics + weighted_metrics

    # Create header
    header_parts = ["Model"] + [name for name, _ in all_metrics]
    header = " | ".join(f"{part:>12}" for part in header_parts)
    separator = "-" * len(header)

    # Create rows
    rows = [header, separator]

    for eval_data in evaluations:
        model_name = eval_data["model"][:12]  # Truncate long model names
        metrics = eval_data["metrics"]

        metric_values = []
        for _, metric_key in all_metrics:
            value = metrics.get(metric_key, 0.0)
            metric_values.append(f"{value:>12.4f}")

        row_parts = [f"{model_name:>12}"] + metric_values
        row = " | ".join(row_parts)
        rows.append(row)

    return "\n".join(rows)


def create_ranking_analysis(evaluations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Create ranking analysis for different metrics.

    Args:
        evaluations: List of evaluation data dictionaries

    Returns:
        Dictionary with rankings for different metrics
    """
    ranking_metrics = [
        ("f1", "F1 Score"),
        ("macro_f1", "Macro-F1"),
        ("exact_match", "Exact Match"),
        ("semantic_match_rate", "Semantic Similarity"),
        ("rouge_1", "ROUGE-1")
    ]

    # Add weighted metrics if available
    if evaluations and "weighted_macro_f1" in evaluations[0]["metrics"]:
        ranking_metrics.append(("weighted_macro_f1", "Weighted Macro-F1"))
    if evaluations and "weighted_semantic_match_rate" in evaluations[0]["metrics"]:
        ranking_metrics.append(("weighted_semantic_match_rate", "Weighted Semantic"))

    rankings = {}

    for metric_key, metric_name in ranking_metrics:
        # Create list of (model, value) pairs
        metric_values = []
        for eval_data in evaluations:
            value = eval_data["metrics"].get(metric_key, 0.0)
            metric_values.append({
                "model": eval_data["model"],
                "file": eval_data["file"],
                "value": value
            })

        # Sort by value (descending)
        metric_values.sort(key=lambda x: x["value"], reverse=True)
        rankings[metric_key] = {
            "name": metric_name,
            "ranking": metric_values
        }

    return rankings


def print_ranking_summary(rankings: Dict[str, Dict[str, Any]]) -> None:
    """Print ranking summary for key metrics.

    Args:
        rankings: Dictionary with ranking data
    """
    print("\n" + "=" * 60)
    print("RANKING SUMMARY")
    print("=" * 60)

    # Show top 3 for key metrics
    key_metrics = ["f1", "macro_f1", "weighted_macro_f1", "weighted_semantic_match_rate"]

    for metric_key in key_metrics:
        if metric_key not in rankings:
            continue

        ranking_data = rankings[metric_key]
        metric_name = ranking_data["name"]
        ranking = ranking_data["ranking"]

        print(f"\n🏆 Top 3 by {metric_name}:")
        print("-" * 30)

        for i, entry in enumerate(ranking[:3], 1):
            medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
            print(f"{medal} {entry['model']}: {entry['value']:.4f}")


def save_comparison_results(comparison_data: Dict[str, Any], output_path: Path) -> None:
    """Save comparison results to JSON file.

    Args:
        comparison_data: Complete comparison analysis
        output_path: Path where to save the results
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)
        print(f"📁 Comparison results saved to: {output_path}")
    except Exception as e:
        print(f"⚠️  Failed to save comparison results: {e}")


def generate_comparison_report(comparison_data: Dict[str, Any], evaluations: List[Dict[str, Any]],
                               rankings: Dict[str, Dict[str, Any]]) -> str:
    """Generate detailed text report of the comparison.

    Args:
        comparison_data: Complete comparison analysis
        evaluations: List of evaluation data
        rankings: Ranking analysis results

    Returns:
        Formatted report string
    """
    report_lines = []

    # Header
    report_lines.append("=" * 80)
    report_lines.append("EVALUATION COMPARISON REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Generated: {comparison_data['comparison_metadata']['timestamp']}")
    report_lines.append(f"Total Evaluations: {comparison_data['comparison_metadata']['total_evaluations']}")
    report_lines.append("")

    # Files compared
    report_lines.append("FILES COMPARED")
    report_lines.append("-" * 40)
    for i, filename in enumerate(comparison_data['comparison_metadata']['evaluations_compared'], 1):
        report_lines.append(f"  {i}. {filename}")
    report_lines.append("")

    # Evaluation details
    report_lines.append("EVALUATION DETAILS")
    report_lines.append("-" * 40)
    for eval_data in evaluations:
        report_lines.append(f"Model: {eval_data['model']}")
        report_lines.append(f"  File: {eval_data['file']}")
        report_lines.append(f"  Samples: {eval_data['total_samples']}")
        report_lines.append(f"  Timestamp: {eval_data.get('timestamp', 'Unknown')}")
        report_lines.append("")

    # Comparison table
    report_lines.append("METRICS COMPARISON TABLE")
    report_lines.append("-" * 40)
    report_lines.append(create_comparison_table(evaluations))
    report_lines.append("")

    # Rankings
    report_lines.append("DETAILED RANKINGS")
    report_lines.append("-" * 40)

    key_metrics = ["f1", "macro_f1", "weighted_macro_f1", "weighted_semantic_match_rate", "exact_match",
                   "semantic_match_rate"]

    for metric_key in key_metrics:
        if metric_key not in rankings:
            continue

        ranking_data = rankings[metric_key]
        metric_name = ranking_data["name"]
        ranking = ranking_data["ranking"]

        report_lines.append(f"\n📊 {metric_name} Rankings:")
        report_lines.append("-" * 30)

        for i, entry in enumerate(ranking, 1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            else:
                medal = f"{i:2d}. "

            report_lines.append(f"{medal}{entry['model']:<25} {entry['value']:.4f}")

    # Best performers summary
    report_lines.append("\n" + "=" * 60)
    report_lines.append("BEST PERFORMERS SUMMARY")
    report_lines.append("=" * 60)

    summary = comparison_data.get('summary', {})

    if 'best_overall' in summary and summary['best_overall']:
        best = summary['best_overall']
        report_lines.append(f"🏆 Best Overall (F1): {best.get('model', 'N/A')} ({best.get('value', 0):.4f})")

    if 'best_weighted' in summary and summary['best_weighted']:
        best = summary['best_weighted']
        report_lines.append(f"⚖️  Best Weighted (Macro-F1): {best.get('model', 'N/A')} ({best.get('value', 0):.4f})")

    if 'best_semantic' in summary and summary['best_semantic']:
        best = summary['best_semantic']
        report_lines.append(f"🧠 Best Semantic: {best.get('model', 'N/A')} ({best.get('value', 0):.4f})")

    # Performance insights
    report_lines.append("\n" + "=" * 60)
    report_lines.append("PERFORMANCE INSIGHTS")
    report_lines.append("=" * 60)

    # Calculate some insights
    f1_scores = [eval_data["metrics"].get("f1", 0.0) for eval_data in evaluations]
    if f1_scores:
        avg_f1 = sum(f1_scores) / len(f1_scores)
        max_f1 = max(f1_scores)
        min_f1 = min(f1_scores)

        report_lines.append(f"F1 Score Statistics:")
        report_lines.append(f"  Average: {avg_f1:.4f}")
        report_lines.append(f"  Best:    {max_f1:.4f}")
        report_lines.append(f"  Worst:   {min_f1:.4f}")
        report_lines.append(f"  Range:   {max_f1 - min_f1:.4f}")

    # Weighted vs Regular comparison if available
    weighted_available = any("weighted_macro_f1" in eval_data["metrics"] for eval_data in evaluations)
    if weighted_available:
        report_lines.append(f"\nWeighted Metrics Analysis:")
        for eval_data in evaluations:
            metrics = eval_data["metrics"]
            regular_f1 = metrics.get("macro_f1", 0.0)
            weighted_f1 = metrics.get("weighted_macro_f1", 0.0)
            improvement = weighted_f1 - regular_f1

            report_lines.append(f"  {eval_data['model'][:20]:<20}: "
                                f"Regular={regular_f1:.4f}, Weighted={weighted_f1:.4f}, "
                                f"Δ={improvement:+.4f}")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def save_comparison_report(report_content: str, output_path: Path) -> None:
    """Save comparison report to text file.

    Args:
        report_content: Formatted report string
        output_path: Path where to save the report
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"📄 Comparison report saved to: {output_path}")
    except Exception as e:
        print(f"⚠️  Failed to save comparison report: {e}")


def main() -> bool:
    """Compare evaluation results."""

    print("=" * 80)
    print("EVALUATION COMPARISON TOOL")
    print("=" * 80)

    # Find result files
    result_files = find_evaluation_results()

    if len(result_files) < 2:
        print("❌ Need at least 2 evaluation result files to compare!")
        print(f"Found {len(result_files)} files in evaluation/results/")
        if len(result_files) == 1:
            print(f"Available file: {result_files[0].name}")
        print("\nRun evaluations first:")
        print("  python scripts/run_evaluation.py")
        return False

    print(f"Found {len(result_files)} evaluation results:")
    for i, file_path in enumerate(result_files, 1):
        print(f"  {i}. {file_path.name}")

    # Load all evaluations
    print(f"\n📊 Loading evaluation results...")
    evaluations = []

    for file_path in result_files:
        eval_data = load_evaluation_result(file_path)
        if eval_data:
            evaluations.append(eval_data)
            print(f"✓ Loaded: {file_path.name}")

    if len(evaluations) < 2:
        print("❌ Need at least 2 valid evaluation files to compare!")
        return False

    print(f"\n✓ Successfully loaded {len(evaluations)} evaluations")

    # Create comparison analysis
    print(f"\n📈 Creating comparison analysis...")

    # Sort evaluations by F1 score for consistent ordering
    evaluations.sort(key=lambda x: x["metrics"].get("f1", 0.0), reverse=True)

    # Create comparison table
    print(f"\n{create_comparison_table(evaluations)}")

    # Create rankings
    rankings = create_ranking_analysis(evaluations)
    print_ranking_summary(rankings)

    # Identify best performers
    print(f"\n" + "=" * 60)
    print("BEST PERFORMERS")
    print("=" * 60)

    if "f1" in rankings:
        best_overall = rankings["f1"]["ranking"][0]
        print(f"🏆 Best Overall (F1): {best_overall['model']} ({best_overall['value']:.4f})")

    if "weighted_macro_f1" in rankings:
        best_weighted = rankings["weighted_macro_f1"]["ranking"][0]
        print(f"⚖️  Best Weighted (Macro-F1): {best_weighted['model']} ({best_weighted['value']:.4f})")

    if "semantic_match_rate" in rankings:
        best_semantic = rankings["semantic_match_rate"]["ranking"][0]
        print(f"🧠 Best Semantic: {best_semantic['model']} ({best_semantic['value']:.4f})")

    # Create complete comparison data
    comparison_data = {
        "comparison_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_evaluations": len(evaluations),
            "evaluations_compared": [eval_data["file"] for eval_data in evaluations]
        },
        "evaluations": evaluations,
        "rankings": rankings,
        "summary": {
            "best_overall": rankings.get("f1", {}).get("ranking", [{}])[0],
            "best_weighted": rankings.get("weighted_macro_f1", {}).get("ranking", [{}])[0],
            "best_semantic": rankings.get("semantic_match_rate", {}).get("ranking", [{}])[0]
        }
    }

    # Prepare output paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    results_dir = project_root / "evaluation" / "results"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_json_path = results_dir / f"comparison_analysis_{timestamp}.json"
    comparison_report_path = results_dir / f"comparison_report_{timestamp}.txt"

    # Save JSON results
    save_comparison_results(comparison_data, comparison_json_path)

    # Generate and save text report
    report_content = generate_comparison_report(comparison_data, evaluations, rankings)
    save_comparison_report(report_content, comparison_report_path)

    print(f"\n✅ Comparison completed successfully!")
    print(f"📁 Results: {comparison_json_path.name}")
    print(f"📄 Report:  {comparison_report_path.name}")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
