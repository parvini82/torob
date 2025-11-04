#!/usr/bin/env python3
# File: scripts/evaluate_scenarios_full.py
# Purpose: Evaluate scenario-based predictions from evaluation/scenario_predictions with full metrics.

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys

# Ensure project root in PYTHONPATH
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evaluation import EvaluationConfig
from evaluation.metrics import MetricsAggregator


def find_latest_scenario_prediction():
    """Find the most recent predictions_*.json under evaluation/scenario_predictions."""
    pred_dir = project_root / "evaluation" / "scenario_predictions"
    if not pred_dir.exists():
        return None
    files = sorted(pred_dir.glob("predictions_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_prediction_data(prediction_path: Path) -> Dict[str, Any]:
    with open(prediction_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ["predictions", "ground_truths", "metadata", "performance"]:
        if key not in data:
            raise ValueError(f"Missing required field in predictions file: {key}")
    return data


def safe_get(val, default=0.0):
    return default if val is None else val


def main():
    pred_path = find_latest_scenario_prediction()
    if pred_path is None:
        print("❌ No scenario prediction files found under evaluation/scenario_predictions.")
        print("   Run: python scripts/run_scenario_predictions.py")
        return False

    print("=" * 80)
    print("SCENARIO FULL EVALUATION (ALL METRICS)")
    print("=" * 80)
    print(f"Using predictions file: {pred_path.name}")

    pred_data = load_prediction_data(pred_path)
    predictions: List[List[Dict[str, Any]]] = pred_data["predictions"]
    ground_truths: List[List[Dict[str, Any]]] = pred_data["ground_truths"]

    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Attach model_name coherently
    model_name = pred_data["metadata"].get("model_name", "unknown_model")
    scenario_meta = pred_data.get("scenario_metadata", {})
    scenario_name = scenario_meta.get("scenario", "unknown_scenario")

    config = EvaluationConfig(
        results_dir=results_dir,
        model_name=f"{scenario_name}__{model_name}",
        precision_digits=4,
    )

    aggregator = MetricsAggregator(config, enabled_metrics=["exact", "similarity", "partial", "lenient"])

    print("\nCalculating metrics (exact, similarity, partial, lenient, ROUGE-1)...")
    results = aggregator.evaluate_batch(predictions, ground_truths)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"evaluation_{config.model_name}_{ts}"

    output_json = results_dir / f"{base_name}.json"
    full_payload = {
        "evaluation_metadata": {
            "prediction_file": str(pred_path),
            "model_name": config.model_name,
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_samples": len(predictions),
            "enabled_metrics": ["exact", "similarity", "partial", "lenient", "rouge_1"]
        },
        "scenario_metadata": scenario_meta,
        "prediction_metadata": pred_data.get("metadata", {}),
        "model_performance": pred_data.get("performance", {}),
        "metrics": results
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False, indent=2)

    report_txt = results_dir / f"{base_name}_report.txt"

    lines = []
    lines.append("=" * 80)
    lines.append("SCENARIO EVALUATION REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("EVALUATION METADATA")
    lines.append("-" * 40)
    lines.append(f"Scenario: {scenario_name}")
    if "models" in scenario_meta:
        lines.append(f"Models: {json.dumps(scenario_meta['models'], ensure_ascii=False)}")
    lines.append(f"Model Name: {config.model_name}")
    lines.append(f"Prediction File: {pred_path}")
    lines.append(f"Total Samples: {len(predictions)}")
    lines.append(f"Timestamp: {datetime.now().isoformat()}")
    lines.append("")

    perf = pred_data.get("performance", {})
    total = max(1, perf.get("successful_predictions", 0) + perf.get("failed_predictions", 0))
    success_rate = (perf.get("successful_predictions", 0) / total) * 100.0
    lines.append("MODEL EXECUTION PERFORMANCE")
    lines.append("-" * 40)
    lines.append(f"Successful Predictions: {perf.get('successful_predictions', 0)}")
    lines.append(f"Failed Predictions:     {perf.get('failed_predictions', 0)}")
    lines.append(f"Success Rate:           {success_rate:.1f}%")
    lines.append(f"Avg Time/Product:       {safe_get(perf.get('avg_time_per_product'), 0.0):.3f}s")
    lines.append("")

    lines.append("EXACT MATCHING (MAVE-style)")
    lines.append("-" * 40)
    lines.append(f"Precision (Micro)\t{results.get('precision', 0.0):.4f}")
    lines.append(f"Recall (Micro)\t\t{results.get('recall', 0.0):.4f}")
    lines.append(f"F1 (Micro)\t\t{results.get('f1', 0.0):.4f}")
    lines.append(f"Precision (Macro)\t{results.get('macro_precision', 0.0):.4f}")
    lines.append(f"Recall (Macro)\t\t{results.get('macro_recall', 0.0):.4f}")
    lines.append(f"F1 (Macro)\t\t{results.get('macro_f1', 0.0):.4f}")
    lines.append(f"Exact Match Rate\t{results.get('exact_match', 0.0):.4f}")
    lines.append("")

    lines.append("SIMILARITY METRICS")
    lines.append("-" * 40)
    lines.append(f"Jaccard\t\t\t{results.get('jaccard', 0.0):.4f}")
    lines.append(f"Dice\t\t\t{results.get('dice', 0.0):.4f}")
    lines.append(f"Semantic Match Rate\t{results.get('semantic_match_rate', 0.0):.4f}")
    if "weighted_semantic_match_rate" in results:
        lines.append(f"Weighted Semantic Rate\t{results.get('weighted_semantic_match_rate', 0.0):.4f}")
    lines.append("")

    lines.append("PARTIAL EVALUATION")
    lines.append("-" * 40)
    lines.append(f"Partial Precision\t{results.get('partial_precision', 0.0):.4f}")
    lines.append(f"Partial Recall\t\t{results.get('partial_recall', 0.0):.4f}")
    lines.append(f"Partial F1\t\t{results.get('partial_f1', 0.0):.4f}")
    lines.append("")

    lines.append("LENIENT EVALUATION")
    lines.append("-" * 40)
    lines.append(f"Lenient Precision\t{results.get('lenient_precision', 0.0):.4f}")
    lines.append(f"Lenient Recall\t\t{results.get('lenient_recall', 0.0):.4f}")
    lines.append(f"Lenient F1\t\t{results.get('lenient_f1', 0.0):.4f}")
    lines.append("")

    lines.append("ADDITIONAL")
    lines.append("-" * 40)
    lines.append(f"ROUGE-1\t\t\t{results.get('rouge_1', 0.0):.4f}")
    if results.get('skipped_samples', 0) > 0:
        lines.append("")
        lines.append(f"Note: {results['skipped_samples']} samples skipped (empty GT)")

    with open(report_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n" + "=" * 60)
    print("SUMMARY (KEY METRICS)")
    print("=" * 60)
    print(f"F1 (Micro):     {results.get('f1', 0.0):.4f}")
    print(f"F1 (Macro):     {results.get('macro_f1', 0.0):.4f}")
    print(f"Exact Match:    {results.get('exact_match', 0.0):.4f}")
    print(f"Jaccard:        {results.get('jaccard', 0.0):.4f}")
    print(f"Lenient F1:     {results.get('lenient_f1', 0.0):.4f}")
    print(f"ROUGE-1:        {results.get('rouge_1', 0.0):.4f}")

    print(f"\n📁 Saved JSON:  {output_json}")
    print(f"📊 Saved Report:{report_txt}")
    return True


if __name__ == "__main__":
    ok = main()
    if not ok:
        sys.exit(1)
