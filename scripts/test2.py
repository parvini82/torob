import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Callable
import os
from dotenv import load_dotenv
import requests

# Load .env file
load_dotenv()

VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen/qwen2.5-vl-32b-instruct:free")

from src.service.langgraph.langgraph_service import run_langgraph_on_url

def example_model_function_with_rate_limit(image_url: str, max_retries: int = 5, base_delay: float = 5.0) -> List[Dict[str, Any]]:
    """Model function with rate limit handling and exponential backoff.

    Args:
        image_url: URL of product image
        max_retries: Maximum number of retries for rate limit errors
        base_delay: Initial delay (seconds) before retrying

    Returns:
        List of entity dictionaries
    """
    attempt = 0
    while attempt <= max_retries:
        output_model = run_langgraph_on_url(image_url)
        if output_model is None:
            return []  # If no result is returned, return an empty list

        # Try to handle rate limit errors
        try:
            entities = output_model.get('persian', {}).get('entities', [])
            return entities
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                sleep_time = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue  # Retry
            else:
                raise  # non-rate limit error: raise the exception
        except Exception as e:
            # Catching other exceptions including rate limit messages
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 429:
                sleep_time = base_delay * (2 ** attempt)
                print(f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue
            if "Rate limit exceeded" in str(e):
                sleep_time = base_delay * (2 ** attempt)
                print(f"Rate limit hit. Waiting {sleep_time} seconds before retrying (attempt {attempt+1}/{max_retries})...")
                time.sleep(sleep_time)
                attempt += 1
                continue
            raise  # Unrecognized error: raise

    print("Rate limit retry limit reached; skipping image.")
    return []

def handle_failed_predictions(input_file: Path, output_file: Path) -> None:
    """Handle failed predictions by re-running them with the model.

    Args:
        input_file: Path to the evaluation output file
        output_file: Path to save the updated results
    """
    print("Reading the evaluation results...")
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # Prepare to write the updated results
    updated_results = []
    failed_predictions = 0
    successful_predictions = 0

    # Go through each result
    for result in results:
        if result.get('status') == 'failed':
            print(f"Re-running failed prediction for image: {result.get('image_url')}")
            try:
                prediction = example_model_function_with_rate_limit(result.get("image_url"))
                result["predictions"] = prediction
                result["status"] = "success"
                successful_predictions += 1
                print(f"✓ Successfully re-processed {result.get('image_url')}")
            except Exception as e:
                print(f"❌ Failed to re-process {result.get('image_url')}: {e}")
                result["error"] = str(e)
                failed_predictions += 1
        updated_results.append(result)

    # Save the updated results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(updated_results, f, ensure_ascii=False, indent=2)

    print(f"Evaluation completed with {successful_predictions} successful re-processed predictions and {failed_predictions} failed.")

def main():
    """Main function to handle failed predictions and re-run them."""
    input_file = Path("/Users/work/Desktop/DataScience/RahnemaCollege/final_project/torob/evaluation/results/evaluation_toy_sample_min_8_entities-3.json")  # Replace with actual path
    output_file = Path("/Users/work/Desktop/DataScience/RahnemaCollege/final_project/torob/evaluation/results/evaluation_toy_sample_min_8_entities-3-updated.json")  # Replace with actual path

    # Handle failed predictions
    handle_failed_predictions(input_file, output_file)

if __name__ == "__main__":
    main()
