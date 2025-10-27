"""Main evaluator for combining model execution and metrics calculation.

This module provides a simple interface to run complete evaluations:
load sample -> run model -> calculate metrics -> save results.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from .config import EvaluationConfig
from .model_runner import ModelRunner
from .metrics import EntityMetrics


class SimpleEvaluator:
    """Simple evaluator combining model execution and metrics calculation.

    This class orchestrates the complete evaluation pipeline:
    1. Load toy sample
    2. Run model on images
    3. Calculate comprehensive metrics
    4. Save results and generate reports
    """

    def __init__(self, config: EvaluationConfig):
        """Initialize evaluator with configuration.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config
        self.config.ensure_directories()

        # Initialize components
        self.model_runner = ModelRunner(config)
        self.metrics = EntityMetrics(config)

    def run_evaluation(self,
                       sample_path: Path,
                       model_function: Callable[[str], List[Dict[str, Any]]],
                       output_name: Optional[str] = None) -> Dict[str, Any]:
        """Run complete evaluation pipeline.

        Args:
            sample_path: Path to toy sample JSON file
            model_function: Function that takes image URL and returns entity predictions
            output_name: Optional name for output files

        Returns:
            Complete evaluation results
        """
        print("=" * 80)
        print("COMPLETE MODEL EVALUATION PIPELINE")
        print("=" * 80)

        start_time = time.time()

        # Step 1: Run model on sample
        print("\n[STEP 1] Running model predictions...")
        model_results = self.model_runner.run_model_on_sample(
            sample_path=sample_path,
            model_function=model_function
        )

        # Step 2: Calculate metrics
        print("\n[STEP 2] Calculating evaluation metrics...")
        predictions = model_results["predictions"]
        ground_truths = model_results["ground_truths"]

        metrics_results = self.metrics.evaluate_batch(predictions, ground_truths)

        # Step 3: Combine results
        evaluation_results = {
            "evaluation_metadata": {
                "sample_path": str(sample_path),
                "model_name": self.config.model_name,
                "evaluation_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "total_samples": len(predictions)
            },
            "model_execution": model_results["performance"],
            "metrics": metrics_results,
            "detailed_predictions": {
                "predictions": predictions,
                "ground_truths": ground_truths
            } if self.config.precision_digits else None
        }

        # Step 4: Save results
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"evaluation_{self.config.model_name}_{timestamp}"

        results_path = self.save_evaluation_results(evaluation_results, output_name)
        report_path = self.generate_evaluation_report(evaluation_results, output_name)

        # Step 5: Print summary
        self.print_evaluation_summary(evaluation_results)

        print(f"\n✓ Evaluation completed in {evaluation_results['evaluation_metadata']['evaluation_time']:.2f} seconds")
        print(f"📁 Results saved to: {results_path}")
        print(f"📊 Report saved to: {report_path}")

        return evaluation_results

    def save_evaluation_results(self, results: Dict[str, Any], output_name: str) -> Path:
        """Save complete evaluation results to JSON.

        Args:
            results: Complete evaluation results
            output_name: Base name for output file

        Returns:
            Path where results were saved
        """
        output_path = self.config.results_dir / f"{output_name}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return output_path

    def generate_evaluation_report(self, results: Dict[str, Any], output_name: str) -> Path:
        """Generate human-readable evaluation report.

        Args:
            results: Complete evaluation results
            output_name: Base name for output file

        Returns:
            Path where report was saved
        """
        report_path = self.config.results_dir / f"{output_name}_report.txt"

        metrics = results["metrics"]
        metadata = results["evaluation_metadata"]
        performance = results["model_execution"]

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MODEL EVALUATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Metadata
        report_lines.append("EVALUATION METADATA")
        report_lines.append("-" * 40)
        report_lines.append(f"Model Name: {metadata['model_name']}")
        report_lines.append(f"Sample Path: {metadata['sample_path']}")
        report_lines.append(f"Total Samples: {metadata['total_samples']}")
        report_lines.append(f"Evaluation Time: {metadata['evaluation_time']:.2f} seconds")
        report_lines.append(f"Timestamp: {metadata['timestamp']}")
        report_lines.append("")

        # Model Performance
        report_lines.append("MODEL EXECUTION PERFORMANCE")
        report_lines.append("-" * 40)
        report_lines.append(f"Successful Predictions: {performance['successful_predictions']}")
        report_lines.append(f"Failed Predictions: {performance['failed_predictions']}")
        report_lines.append(f"Average Time per Product: {performance['avg_time_per_product']:.3f}s")
        report_lines.append("")

        # Main Metrics (Research Paper Format)
        report_lines.append("EVALUATION METRICS")
        report_lines.append("-" * 40)
        report_lines.append(self.metrics.format_results_table(metrics))
        report_lines.append("")

        # Detailed Metrics
        if "detailed_metrics" in metrics:
            detailed = metrics["detailed_metrics"]
            report_lines.append("DETAILED METRICS")
            report_lines.append("-" * 40)
            report_lines.append(f"Macro Precision: {detailed['macro_precision']:.4f}")
            report_lines.append(f"Macro Recall: {detailed['macro_recall']:.4f}")
            report_lines.append(f"Micro Precision: {detailed['micro_precision']:.4f}")
            report_lines.append(f"Micro Recall: {detailed['micro_recall']:.4f}")
            report_lines.append("")

        # Sample Analysis
        if metrics["per_sample_results"]:
            sample_results = metrics["per_sample_results"]

            # Best and worst samples
            samples_by_f1 = sorted(enumerate(sample_results),
                                   key=lambda x: x[1]["micro_f1"]["f1"], reverse=True)

            report_lines.append("SAMPLE ANALYSIS")
            report_lines.append("-" * 40)
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

        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        return report_path

    def print_evaluation_summary(self, results: Dict[str, Any]) -> None:
        """Print evaluation summary to console.

        Args:
            results: Complete evaluation results
        """
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)

        metrics = results["metrics"]

        # Main metrics table
        print("\nRESEARCH PAPER METRICS:")
        print(self.metrics.format_results_table(metrics))

        # Quick performance overview
        performance = results["model_execution"]
        total = performance["successful_predictions"] + performance["failed_predictions"]
        success_rate = performance["successful_predictions"] / total * 100 if total > 0 else 0

        print(f"\nMODEL EXECUTION:")
        print(f"Success Rate: {success_rate:.1f}% ({performance['successful_predictions']}/{total})")
        print(f"Avg Time/Product: {performance['avg_time_per_product']:.3f}s")

    def compare_evaluations(self, result_files: List[Path]) -> Dict[str, Any]:
        """Compare multiple evaluation results.

        Args:
            result_files: List of paths to evaluation result JSON files

        Returns:
            Comparison analysis
        """
        print("=" * 60)
        print("EVALUATION COMPARISON")
        print("=" * 60)

        evaluations = []

        # Load all evaluations
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    evaluation = json.load(f)
                    evaluations.append({
                        "file": file_path.name,
                        "model": evaluation["evaluation_metadata"]["model_name"],
                        "metrics": evaluation["metrics"]
                    })
                    print(f"✓ Loaded: {file_path.name}")
            except Exception as e:
                print(f"✗ Failed to load {file_path.name}: {e}")

        if len(evaluations) < 2:
            print("Need at least 2 evaluations to compare")
            return {}

        # Create comparison table
        comparison = {
            "evaluations": evaluations,
            "metric_comparison": {},
            "ranking": {}
        }

        # Extract key metrics for comparison
        key_metrics = ["eighty_percent_accuracy", "macro_f1", "micro_f1", "rouge_1", "exact_match_rate"]

        for metric in key_metrics:
            values = []
            for eval_data in evaluations:
                value = eval_data["metrics"].get(metric, 0.0)
                values.append({
                    "model": eval_data["model"],
                    "file": eval_data["file"],
                    "value": value
                })

            # Sort by value (descending)
            values.sort(key=lambda x: x["value"], reverse=True)
            comparison["metric_comparison"][metric] = values

        # Overall ranking (based on macro_f1)
        macro_f1_ranking = comparison["metric_comparison"]["macro_f1"]
        comparison["ranking"]["by_macro_f1"] = macro_f1_ranking

        # Print comparison table
        print(f"\nCOMPARISON TABLE:")
        print(f"{'Model':<20} {'80%Acc':<8} {'Macro-F1':<8} {'Micro-F1':<8} {'ROUGE-1':<8}")
        print("-" * 60)

        for eval_data in evaluations:
            m = eval_data["metrics"]
            print(f"{eval_data['model']:<20} "
                  f"{m.get('eighty_percent_accuracy', 0):<8.2f} "
                  f"{m.get('macro_f1', 0):<8.2f} "
                  f"{m.get('micro_f1', 0):<8.2f} "
                  f"{m.get('rouge_1', 0):<8.2f}")

        return comparison

    def load_evaluation_results(self, results_path: Path) -> Dict[str, Any]:
        """Load evaluation results from JSON file.

        Args:
            results_path: Path to results JSON file

        Returns:
            Evaluation results dictionary
        """
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
