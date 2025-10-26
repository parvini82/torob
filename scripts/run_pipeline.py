#!/usr/bin/env python3
"""
Pipeline script for Torob project data processing and model evaluation.

This script orchestrates the complete pipeline:
1. Build data and generate toy sample (if not already done)
2. Send toy sample to model service API
3. Save model predictions
4. Run evaluation module and save results

Usage:
    python scripts/run_pipeline.py
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from evaluation.config import EvaluationConfig

# Import evaluation modules
from evaluation.evaluator import ModelEvaluator

# Import the langgraph service
from src.service.langgraph.langgraph_service import run_langgraph_on_url

project_root = Path(__file__).resolve().parent.parent


def setup_paths():
    """Setup project paths and add src to Python path."""
    src_path = project_root / "src"

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    return project_root, src_path


def check_file_exists(file_path: Path) -> bool:
    """Check if file exists and is not empty."""
    return file_path.exists() and file_path.stat().st_size > 0


def build_data() -> bool:
    """
    Execute the build_data.py script to download and create toy sample.

    Returns:
        bool: True if successful, False otherwise
    """
    print("[STEP 1] Building data and generating toy sample...")

    # Check if toy sample already exists
    toy_sample_path = project_root / "data/processed/toy_sample.json"
    if check_file_exists(toy_sample_path):
        print(f"[INFO] Toy sample already exists at {toy_sample_path}")
        return True

    try:
        # Run the build_data script
        result = subprocess.run(
            [sys.executable, "build_data.py"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            print("[OK] Data build completed successfully")
            return True
        else:
            print(f"[ERROR] Data build failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Data build timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"[ERROR] Data build failed with exception: {e}")
        return False


def load_toy_sample(toy_sample_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Load toy sample data from JSON file.

    Args:
        toy_sample_path: Path to toy sample JSON file

    Returns:
        List of toy sample data or None if failed
    """
    try:
        with open(toy_sample_path, "r", encoding="utf-8") as f:
            toy_sample = json.load(f)

        print(f"[OK] Loaded toy sample with {len(toy_sample)} items")
        return toy_sample

    except Exception as e:
        print(f"[ERROR] Failed to load toy sample: {e}")
        return None


def run_model_service(
    toy_sample: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    """
    Send toy sample images to model service API and get predictions.

    Args:
        toy_sample: List of toy sample items

    Returns:
        List of model predictions or None if failed
    """
    print("[STEP 2] Running model service API...")

    try:
        predictions = []

        print(f"[INFO] Processing {len(toy_sample)} samples...")

        # Process each sample
        for i, sample in enumerate(toy_sample):
            try:
                # Get image URL from sample
                image_url = sample.get("image_url")
                if not image_url:
                    print(f"[WARNING] Sample {i} has no image_url, skipping...")
                    predictions.append(
                        {
                            "sample_index": i,
                            "random_key": sample.get("random_key", ""),
                            "error": "No image_url provided",
                            "entities": [],
                        }
                    )
                    continue

                # Call the LangGraph service
                result = run_langgraph_on_url(image_url)

                # Extract Persian entities from result
                persian_output = result.get("persian", {})
                entities = persian_output.get("entities", [])

                # Ensure entities are in the expected format
                if isinstance(entities, dict):
                    # Convert dict format to list format if needed
                    entities = [
                        {"name": name, "values": values}
                        for name, values in entities.items()
                    ]
                elif not isinstance(entities, list):
                    entities = []

                # Create prediction in expected format
                prediction = {
                    "sample_index": i,
                    "random_key": sample.get("random_key", ""),
                    "entities": entities,
                    "english_tags": result.get("english", {}),
                    "persian_tags": result.get("persian", {}),
                    "source_image_url": image_url,
                }

                predictions.append(prediction)

                if (i + 1) % 10 == 0:
                    print(f"[INFO] Processed {i + 1}/{len(toy_sample)} samples")

                # Rate limiting - small delay between requests
                time.sleep(0.2)

            except Exception as e:
                print(f"[WARNING] Failed to process sample {i}: {e}")
                # Add empty prediction to maintain alignment
                predictions.append(
                    {
                        "sample_index": i,
                        "random_key": sample.get("random_key", ""),
                        "error": str(e),
                        "entities": [],
                        "source_image_url": sample.get("image_url", ""),
                    }
                )

        print(f"[OK] Model service completed. Generated {len(predictions)} predictions")
        return predictions

    except ImportError as e:
        print(f"[ERROR] Failed to import LangGraph service: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Model service failed: {e}")
        return None


def save_predictions(
    predictions: List[Dict[str, Any]], output_dir: Path
) -> Optional[Path]:
    """
    Save model predictions to JSON file.

    Args:
        predictions: List of model predictions
        output_dir: Directory to save predictions

    Returns:
        Path to saved predictions file or None if failed
    """
    print("[STEP 3] Saving model predictions...")

    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        predictions_path = output_dir / f"model_predictions_{timestamp}.json"

        # Save predictions
        with open(predictions_path, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)

        print(f"[OK] Predictions saved to {predictions_path}")
        return predictions_path

    except Exception as e:
        print(f"[ERROR] Failed to save predictions: {e}")
        return None


def run_evaluation(
    toy_sample: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    output_dir: Path,
) -> Optional[Dict[str, Any]]:
    """
    Run evaluation module on toy sample and predictions.

    Args:
        toy_sample: Original toy sample data
        predictions: Model predictions
        output_dir: Directory to save evaluation results

    Returns:
        Evaluation results dictionary or None if failed
    """
    print("[STEP 4] Running evaluation...")

    try:
        # Setup evaluation config
        eval_config = EvaluationConfig()
        eval_config.results_dir = output_dir / "evaluation_results"
        eval_config.reports_dir = output_dir / "evaluation_reports"

        # Create evaluator
        evaluator = ModelEvaluator(eval_config)

        # Prepare ground truth entities from toy sample
        ground_truth_entities = []
        predicted_entities = []

        for i, (sample, prediction) in enumerate(zip(toy_sample, predictions)):
            # Extract ground truth entities
            gt_entities = sample.get("entities", [])
            ground_truth_entities.append(gt_entities)

            # Extract predicted entities
            pred_entities = prediction.get("entities", [])
            if isinstance(pred_entities, dict):
                # Convert dict format to list format if needed
                pred_entities = [
                    {"name": name, "values": values}
                    for name, values in pred_entities.items()
                ]
            elif not isinstance(pred_entities, list):
                pred_entities = []

            predicted_entities.append(pred_entities)

        # Run comprehensive evaluation
        session_name = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results = evaluator.run_comprehensive_evaluation(
            toy_sample=toy_sample,
            entity_predictions=predicted_entities,
            entity_ground_truths=ground_truth_entities,
            session_name=session_name,
        )

        # Generate evaluation report
        report_path = evaluator.generate_evaluation_report(
            results, include_detailed=True
        )

        print(f"[OK] Evaluation completed. Report saved to {report_path}")
        return results

    except ImportError as e:
        print(f"[ERROR] Failed to import evaluation modules: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Evaluation failed: {e}")
        return None


def save_evaluation_results(
    results: Dict[str, Any], output_dir: Path
) -> Optional[Path]:
    """
    Save evaluation results to JSON file.

    Args:
        results: Evaluation results dictionary
        output_dir: Directory to save results

    Returns:
        Path to saved results file or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with session info
        session_id = results.get("session_info", {}).get("session_id", "unknown")
        results_path = output_dir / f"pipeline_results_{session_id}.json"

        # Save results
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"[OK] Pipeline results saved to {results_path}")
        return results_path

    except Exception as e:
        print(f"[ERROR] Failed to save evaluation results: {e}")
        return None


def print_summary(results: Dict[str, Any]):
    """Print pipeline execution summary."""
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 60)

    # Session info
    session_info = results.get("session_info", {})
    print(f"Session ID: {session_info.get('session_id', 'N/A')}")
    print(f"Duration: {session_info.get('duration_seconds', 0):.2f} seconds")

    # Sample quality summary
    if "sample_quality" in results:
        sq = results["sample_quality"]
        print(f"\nSample Quality Score: {sq.get('overall_quality_score', 0):.2f}")
        print(f"Sample Size: {sq.get('sample_size', 0)}")

        # Entity coverage
        entity_cov = sq.get("entity_coverage", {})
        print(f"Entity Coverage Rate: {entity_cov.get('entity_coverage_rate', 0):.2%}")

        # Image validity
        img_val = sq.get("image_validity", {})
        print(f"Image Validity Rate: {img_val.get('url_validity_rate', 0):.2%}")

    # Entity extraction summary
    if "entity_extraction" in results:
        ee = results["entity_extraction"]
        macro_avg = ee.get("macro_averages", {})
        print(f"\nEntity Extraction Performance:")
        print(f"Exact Match Rate: {macro_avg.get('exact_match', 0):.2%}")
        print(f"Partial Match F1: {macro_avg.get('partial_match_f1', 0):.3f}")
        print(f"Semantic F1: {macro_avg.get('semantic_f1', 0):.3f}")
        print(f"80% Accuracy Rate: {macro_avg.get('eighty_percent_accuracy', 0):.2%}")

    print("=" * 60)


def main():
    """Main pipeline execution function."""
    print("Starting Torob Data Pipeline...")
    print("=" * 60)

    # Setup paths
    project_root, src_path = setup_paths()

    # Define output directory for this pipeline run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "data" / "pipeline_outputs" / f"run_{timestamp}"

    # Step 1: Build data and generate toy sample
    if not build_data():
        print("[FATAL] Data building failed. Stopping pipeline.")
        sys.exit(1)

    # Load toy sample
    toy_sample_path = project_root / "data" / "processed" / "toy_sample.json"
    toy_sample = load_toy_sample(toy_sample_path)
    if toy_sample is None:
        print("[FATAL] Could not load toy sample. Stopping pipeline.")
        sys.exit(1)

    # Step 2: Run model service
    predictions = run_model_service(toy_sample)
    if predictions is None:
        print("[FATAL] Model service failed. Stopping pipeline.")
        sys.exit(1)

    # Step 3: Save predictions
    predictions_path = save_predictions(predictions, output_dir)
    if predictions_path is None:
        print("[WARNING] Could not save predictions, but continuing...")

    # Step 4: Run evaluation
    evaluation_results = run_evaluation(toy_sample, predictions, output_dir)
    if evaluation_results is None:
        print("[FATAL] Evaluation failed. Stopping pipeline.")
        sys.exit(1)

    # Save final results
    results_path = save_evaluation_results(evaluation_results, output_dir)
    if results_path is None:
        print("[WARNING] Could not save final results")

    # Print summary
    print_summary(evaluation_results)

    print(f"\n[COMPLETED] Pipeline finished successfully!")
    print(f"Output directory: {output_dir}")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Pipeline stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] Unexpected error: {e}")
        sys.exit(1)
