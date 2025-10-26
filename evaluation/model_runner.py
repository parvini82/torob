"""Model execution interface for evaluation.

This module handles running models on product data and collecting predictions.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import EvaluationConfig


class ModelRunner:
    """Handles running models on product samples and collecting results.

    This class provides a simple interface to:
    - Load product samples
    - Extract images and pass to models
    - Collect and save predictions
    """

    def __init__(self, config: EvaluationConfig):
        """Initialize model runner with configuration.

        Args:
            config: EvaluationConfig instance
        """
        self.config = config
        self.config.ensure_directories()

    def load_sample(self, sample_path: Path) -> List[Dict[str, Any]]:
        """Load product sample from JSON file.

        Args:
            sample_path: Path to JSON file containing product sample

        Returns:
            List of product dictionaries
        """
        print(f"Loading sample from: {sample_path}")

        with open(sample_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        print(f"✓ Loaded {len(products)} products")
        return products

    def extract_images(self, products: List[Dict[str, Any]]) -> List[str]:
        """Extract image URLs from products.

        Args:
            products: List of product dictionaries

        Returns:
            List of image URLs
        """
        image_urls = []
        for product in products:
            url = product.get("image_url", "")
            if url and url.startswith("http"):
                image_urls.append(url)
            else:
                image_urls.append(None)  # Placeholder for missing images

        valid_images = sum(1 for url in image_urls if url)
        print(f"✓ Extracted {valid_images}/{len(image_urls)} valid image URLs")

        return image_urls

    def run_model_on_sample(self,
                            sample_path: Path,
                            model_function: callable,
                            output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Run model on a complete sample and save results.

        Args:
            sample_path: Path to sample JSON file
            model_function: Function that takes image URL and returns predictions
            output_path: Optional path to save results

        Returns:
            Dictionary containing all results and metadata
        """
        print("=" * 60)
        print("MODEL EVALUATION RUN")
        print("=" * 60)

        # Load sample
        products = self.load_sample(sample_path)
        image_urls = self.extract_images(products)

        # Run predictions
        print(f"Running {self.config.model_name} on {len(products)} products...")

        predictions = []
        ground_truths = []
        start_time = time.time()

        for i, (product, image_url) in enumerate(zip(products, image_urls)):
            print(f"  Processing {i + 1}/{len(products)}: ", end="")

            # Get ground truth
            ground_truth = product.get("entities", [])
            ground_truths.append(ground_truth)

            # Get prediction
            try:
                if image_url:
                    prediction = model_function(image_url)
                    predictions.append(prediction)
                    print(f"✓ Got {len(prediction)} entities")
                else:
                    predictions.append([])
                    print("⚠ No image URL")
            except Exception as e:
                predictions.append([])
                print(f"✗ Error: {e}")

        end_time = time.time()
        duration = end_time - start_time

        # Prepare results
        results = {
            "metadata": {
                "model_name": self.config.model_name,
                "sample_path": str(sample_path),
                "sample_size": len(products),
                "execution_time": duration,
                "timestamp": datetime.now().isoformat(),
            },
            "products": products,
            "predictions": predictions,
            "ground_truths": ground_truths,
            "performance": {
                "total_products": len(products),
                "successful_predictions": sum(1 for p in predictions if p),
                "failed_predictions": sum(1 for p in predictions if not p),
                "avg_time_per_product": duration / len(products) if products else 0,
            }
        }

        # Save results
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"model_results_{self.config.model_name}_{timestamp}.json"
            output_path = self.config.results_dir / filename

        self.save_results(results, output_path)

        print(f"\n✓ Model run completed in {duration:.2f} seconds")
        print(f"📁 Results saved to: {output_path}")

        return results

    def save_results(self, results: Dict[str, Any], output_path: Path) -> None:
        """Save results to JSON file.

        Args:
            results: Results dictionary
            output_path: Path to save results
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✓ Saved results to: {output_path}")


# Example model function signature
def example_model_function(image_url: str) -> List[Dict[str, Any]]:
    """Example model function that takes image URL and returns entities.

    Args:
        image_url: URL of product image

    Returns:
        List of entity dictionaries with 'name' and 'values' keys
    """
    # This is where you'd call your actual model
    # For now, return empty list as placeholder
    return []
