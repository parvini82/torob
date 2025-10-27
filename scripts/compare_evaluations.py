#!/usr/bin/env python3
"""Compare multiple evaluation results.

This script loads multiple evaluation result files and compares their metrics,
generating comparison tables and rankings.

Usage:
    python scripts/compare_evaluations.py
"""

from pathlib import Path
from evaluation import SimpleEvaluator, EvaluationConfig


def find_evaluation_results():
    """Find available evaluation result files.

    Returns:
        List of paths to evaluation result files
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    results_dir = project_root / "evaluation" / "results"

    if not results_dir.exists():
        return []

    # Find JSON files that contain evaluation results (not reports)
    result_files = []
    for json_file in results_dir.glob("*.json"):
        # Skip report files
        if "_report" not in json_file.name:
            result_files.append(json_file)

    return sorted(result_files)


def main():
    """Compare evaluation results."""

    print("=" * 80)
    print("EVALUATION COMPARISON TOOL")
    print("=" * 80)

    # Find result files
    result_files = find_evaluation_results()

    if len(result_files) < 2:
        print("❌ Need at least 2 evaluation result files to compare!")
        print(f"Found {len(result_files)} files in evaluation/results/")
        print("\nRun evaluations first:")
        print("  python scripts/run_evaluation.py")
        return False

    print(f"Found {len(result_files)} evaluation results:")
    for i, file_path in enumerate(result_files, 1):
        print(f"  {i}. {file_path.name}")

    # Setup evaluator for comparison
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config = EvaluationConfig(results_dir=project_root / "evaluation" / "results")

    evaluator = SimpleEvaluator(config)

    try:
        # Run comparison
        comparison_results = evaluator.compare_evaluations(result_files)

        if comparison_results:
            print(f"\n✓ Comparison completed!")

            # Show top performer
            if (
                "ranking" in comparison_results
                and "by_macro_f1" in comparison_results["ranking"]
            ):
                top_performer = comparison_results["ranking"]["by_macro_f1"][0]
                print(
                    f"\n🏆 Top Performer (by Macro-F1): {top_performer['model']} ({top_performer['value']:.4f})"
                )

            return True
        else:
            print("❌ Comparison failed - no valid results found")
            return False

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
