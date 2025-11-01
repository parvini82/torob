#!/usr/bin/env python3
"""Run model predictions on toy sample and save results.

This script loads a toy sample, runs the model on product images,
and saves the predictions for later evaluation.

Usage:
    python scripts/run_model_predictions.py
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from evaluation import ModelRunner, EvaluationConfig

import time
import random
from typing import List, Dict, Any

from src.service.workflow.langgraph_service import run_langgraph_on_url


def example_model_function(image_url: str) -> List[Dict[str, Any]]:
    """Model function with robust retry logic and error handling.

    Args:
        image_url: URL of product image

    Returns:
        List of entity dictionaries with 'name' and 'values' keys
    """

    # Retry configuration
    MAX_RETRIES = 9
    BASE_DELAY = 20  # Base delay in seconds
    MAX_DELAY = 180  # Maximum delay in seconds

    last_error = None
    total_wait_time = 0

    for attempt in range(MAX_RETRIES + 1):  # +1 for initial attempt
        try:
            if attempt > 0:
                # Calculate delay with exponential backoff + jitter
                delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)
                # Add random jitter (±20% of delay)
                jitter = random.uniform(-0.2 * delay, 0.2 * delay)
                actual_delay = max(5, delay + jitter)  # Minimum 5 seconds

                print(
                    f"    Attempt {attempt + 1}/{MAX_RETRIES + 1} for {image_url[:50]}... (waiting {actual_delay:.1f}s)"
                )
                time.sleep(actual_delay)
                total_wait_time += actual_delay
            else:
                # Initial sleep to prevent rate limiting
                print(f"    Processing {image_url[:50]}... (initial 20s delay)")
                time.sleep(BASE_DELAY)
                total_wait_time += BASE_DELAY

            # Call the actual model
            output_model = run_langgraph_on_url(image_url)

            # Validate output structure
            if not output_model:
                raise ValueError("Model returned empty/null result")

            if "persian" not in output_model:
                raise KeyError("'persian' key not found in model output")

            persian_section = output_model.get("persian")
            if not persian_section or "entities" not in persian_section:
                raise KeyError("'entities' key not found in persian section")

            entities = persian_section.get("entities")
            if not isinstance(entities, list):
                raise TypeError(f"entities is not a list, got: {type(entities)}")

            # Success! Return the entities
            if attempt > 0:
                print(
                    f"    ✓ Success on attempt {attempt + 1} after {total_wait_time:.1f}s total wait time"
                )

            return entities

        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            error_msg = str(e)

            # Check for specific error types that warrant retry
            should_retry = False
            wait_multiplier = 1

            # Rate limiting errors
            if any(
                keyword in error_msg.lower()
                for keyword in [
                    "rate limit",
                    "too many requests",
                    "429",
                    "quota exceeded",
                    "rate exceeded",
                    "throttled",
                ]
            ):
                should_retry = True
                wait_multiplier = 2  # Wait longer for rate limits
                print(f"    ⚠ Rate limit error on attempt {attempt + 1}: {error_msg}")

            # Network/connection errors
            elif any(
                keyword in error_msg.lower()
                for keyword in [
                    "connection",
                    "timeout",
                    "network",
                    "dns",
                    "unreachable",
                    "connection refused",
                    "connection reset",
                    "socket",
                ]
            ):
                should_retry = True
                print(f"    ⚠ Network error on attempt {attempt + 1}: {error_msg}")

            # Server errors (5xx)
            elif any(
                keyword in error_msg.lower()
                for keyword in [
                    "server error",
                    "500",
                    "502",
                    "503",
                    "504",
                    "bad gateway",
                    "service unavailable",
                    "gateway timeout",
                    "internal server error",
                ]
            ):
                should_retry = True
                print(f"    ⚠ Server error on attempt {attempt + 1}: {error_msg}")

            # Temporary service issues
            elif any(
                keyword in error_msg.lower()
                for keyword in [
                    "temporarily unavailable",
                    "service busy",
                    "overloaded",
                    "maintenance",
                    "try again later",
                ]
            ):
                should_retry = True
                wait_multiplier = 1.5
                print(
                    f"    ⚠ Service temporarily unavailable on attempt {attempt + 1}: {error_msg}"
                )

            # Data structure issues (might be temporary)
            elif error_type in ["KeyError", "TypeError", "ValueError"]:
                should_retry = True
                print(
                    f"    ⚠ Data structure error on attempt {attempt + 1}: {error_msg}"
                )

            else:
                # Unknown error - still try once more, but don't wait as long
                should_retry = True
                wait_multiplier = 0.5
                print(
                    f"    ⚠ Unknown error ({error_type}) on attempt {attempt + 1}: {error_msg}"
                )

            # Check if we should retry
            if attempt < MAX_RETRIES and should_retry:
                # Adjust wait time based on error type
                BASE_DELAY = int(BASE_DELAY * wait_multiplier)
                continue
            else:
                # Final attempt failed or error not worth retrying
                break

    # All retries exhausted
    error_type = type(last_error).__name__ if last_error else "Unknown"
    error_msg = str(last_error) if last_error else "Unknown error"

    print(
        f"    ✗ Failed after {MAX_RETRIES + 1} attempts and {total_wait_time:.1f}s total wait time"
    )
    print(f"      Final error ({error_type}): {error_msg}")
    print(f"      Returning empty list for: {image_url[:60]}...")

    return []


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
        "Ground_Truth_first10.json",
        "Ground_Truth.json",
        "toy_sample_high_entity.json",
        "toy_sample_standard.json",
        "toy_sample_min_10_entities.json",
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


def save_prediction_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save prediction results to JSON file.

    Args:
        results: Results dictionary from ModelRunner
        output_path: Path to save results
    """
    # Extract only the essential data for evaluation
    prediction_data = {
        "metadata": results["metadata"],
        "products": results["products"],
        "predictions": results["predictions"],
        "ground_truths": results["ground_truths"],
        "performance": results["performance"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prediction_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Saved predictions to: {output_path}")


def main():
    """Run model predictions on toy sample."""

    print("=" * 80)
    print("MODEL PREDICTION RUNNER")
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
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        print(f"Sample size: {len(sample_data)} products")
    except Exception as e:
        print(f"❌ Error loading sample: {e}")
        return False

    # Setup configuration
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # MODEL_NAME = "your_model"  # Change this based to your model name

    config = EvaluationConfig(
        results_dir=project_root / "evaluation" / "predictions",
    )

    # Create model runner
    runner = ModelRunner(config)

    print(f"\nRunning predictions with model: {config.model_name}")
    print("Note: Using placeholder model function. Replace with your actual model!")

    try:
        # Run model on sample
        results = runner.run_model_on_sample(
            sample_path=sample_path, model_function=example_model_function
        )

        # Save predictions for later evaluation
        output_filename = f"predictions_{config.model_name}_{sample_path.stem}.json"
        output_path = config.results_dir / output_filename

        save_prediction_results(results, output_path)

        print(f"\n🎉 Predictions completed successfully!")
        print(f"📁 Results saved to: {output_path}")
        print(f"\nNext step: Run evaluation script with these predictions")
        print(f"  python scripts/evaluate_predictions.py {output_path}")

        return True

    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
