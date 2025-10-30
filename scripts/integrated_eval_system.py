
"""
Integrated Multi-Model Evaluation System for AI Tagging Pipeline

Features:
- Provider selection per model pair (OpenRouter or Metis)
- Two-stage evaluation pipeline (first-pass + failure recovery)
- Rate limiting with exponential backoff
- Fault tolerance with automatic resumption
- Incremental progress saving
- Structured JSON output with performance metrics
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

# Import unified model client
from src.service.workflow.model_client import get_model_client, UnifiedModelClient

# Load .env file
load_dotenv()


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output."""
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


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('EvaluationPipeline')
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# DATA MODELS
# ============================================================================

class PredictionStatus(Enum):
    """Status of a prediction."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


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


@dataclass
class EvaluationConfig:
    """Evaluation configuration."""
    model_pairs: List[Dict[str, str]]
    dataset_path: Path
    output_dir: Path
    log_dir: Optional[Path] = None
    resume: bool = True
    max_retries_per_image: int = 5
    max_recovery_iterations: int = 10

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limiter for API requests (15 requests per minute)."""
    MAX_REQUESTS_PER_MINUTE = 15

    def __init__(self):
        self.last_request_time: Optional[float] = None
        self.delay_time = 60 / self.MAX_REQUESTS_PER_MINUTE
        self.logger = logging.getLogger('RateLimiter')

    def wait_if_needed(self) -> None:
        """Wait to maintain rate limit."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.delay_time:
                sleep_time = self.delay_time - time_since_last
                self.logger.info(f"⏱️  Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

    def record_request(self) -> None:
        """Record the time of a request."""
        self.last_request_time = time.time()


# ============================================================================
# MODEL EXECUTOR
# ============================================================================

class ModelExecutor:
    """Executes model function with rate limiting and exponential backoff."""

    def __init__(
            self,
            model_client: UnifiedModelClient,
            vision_model: str,
            logger: logging.Logger
    ):
        self.model_client = model_client
        self.vision_model = vision_model
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
                self.logger.debug(
                    f"Executing model for {image_url[:60]}... "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )

                # Prepare message with image
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": image_url},
                            {
                                "type": "text",
                                "text": "Extract all visible product tags and entities from this image in JSON format with 'entities' key containing array of objects with 'name' and 'values' keys."
                            }
                        ]
                    }
                ]

                # Call model using unified client
                response = self.model_client.call_json(
                    model=self.vision_model,
                    messages=messages,
                    max_retries=1,
                    enforce_json_mode=True
                )

                self.rate_limiter.record_request()

                # Extract entities from response
                result = response.get("json", {})
                entities = result.get("entities", [])

                return entities, attempt, None

            except Exception as e:
                error_str = str(e)
                self.rate_limiter.record_request()

                # Check if it's a rate limit error
                is_rate_limit = (
                        "429" in error_str or
                        "Rate limit" in error_str or
                        "rate limit exceeded" in error_str.lower()
                )

                if is_rate_limit and attempt < max_retries:
                    sleep_time = base_delay * (2 ** attempt)
                    self.logger.warning(
                        f"⚠️  Rate limit hit. Retrying in {sleep_time}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )
                    time.sleep(sleep_time)
                    attempt += 1
                else:
                    last_error = error_str
                    self.logger.error(f"❌ Model execution failed: {error_str}")
                    break

        return [], max_retries, last_error


# ============================================================================
# PROGRESS MANAGEMENT
# ============================================================================

class ProgressManager:
    """Manages progress saving and resumption."""

    def __init__(self, progress_path: Path, results_path: Path, logger: logging.Logger):
        self.progress_path = progress_path
        self.results_path = results_path
        self.logger = logger

    def save_progress(self, result: PredictionResult) -> None:
        """Save progress incrementally to JSONL."""
        with open(self.progress_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + '\n')
        self.logger.debug(f"Progress saved for image {result.index}")

    def update_results(self, results: List[PredictionResult]) -> None:
        """Update main results JSON file."""
        results_dict = [r.to_dict() for r in results]
        with open(self.results_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)
        self.logger.debug(f"Results updated: {len(results)} total")

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

            completed = sum(1 for r in results if r.status == PredictionStatus.SUCCESS)
            self.logger.info(f"Loaded {len(results)} results ({completed} completed)")
            return results, len(results)
        except Exception as e:
            self.logger.error(f"Error loading progress: {e}")
            return results, 0


# ============================================================================
# TAGGING PIPELINE
# ============================================================================

class TaggingPipeline:
    """Main tagging pipeline orchestrator."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.executor: Optional[ModelExecutor] = None

    def set_executor(self, executor: ModelExecutor) -> None:
        """Set the model executor to use."""
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
            image_url = product.get('image_url')
            ground_truth = product.get('entities', [])

            self.logger.info(f"\n[{idx + 1}/{total}] Processing: {image_url[:60]}...")

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
                self.logger.info(f"✅ Success ({len(predictions)} entities, {pred_time:.2f}s)")
            else:
                self.logger.error(f"❌ Failed: {error}")

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
                self.logger.info(f"\n[Retry] {result.image_url[:60]}...")

                pred_start = time.time()
                predictions, retry_count, error = self.executor.execute_with_retry(result.image_url)
                pred_time = time.time() - pred_start

                if error is None:
                    result.status = PredictionStatus.SUCCESS
                    result.predictions = predictions
                    result.error = None
                    self.logger.info(f"✅ Success ({len(predictions)} entities, {pred_time:.2f}s)")
                else:
                    result.retry_count += 1
                    self.logger.warning(f"⚠️  Still failing: {error}")

                result.prediction_time_seconds = round(pred_time, 2)
                result.timestamp = datetime.now().isoformat()
                progress_manager.save_progress(result)

            progress_manager.update_results(results)
            iteration += 1

        failed_count = sum(1 for r in results if r.status == PredictionStatus.FAILED)
        if failed_count > 0:
            self.logger.warning(
                f"⚠️  {failed_count} predictions still failed after {max_iterations} iterations"
            )

        return results


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

class OutputGenerator:
    """Generates structured evaluation output."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def generate_output(
            self,
            results: List[PredictionResult],
            dataset: List[Dict[str, Any]],
            model_pair: Dict[str, str],
            execution_time: float,
            sample_path: str
    ) -> Dict[str, Any]:
        """Generate final structured output."""
        successful = sum(1 for r in results if r.status == PredictionStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == PredictionStatus.FAILED)

        metadata = {
            'vision_model': model_pair.get('VISION_MODEL'),
            'provider': model_pair.get('PROVIDER', 'openrouter'),
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

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.pipeline = TaggingPipeline(self.logger)
        self.output_generator = OutputGenerator(self.logger)

    def _setup_logger(self) -> logging.Logger:
        """Setup logger."""
        log_file = None
        if self.config.log_dir:
            log_file = self.config.log_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        return setup_logging(log_file)

    def _load_dataset(self) -> List[Dict[str, Any]]:
        """Load dataset from JSON."""
        with open(self.config.dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        self.logger.info(f"Loaded dataset: {len(dataset)} samples from {self.config.dataset_path}")
        return dataset

    def run(self) -> None:
        """Run complete evaluation pipeline."""
        self.logger.info("=" * 80)
        self.logger.info("🎯 INTEGRATED MULTI-MODEL EVALUATION SYSTEM")
        self.logger.info("=" * 80)
        self.logger.info(f"Processing {len(self.config.model_pairs)} model pairs")

        dataset = self._load_dataset()

        all_results = []

        for pair_idx, model_pair in enumerate(self.config.model_pairs, 1):
            # Get provider from model pair, default to openrouter
            provider = model_pair.get('PROVIDER', 'openrouter').lower()
            vision_model = model_pair.get('VISION_MODEL')

            self.logger.info(f"\n{'#' * 80}")
            self.logger.info(f"Model Pair {pair_idx}/{len(self.config.model_pairs)}")
            self.logger.info(f"Provider: {provider.upper()}")
            self.logger.info(f"Vision Model: {vision_model}")
            self.logger.info(f"{'#' * 80}")

            # Create output paths
            model_dir = self.config.output_dir / self._sanitize_model_name(model_pair)
            model_dir.mkdir(parents=True, exist_ok=True)

            progress_path = model_dir / 'progress.jsonl'
            results_path = model_dir / 'results.json'
            final_output_path = model_dir / 'final_output.json'

            progress_manager = ProgressManager(progress_path, results_path, self.logger)

            # Create model client with specified provider
            model_client = get_model_client(provider)
            self.logger.info(f"🔌 Using API Provider: {model_client.get_current_provider().upper()}")

            # Create executor with current model pair
            executor = ModelExecutor(
                model_client=model_client,
                vision_model=vision_model,
                logger=self.logger
            )
            self.pipeline.set_executor(executor)

            # First stage
            pair_start = time.time()
            results = self.pipeline.run_first_stage(dataset, progress_manager, resume=self.config.resume)

            # Second stage
            results = self.pipeline.run_second_stage(
                results,
                progress_manager,
                self.config.max_recovery_iterations
            )

            pair_time = time.time() - pair_start

            # Generate output
            output = self.output_generator.generate_output(
                results,
                dataset,
                model_pair,
                pair_time,
                str(self.config.dataset_path)
            )

            # Save final output
            with open(final_output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            self.logger.info(f"✅ Final output saved to {final_output_path}")
            all_results.append(output)

        # Summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎉 EVALUATION PIPELINE COMPLETE")
        self.logger.info("=" * 80)
        for idx, output in enumerate(all_results, 1):
            self.logger.info(f"\nModel Pair {idx}:")
            self.logger.info(f"  Provider: {output['metadata']['provider'].upper()}")
            self.logger.info(f"  Vision Model: {output['metadata']['vision_model']}")
            self.logger.info(f"  Success Rate: {output['performance']['success_rate']}%")
            self.logger.info(f"  Avg Time: {output['performance']['avg_time_per_product']}s")

    @staticmethod
    def _sanitize_model_name(model_pair: Dict[str, str]) -> str:
        """Sanitize model names for directory."""
        provider = model_pair.get('PROVIDER', 'openrouter').lower()
        vision = model_pair.get('VISION_MODEL', 'unknown').replace('/', '_').replace(':', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{provider}_{vision}_{timestamp}"


# ============================================================================
# CONFIGURATION LOADING & MAIN
# ============================================================================

def load_config_file(config_path: Path) -> List[Dict[str, str]]:
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main entry point with configurable settings."""

    # Define input variables directly
    config_path = Path('model_pairs.json')
    dataset_path = Path('../data/processed/Ground_Truth_first10.json')
    output_dir = Path('evaluation/results')
    logs_dir = Path('logs')
    no_resume = False
    max_retries = 1
    max_iterations = 10

    print(f"\n📁 Config: {config_path}")
    print(f"📁 Dataset: {dataset_path}")
    print(f"📁 Output: {output_dir}")
    print()

    # Load configurations from the config file
    config_data = load_config_file(config_path)

    if not isinstance(config_data, list):
        raise ValueError("Config file should contain a list of model pairs")

    # Create evaluation config
    eval_config = EvaluationConfig(
        model_pairs=config_data,
        dataset_path=dataset_path,
        output_dir=output_dir,
        log_dir=logs_dir,
        resume=not no_resume,
        max_retries_per_image=max_retries,
        max_recovery_iterations=max_iterations
    )

    # Run orchestrator
    orchestrator = EvaluationOrchestrator(eval_config)
    orchestrator.run()


if __name__ == '__main__':
    main()