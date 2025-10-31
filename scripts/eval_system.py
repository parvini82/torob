# ============================================================================
# INTEGRATED MULTI-PROVIDER MULTI-MODEL EVALUATION SYSTEM
# ============================================================================
#
# This system orchestrates comprehensive evaluation of multiple (PROVIDER, VLM, LLM)
# combinations with fault tolerance, incremental saving, and performance metrics.
#
# Features:
# - Multi-provider support (OpenRouter, Metis, Together)
# - Two-stage evaluation pipeline (first-pass + failure recovery)
# - Rate limiting with exponential backoff
# - Fault tolerance with automatic resumption
# - Incremental progress saving (JSONL)
# - Structured JSON output with comprehensive metrics
# - Colored logging with file persistence
# - Environment variable configuration per model pair
#
# Usage:
#   python eval_system.py --config model_pairs.json \
#                          --dataset data/processed/Ground_Truth_first10.json \
#                          --output evaluation/results
#
# ============================================================================

import json
import time
import logging
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from workflow.langgraph_service import run_langgraph_on_url


# Load environment variables
load_dotenv()


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

@dataclass
class ModelTriple:
    """Represents a (PROVIDER, VISION_MODEL, TRANSLATE_MODEL) combination."""
    provider: str
    vision_model: str
    translate_model: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "PROVIDER": self.provider,
            "VISION_MODEL": self.vision_model,
            "TRANSLATE_MODEL": self.translate_model
        }


class PredictionStatus(Enum):
    """Status enum for predictions."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored console output."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logger with colored console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (DEBUG level)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limiter for API requests (15 requests/minute)."""

    MAX_REQUESTS_PER_MINUTE = 15

    def __init__(self):
        self.last_request_time: Optional[float] = None
        self.delay_time = 60 / self.MAX_REQUESTS_PER_MINUTE

    def wait_if_needed(self) -> None:
        """Wait to maintain rate limit."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.delay_time:
                sleep_time = self.delay_time - time_since_last
                time.sleep(sleep_time)

    def record_request(self) -> None:
        """Record the time of a request."""
        self.last_request_time = time.time()


# ============================================================================
# ENVIRONMENT MANAGER
# ============================================================================

class EnvironmentManager:
    """Manages environment variables for each model pair."""

    def __init__(self, env_file: Optional[Path] = None):
        self.env_file = env_file or Path('.env')
        self.original_env = dict(os.environ)

    def set_for_model(self, model_triple: ModelTriple) -> None:
        """Set environment variables for a specific model triple."""
        os.environ["PROVIDER"] = model_triple.provider
        os.environ["VISION_MODEL"] = model_triple.vision_model
        os.environ["TRANSLATE_MODEL"] = model_triple.translate_model

    def restore_original(self) -> None:
        """Restore original environment variables."""
        os.environ.clear()
        os.environ.update(self.original_env)


# ============================================================================
# PROGRESS MANAGEMENT
# ============================================================================

@dataclass
class PredictionResult:
    """Single prediction result."""
    index: int
    image_url: str
    predictions: List[Dict[str, Any]]
    ground_truth: List[Dict[str, Any]]
    status: PredictionStatus
    prediction_time_seconds: float
    timestamp: str
    error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'index': self.index,
            'image_url': self.image_url,
            'predictions': self.predictions,
            'ground_truth': self.ground_truth,
            'status': self.status.value,
            'prediction_time_seconds': self.prediction_time_seconds,
            'timestamp': self.timestamp,
            'error': self.error,
            'retry_count': self.retry_count
        }


class ProgressManager:
    """Manages incremental progress saving and resumption."""

    def __init__(self, progress_path: Path, results_path: Path, logger: logging.Logger):
        self.progress_path = progress_path
        self.results_path = results_path
        self.logger = logger

    def save_progress(self, result: PredictionResult) -> None:
        """Append result to JSONL progress file."""
        with open(self.progress_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + '\n')

    def update_results(self, results: List[PredictionResult]) -> None:
        """Update cumulative results JSON file."""
        results_data = [r.to_dict() for r in results]
        with open(self.results_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

    def load_progress(self) -> Tuple[List[PredictionResult], int]:
        """Load existing progress from JSONL file."""
        results = []
        if not self.progress_path.exists():
            return results, 0

        try:
            with open(self.progress_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        result = PredictionResult(
                            index=data['index'],
                            image_url=data['image_url'],
                            predictions=data['predictions'],
                            ground_truth=data['ground_truth'],
                            status=PredictionStatus(data['status']),
                            prediction_time_seconds=data['prediction_time_seconds'],
                            timestamp=data['timestamp'],
                            error=data.get('error'),
                            retry_count=data.get('retry_count', 0)
                        )
                        results.append(result)

            self.logger.debug(f"Loaded {len(results)} existing results from progress file")
            return results, len(results)
        except Exception as e:
            self.logger.error(f"Error loading progress: {e}")
            return results, 0


# ============================================================================
# MODEL EXECUTOR
# ============================================================================

class ModelExecutor:
    """Executes model prediction with rate limiting and retry logic."""

    def __init__(self, vision_model: str, translate_model: str, logger: logging.Logger):
        self.vision_model = vision_model
        self.translate_model = translate_model
        self.rate_limiter = RateLimiter()
        self.logger = logger

    def execute_with_retry(
            self,
            image_url: str,
            max_retries: int = 5,
            base_delay: float = 5.0
    ) -> Tuple[List[Dict[str, Any]], int, Optional[str]]:
        """Execute model with exponential backoff retry."""
        attempt = 0
        last_error = None

        while attempt <= max_retries:
            try:
                self.rate_limiter.wait_if_needed()

                #Import and call the langgraph service
                result = run_langgraph_on_url(image_url)
                entities = result.get('persian', {}).get('entities', [])


                self.rate_limiter.record_request()
                return entities, attempt, None

            except Exception as e:
                error_str = str(e)
                self.rate_limiter.record_request()

                # Check if rate limit error
                is_rate_limit = (
                        "429" in error_str or
                        "rate limit" in error_str.lower()
                )

                if is_rate_limit and attempt < max_retries:
                    sleep_time = base_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limit hit. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                    attempt += 1
                else:
                    last_error = error_str
                    self.logger.error(f"Model execution failed: {error_str}")
                    break

        return [], max_retries, last_error


# ============================================================================
# TAGGING PIPELINE
# ============================================================================

class TaggingPipeline:
    """Main tagging pipeline orchestrator."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.executor: Optional[ModelExecutor] = None

    def set_executor(self, executor: ModelExecutor) -> None:
        """Set the model executor."""
        self.executor = executor

    def run_first_stage(
            self,
            dataset: List[Dict[str, Any]],
            progress_manager: ProgressManager,
            resume: bool = True
    ) -> List[PredictionResult]:
        """Run first-stage tagging pipeline."""
        self.logger.info("=" * 80)
        self.logger.info("🚀 FIRST-STAGE TAGGING PIPELINE")
        self.logger.info("=" * 80)

        results = []
        start_index = 0

        if resume:
            results, start_index = progress_manager.load_progress()
            if start_index > 0:
                self.logger.info(f"Resuming from image {start_index + 1}")

        start_time = time.time()
        total = len(dataset)

        for idx in range(start_index, total):
            product = dataset[idx]
            image_url = product.get('image_url', '')
            ground_truth = product.get('entities', [])

            if not image_url:
                self.logger.warning(f"[{idx + 1}/{total}] No image URL found, skipping...")
                continue

            self.logger.info(f"[{idx + 1}/{total}] Processing: {image_url[:60]}...")

            pred_start = time.time()
            predictions, retry_count, error = self.executor.execute_with_retry(image_url)
            pred_time = time.time() - pred_start

            status = PredictionStatus.SUCCESS if error is None else PredictionStatus.FAILED

            result = PredictionResult(
                index=idx + 1,
                image_url=image_url,
                predictions=predictions,
                ground_truth=ground_truth,
                status=status,
                prediction_time_seconds=round(pred_time, 2),
                timestamp=datetime.now().isoformat(),
                error=error,
                retry_count=retry_count
            )

            results.append(result)
            progress_manager.save_progress(result)
            progress_manager.update_results(results)

            if status == PredictionStatus.SUCCESS:
                self.logger.info(f"  ✅ Success ({len(predictions)} entities, {pred_time:.2f}s)")
            else:
                self.logger.error(f"  ❌ Failed: {error}")

        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r.status == PredictionStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == PredictionStatus.FAILED)

        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"First-stage complete: {successful} successful, {failed} failed in {elapsed:.2f}s")
        self.logger.info("=" * 80)

        return results

    def run_second_stage(
            self,
            results: List[PredictionResult],
            progress_manager: ProgressManager,
            max_iterations: int = 10
    ) -> List[PredictionResult]:
        """Run second-stage recovery for failed predictions."""
        iteration = 1

        while iteration <= max_iterations:
            failed_results = [r for r in results if r.status == PredictionStatus.FAILED]

            if not failed_results:
                self.logger.info("✅ All predictions successful!")
                break

            self.logger.info("\n" + "=" * 80)
            self.logger.info(f"🔄 SECOND-STAGE RECOVERY (Iteration {iteration}/{max_iterations})")
            self.logger.info(f"Re-running {len(failed_results)} failed predictions")
            self.logger.info("=" * 80)

            for result in failed_results:
                self.logger.info(f"[Retry] {result.image_url[:60]}...")

                pred_start = time.time()
                predictions, retry_count, error = self.executor.execute_with_retry(result.image_url)
                pred_time = time.time() - pred_start

                if error is None:
                    result.status = PredictionStatus.SUCCESS
                    result.predictions = predictions
                    result.error = None
                    self.logger.info(f"  ✅ Success ({len(predictions)} entities, {pred_time:.2f}s)")
                else:
                    result.retry_count += 1
                    self.logger.warning(f"  ⚠️ Still failing: {error}")

                result.prediction_time_seconds = round(pred_time, 2)
                result.timestamp = datetime.now().isoformat()
                progress_manager.save_progress(result)
                progress_manager.update_results(results)

            iteration += 1

        failed_count = sum(1 for r in results if r.status == PredictionStatus.FAILED)
        if failed_count > 0:
            self.logger.warning(
                f"⚠️ {failed_count} predictions still failed after {max_iterations} iterations"
            )

        return results


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

class OutputGenerator:
    """Generates structured final output."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def generate_output(
            self,
            results: List[PredictionResult],
            model_triple: ModelTriple,
            execution_time: float,
            sample_path: str
    ) -> Dict[str, Any]:
        """Generate final structured output."""
        successful = sum(1 for r in results if r.status == PredictionStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == PredictionStatus.FAILED)

        metadata = {
            'provider': model_triple.provider,
            'vision_model': model_triple.vision_model,
            'translate_model': model_triple.translate_model,
            'sample_path': sample_path,
            'sample_size': len(results),
            'execution_time': round(execution_time, 2),
            'timestamp': datetime.now().isoformat(),
            'successful_predictions': successful,
            'failed_predictions': failed
        }

        products = [
            {
                'index': r.index,
                'image_url': r.image_url,
                'ground_truth_count': len(r.ground_truth)
            }
            for r in results
        ]

        predictions = [r.predictions for r in results]
        ground_truths = [r.ground_truth for r in results]

        performance = {
            'total_products': len(results),
            'successful_predictions': successful,
            'failed_predictions': failed,
            'success_rate': round(successful / len(results) * 100, 2) if results else 0,
            'avg_time_per_product': round(execution_time / len(results), 2) if results else 0
        }

        return {
            'metadata': metadata,
            'products': products,
            'predictions': predictions,
            'ground_truths': ground_truths,
            'performance': performance
        }


# ============================================================================
# ORCHESTRATION
# ============================================================================

class EvaluationOrchestrator:
    """Orchestrates the complete evaluation pipeline."""

    def __init__(self, model_triples: List[ModelTriple], dataset_path: Path, output_dir: Path):
        self.model_triples = model_triples
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.logger = setup_logger('EvaluationOrchestrator')
        self.env_manager = EnvironmentManager()
        self.pipeline = TaggingPipeline(self.logger)
        self.output_generator = OutputGenerator(self.logger)

    def _load_dataset(self) -> List[Dict[str, Any]]:
        """Load dataset from JSON."""
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        self.logger.info(f"Loaded {len(dataset)} samples from {self.dataset_path}")
        return dataset

    def _sanitize_model_name(self, model_triple: ModelTriple) -> str:
        """Create sanitized directory name for model pair."""
        provider = model_triple.provider.lower()
        vision = model_triple.vision_model.replace('/', '_').replace(':', '')
        translate = model_triple.translate_model.replace('/', '_').replace(':', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{provider}_{vision}_{translate}_{timestamp}"

    def run(self) -> None:
        """Run complete evaluation pipeline."""
        self.logger.info("=" * 80)
        self.logger.info("🎯 INTEGRATED MULTI-MODEL EVALUATION SYSTEM")
        self.logger.info("=" * 80)
        self.logger.info(f"Processing {len(self.model_triples)} model triples\n")

        dataset = self._load_dataset()
        all_results = []

        for pair_idx, model_triple in enumerate(self.model_triples, 1):
            self.logger.info(f"\n{'#' * 80}")
            self.logger.info(f"Model Triple {pair_idx}/{len(self.model_triples)}")
            self.logger.info(f"Provider: {model_triple.provider}")
            self.logger.info(f"Vision Model: {model_triple.vision_model}")
            self.logger.info(f"Translate Model: {model_triple.translate_model}")
            self.logger.info(f"{'#' * 80}\n")

            # Set environment variables for this model pair
            self.env_manager.set_for_model(model_triple)

            # Create output directory
            model_dir = self.output_dir / self._sanitize_model_name(model_triple)
            model_dir.mkdir(parents=True, exist_ok=True)

            progress_path = model_dir / 'progress.jsonl'
            results_path = model_dir / 'results.json'
            final_output_path = model_dir / 'final_output.json'

            progress_manager = ProgressManager(progress_path, results_path, self.logger)

            # Create executor
            executor = ModelExecutor(
                vision_model=model_triple.vision_model,
                translate_model=model_triple.translate_model,
                logger=self.logger
            )
            self.pipeline.set_executor(executor)

            # First stage
            pair_start = time.time()
            results = self.pipeline.run_first_stage(dataset, progress_manager, resume=True)

            # Second stage
            results = self.pipeline.run_second_stage(results, progress_manager, max_iterations=10)

            pair_time = time.time() - pair_start

            # Generate and save output
            output = self.output_generator.generate_output(
                results,
                model_triple,
                pair_time,
                str(self.dataset_path)
            )

            with open(final_output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            self.logger.info(f"✅ Final output saved to {final_output_path}\n")
            all_results.append(output)

        # Summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎉 EVALUATION PIPELINE COMPLETE")
        self.logger.info("=" * 80)

        for idx, output in enumerate(all_results, 1):
            self.logger.info(f"\nModel Triple {idx}:")
            self.logger.info(f"  Provider: {output['metadata']['provider']}")
            self.logger.info(f"  Vision Model: {output['metadata']['vision_model']}")
            self.logger.info(f"  Success Rate: {output['performance']['success_rate']}%")
            self.logger.info(f"  Avg Time: {output['performance']['avg_time_per_product']}s")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def load_model_pairs(config_path: Path) -> List[ModelTriple]:
    """Load model pairs from JSON configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return [ModelTriple(**pair) for pair in data]
    else:
        raise ValueError("Config file must contain a list of model pairs")


def main():
    """Main entry point with hardcoded parameters."""
    # Directly provide the values for config, dataset, and output
    config_path = Path('model_pairs.json')  # Replace with the actual path to your config file
    dataset_path = Path('../data/processed/Ground_Truth_first10.json')  # Replace with the actual dataset path
    output_dir = Path('evaluation/results')  # Replace with the desired output directory path

    # Validate inputs
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    if not dataset_path.exists():
        print(f"❌ Dataset file not found: {dataset_path}")
        sys.exit(1)

    # Load configuration
    model_triples = load_model_pairs(config_path)
    print(f"Loaded {len(model_triples)} model pairs from {config_path}")

    # Create orchestrator and run
    orchestrator = EvaluationOrchestrator(model_triples, dataset_path, output_dir)
    orchestrator.run()



if __name__ == "__main__":
    main()