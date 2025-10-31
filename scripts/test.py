#!/usr/bin/env python3
"""Run model evaluation on toy sample with step-by-step progress and incremental saving.

This script:
1. Loads toy sample
2. Runs the model on product images (one at a time with progress)
3. Saves each result immediately after prediction
4. Handles rate limit (HTTP 429) with exponential backoff
5. Generates a report with the saved model output
6. Limits the request rate to 15 per minute

Usage:
    python scripts/run_evaluation_verbose.py
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import os
from dotenv import load_dotenv
import requests

# Load .env file
load_dotenv()

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")

from src.service.workflow.langgraph_service import run_langgraph_on_url

# Track the time of the last request
last_request_time = None

# Maximum requests per minute
MAX_REQUESTS_PER_MINUTE = 15

# Calculate delay time between requests to limit the rate
delay_time = 60 / MAX_REQUESTS_PER_MINUTE


def example_model_function_with_rate_limit(image_url: str, max_retries: int = 5, base_delay: float = 5.0) -> List[
    Dict[str, Any]]:
    """Model function with rate limit handling and exponential backoff.

    Args:
        image_url: URL of product image
        max_retries: Maximum number of retries for rate limit errors
        base_delay: Initial delay (seconds) before retrying

    Returns:
        List of entity dictionaries
    """
    global last_request_time

    attempt = 0
    while attempt <= max_retries:
        # Wait if necessary to maintain the 15 requests per minute rate
        if last_request_time:
            time_since_last_request = time.time() - last_request_time
            if time_since_last_request < delay_time:
                sleep_time = delay_time - time_since_last_request
                print(f"  💡 Sleeping for {sleep_time:.2f}s to maintain request rate...")
                time.sleep(sleep_time)

        # Make the request
        output_model = run_langgraph_on_url(image_url)

        # Update the last request time
        last_request_time = time.time()

        if output_model is None:
            return []  # If no result is returned, return an empty list

        # Try to handle rate limit errors
        try:
            entities = output_model.get('persian', {}).get('entities', [])
            return entities
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                sleep_time = base_delay * (2 ** attempt)  # Exponential backoff
                print(
                    f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue  # Retry
            else:
                raise  # non-rate limit error: raise the exception
        except Exception as e:
            # Catching other exceptions including rate limit messages
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 429:
                sleep_time = base_delay * (2 ** attempt)
                print(
                    f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue
            if "Rate limit exceeded" in str(e):
                sleep_time = base_delay * (2 ** attempt)
                print(
                    f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue
            raise  # Unrecognized error: raise

    print("Rate limit retry limit reached; skipping image.")
    return []


def find_toy_sample():
    """Find available toy sample files.

    Returns:
        Path to toy sample file or None if not found
    """
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    processed_dir = project_root / "data" / "processed"

    if not processed_dir.exists():
        return None

    sample_names = [
        "toy_sample_min_8_entities-2.json"
    ]

    for sample_name in sample_names:
        sample_path = processed_dir / sample_name
        if sample_path.exists():
            return sample_path

    toy_samples = list(processed_dir.glob("toy_sample*.json"))
    if toy_samples:
        return toy_samples[0]

    return None


class EvaluationConfig:
    """Configuration for evaluation pipeline."""

    def __init__(self, results_dir: Path, model_name: str, precision_digits: int):
        self.results_dir = results_dir
        self.model_name = model_name
        self.precision_digits = precision_digits
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure results directory exists."""
        if not self.results_dir.exists():
            print(f"Creating directory: {self.results_dir}")
            self.results_dir.mkdir(parents=True)  # Creates the directory if it doesn't exist


class VerboseEvaluator:
    """Evaluator with step-by-step progress and incremental saving."""

    def __init__(self, config: EvaluationConfig):
        """Initialize evaluator with configuration.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config
        self.config.ensure_directories()

    def run_evaluation(self,
                       sample_path: Path,
                       model_function: Callable[[str], List[Dict[str, Any]]],
                       output_name: Optional[str] = None) -> Dict[str, Any]:
        """Run evaluation pipeline with verbose progress and incremental saving.

        Args:
            sample_path: Path to toy sample JSON file
            model_function: Function that takes image URL and returns entity predictions
            output_name: Optional name for output files

        Returns:
            Model output results
        """
        print("=" * 80)
        print("MODEL EVALUATION PIPELINE (VERBOSE MODE)")
        print("=" * 80)

        start_time = time.time()

        # Step 1: Load sample data
        print("\n[STEP 1] Loading toy sample...")
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)

        total_products = len(sample_data)
        print(f"✓ Loaded {total_products} products from {sample_path.name}")

        # Prepare output filename
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"evaluation_{self.config.model_name.replace('/', '_')}_{timestamp}"

        # Prepare output paths
        results_path = self.config.results_dir / f"{output_name}-3.json"
        progress_path = self.config.results_dir / f"{output_name}_progress-3.jsonl"

        print(f"\n[STEP 2] Running model predictions...")
        print(f"Results will be saved to: {results_path}")
        print(f"Progress log: {progress_path}")
        print("-" * 80)

        output_results = []
        successful_predictions = 0
        failed_predictions = 0

        # Clear progress file if it exists
        if progress_path.exists():
            progress_path.unlink()

        for idx, product in enumerate(sample_data, 1):
            image_url = product.get("image_url")

            print(f"\n[{idx}/{total_products}] Processing product...")
            print(f"  URL: {image_url}")

            if not image_url:
                print("  ⚠️  No image URL found, skipping...")
                failed_predictions += 1
                continue

            # Time the prediction
            pred_start = time.time()

            try:
                print("  🔄 Running model prediction...")
                prediction = model_function(image_url)
                pred_time = time.time() - pred_start

                result = {
                    "index": idx,
                    "image_url": image_url,
                    "predictions": prediction,
                    "prediction_time_seconds": round(pred_time, 2),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }

                output_results.append(result)
                successful_predictions += 1

                # Print prediction summary
                print(f"  ✓ Prediction complete in {pred_time:.2f}s")
                print(f"  📊 Found {len(prediction)} entities:")
                for entity in prediction[:3]:  # Show first 3 entities
                    entity_name = entity.get('name', 'Unknown')
                    entity_values = entity.get('values', [])
                    print(f"     - {entity_name}: {entity_values}")
                if len(prediction) > 3:
                    print(f"     ... and {len(prediction) - 3} more entities")

            except Exception as e:
                pred_time = time.time() - pred_start
                print(f"  ❌ Prediction failed after {pred_time:.2f}s")
                print(f"  Error: {str(e)}")

                result = {
                    "index": idx,
                    "image_url": image_url,
                    "predictions": [],
                    "prediction_time_seconds": round(pred_time, 2),
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e)
                }

                output_results.append(result)
                failed_predictions += 1

            # Save progress incrementally (append to JSONL)
            with open(progress_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

            # Also update the main results file
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(output_results, f, ensure_ascii=False, indent=2)

            print(f"  💾 Progress saved ({successful_predictions} successful, {failed_predictions} failed)")

        # Final summary
        total_time = time.time() - start_time
        print("\n" + "=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)
        print(f"Total products: {total_products}")
        print(f"Successful predictions: {successful_predictions}")
        print(f"Failed predictions: {failed_predictions}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per prediction: {total_time / total_products:.2f}s")
        print(f"\n✓ Final results saved to: {results_path}")
        print(f"✓ Progress log saved to: {progress_path}")

        return {
            "results": output_results,
            "summary": {
                "total": total_products,
                "successful": successful_predictions,
                "failed": failed_predictions,
                "total_time_seconds": round(total_time, 2),
                "average_time_seconds": round(total_time / total_products, 2)
            }
        }

    def print_model_output_summary(self, output: List[Dict[str, Any]]) -> None:
        """Print model output summary to console.

        Args:
            output: Model output results
        """
        print("\n" + "=" * 60)
        print("MODEL OUTPUT SUMMARY")
        print("=" * 60)

        successful = [r for r in output if r.get('status') == 'success']
        failed = [r for r in output if r.get('status') == 'failed']

        print(f"Total predictions: {len(output)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        if successful:
            print(f"\nExample successful prediction:")
            print(json.dumps(successful[0], ensure_ascii=False, indent=2))

        print("=" * 60)


def main():
    """Run model evaluation pipeline with verbose output."""

    print("=" * 80)
    print("MODEL EVALUATION PIPELINE (VERBOSE MODE)")
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

    # Setup evaluation configuration
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config = EvaluationConfig(
        results_dir=project_root / "evaluation" / "results",
        model_name=VISION_MODEL,
        precision_digits=4
    )

    # Create evaluator
    evaluator = VerboseEvaluator(config)

    print(f"\nStarting evaluation with model: {config.model_name}")

    try:
        # Run evaluation with verbose output
        results = evaluator.run_evaluation(
            sample_path=sample_path,
            model_function=example_model_function_with_rate_limit,
            output_name=f"evaluation_{sample_path.stem}"
        )

        print("\n🎉 Evaluation completed successfully!")
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
