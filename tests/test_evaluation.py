"""Tests for the evaluation module functionality.

This module tests the evaluation components with dummy data to ensure
everything works correctly before running on real samples.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

from evaluation import EvaluationConfig, EntityMetrics, ModelRunner, SimpleEvaluator


class TestEntityMetrics:
    """Test cases for EntityMetrics class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return EvaluationConfig(precision_digits=4)

    @pytest.fixture
    def metrics(self, config):
        """Provide EntityMetrics instance."""
        return EntityMetrics(config)

    @pytest.fixture
    def sample_ground_truth(self):
        """Provide sample ground truth data."""
        return [{"name": "رنگ", "values": ["آبی"]}, {"name": "جنس", "values": ["پنبه"]}]

    def test_exact_match_perfect(self, metrics, sample_ground_truth):
        """Test exact match with perfect prediction."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "جنس", "values": ["پنبه"]},
        ]
        result = metrics.exact_match(predicted, sample_ground_truth)
        assert result == 1.0

    def test_exact_match_partial(self, metrics, sample_ground_truth):
        """Test exact match with partial prediction."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "سایز", "values": ["لارج"]},
        ]
        result = metrics.exact_match(predicted, sample_ground_truth)
        assert result == 0.0

    def test_exact_match_empty_ground_truth(self, metrics):
        """Test exact match with empty ground truth."""
        predicted = []
        ground_truth = []
        result = metrics.exact_match(predicted, ground_truth)
        assert result == 1.0

    def test_eighty_percent_accuracy_pass(self, metrics, sample_ground_truth):
        """Test 80% accuracy with passing case."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "جنس", "values": ["پنبه"]},
        ]
        result = metrics.eighty_percent_accuracy(predicted, sample_ground_truth)
        assert result == 1.0

    def test_eighty_percent_accuracy_fail(self, metrics, sample_ground_truth):
        """Test 80% accuracy with failing case."""
        predicted = [{"name": "برند", "values": ["نایک"]}]
        result = metrics.eighty_percent_accuracy(predicted, sample_ground_truth)
        assert result == 0.0

    def test_micro_f1_perfect(self, metrics, sample_ground_truth):
        """Test Micro-F1 with perfect prediction."""
        predicted = sample_ground_truth.copy()
        result = metrics.micro_f1(predicted, sample_ground_truth)

        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_micro_f1_partial(self, metrics, sample_ground_truth):
        """Test Micro-F1 with partial prediction."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "برند", "values": ["نایک"]},
        ]
        result = metrics.micro_f1(predicted, sample_ground_truth)

        assert 0.0 <= result["precision"] <= 1.0
        assert 0.0 <= result["recall"] <= 1.0
        assert 0.0 <= result["f1"] <= 1.0

    def test_macro_f1_calculation(self, metrics, sample_ground_truth):
        """Test Macro-F1 calculation."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "سایز", "values": ["متوسط"]},
        ]
        result = metrics.macro_f1(predicted, sample_ground_truth)

        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert all(0.0 <= v <= 1.0 for v in result.values())

    def test_rouge_1_calculation(self, metrics, sample_ground_truth):
        """Test ROUGE-1 calculation."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "جنس", "values": ["نخ"]},
        ]
        result = metrics.rouge_1(predicted, sample_ground_truth)

        assert 0.0 <= result <= 1.0

    def test_evaluate_single_sample(self, metrics, sample_ground_truth):
        """Test single sample evaluation."""
        predicted = [
            {"name": "رنگ", "values": ["آبی"]},
            {"name": "جنس", "values": ["پنبه"]},
        ]
        result = metrics.evaluate_single_sample(predicted, sample_ground_truth)

        expected_keys = [
            "exact_match",
            "eighty_percent_accuracy",
            "micro_f1",
            "macro_f1",
            "rouge_1",
        ]
        assert all(key in result for key in expected_keys)

    def test_evaluate_batch(self, metrics):
        """Test batch evaluation."""
        predictions = [
            [{"name": "رنگ", "values": ["آبی"]}],
            [{"name": "جنس", "values": ["پنبه"]}],
            [],
        ]
        ground_truths = [
            [{"name": "رنگ", "values": ["آبی"]}],
            [{"name": "جنس", "values": ["پنبه"]}],
            [{"name": "برند", "values": ["نایک"]}],
        ]

        result = metrics.evaluate_batch(predictions, ground_truths)

        assert result["total_samples"] == 3
        assert "macro_f1" in result
        assert "micro_f1" in result
        assert "rouge_1" in result
        assert "eighty_percent_accuracy" in result
        assert "exact_match_rate" in result

    def test_format_results_table(self, metrics):
        """Test results table formatting."""
        sample_results = {
            "eighty_percent_accuracy": 0.75,
            "macro_f1": 0.65,
            "micro_f1": 0.70,
            "rouge_1": 0.60,
            "exact_match_rate": 0.50,
        }

        table = metrics.format_results_table(sample_results)

        assert "80%Acc." in table
        assert "Macro-F1" in table
        assert "Micro-F1" in table
        assert "ROUGE-1" in table
        assert "0.75" in table


class TestModelRunner:
    """Test cases for ModelRunner class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EvaluationConfig(results_dir=Path(temp_dir))

    @pytest.fixture
    def runner(self, config):
        """Provide ModelRunner instance."""
        return ModelRunner(config)

    @pytest.fixture
    def sample_data(self):
        """Provide sample product data."""
        return [
            {
                "title": "پیراهن آبی",
                "image_url": "https://example.com/image1.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["آبی"]},
                    {"name": "جنس", "values": ["پنبه"]},
                ],
            },
            {
                "title": "کفش ورزشی",
                "image_url": "https://example.com/image2.jpg",
                "entities": [
                    {"name": "نوع", "values": ["کفش"]},
                    {"name": "کاربری", "values": ["ورزشی"]},
                ],
            },
        ]

    def test_load_sample(self, runner, sample_data):
        """Test sample loading from file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(sample_data, f, ensure_ascii=False)
            sample_path = Path(f.name)

        try:
            products = runner.load_sample(sample_path)
            assert len(products) == 2
            assert products[0]["title"] == "پیراهن آبی"
        finally:
            sample_path.unlink()

    def test_extract_images(self, runner, sample_data):
        """Test image URL extraction."""
        image_urls = runner.extract_images(sample_data)

        assert len(image_urls) == 2
        assert "https://example.com/image1.jpg" in image_urls
        assert "https://example.com/image2.jpg" in image_urls

    def test_extract_images_with_invalid_urls(self, runner):
        """Test image extraction with invalid URLs."""
        sample_data = [
            {"title": "Test", "image_url": "invalid-url"},
            {"title": "Test2", "image_url": "https://valid.com/img.jpg"},
            {"title": "Test3"},  # No image_url
        ]

        image_urls = runner.extract_images(sample_data)

        assert len(image_urls) == 3
        assert image_urls[0] is None  # Invalid URL
        assert image_urls[1] == "https://valid.com/img.jpg"  # Valid URL
        assert image_urls[2] is None  # Missing URL


class TestSimpleEvaluator:
    """Test cases for SimpleEvaluator class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EvaluationConfig(results_dir=Path(temp_dir), model_name="test_model")

    @pytest.fixture
    def evaluator(self, config):
        """Provide SimpleEvaluator instance."""
        return SimpleEvaluator(config)

    @pytest.fixture
    def sample_data(self):
        """Provide sample product data."""
        return [
            {
                "title": "تست محصول",
                "image_url": "https://example.com/test.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["قرمز"]},
                    {"name": "جنس", "values": ["پلاستیک"]},
                ],
            }
        ]

    def dummy_model_function(self, image_url: str) -> List[Dict[str, Any]]:
        """Dummy model for testing."""
        return [
            {"name": "رنگ", "values": ["قرمز"]},
            {"name": "جنس", "values": ["پلاستیک"]},
        ]

    def test_run_evaluation(self, evaluator, sample_data):
        """Test complete evaluation pipeline."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(sample_data, f, ensure_ascii=False)
            sample_path = Path(f.name)

        try:
            results = evaluator.run_evaluation(
                sample_path=sample_path,
                model_function=self.dummy_model_function,
                output_name="test_run",
            )

            # Check result structure
            assert "evaluation_metadata" in results
            assert "model_execution" in results
            assert "metrics" in results

            # Check metadata
            metadata = results["evaluation_metadata"]
            assert metadata["model_name"] == "test_model"
            assert metadata["total_samples"] == 1

            # Check metrics
            metrics = results["metrics"]
            assert "macro_f1" in metrics
            assert "micro_f1" in metrics
            assert "rouge_1" in metrics

        finally:
            sample_path.unlink()

    def test_save_evaluation_results(self, evaluator):
        """Test saving evaluation results."""
        test_results = {
            "evaluation_metadata": {"model_name": "test"},
            "metrics": {"macro_f1": 0.85},
        }

        results_path = evaluator.save_evaluation_results(test_results, "test_save")

        assert results_path.exists()
        assert results_path.name == "test_save.json"

        # Verify content
        with open(results_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["evaluation_metadata"]["model_name"] == "test"
        assert saved_data["metrics"]["macro_f1"] == 0.85


class TestEvaluationConfig:
    """Test cases for EvaluationConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EvaluationConfig()

        assert config.results_dir == Path("evaluation/results")
        assert config.model_name == "default_model"
        assert config.precision_digits == 4
        assert config.exact_match_threshold == 1.0
        assert config.partial_match_threshold == 0.8

    def test_custom_config(self):
        """Test custom configuration values."""
        custom_dir = Path("/tmp/custom_results")
        config = EvaluationConfig(
            results_dir=custom_dir, model_name="custom_model", precision_digits=2
        )

        assert config.results_dir == custom_dir
        assert config.model_name == "custom_model"
        assert config.precision_digits == 2

    def test_ensure_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            results_dir = Path(temp_dir) / "test_results"
            config = EvaluationConfig(results_dir=results_dir)

            assert not results_dir.exists()
            config.ensure_directories()
            assert results_dir.exists()


# Integration tests
class TestEvaluationIntegration:
    """Integration tests for the evaluation module."""

    def test_end_to_end_evaluation(self):
        """Test complete end-to-end evaluation workflow."""
        # Create sample data
        sample_data = [
            {
                "title": "محصول تست",
                "image_url": "https://example.com/test.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["آبی"]},
                    {"name": "جنس", "values": ["پنبه"]},
                ],
            }
        ]

        def test_model(image_url: str) -> List[Dict[str, Any]]:
            return [
                {"name": "رنگ", "values": ["آبی"]},
                {"name": "جنس", "values": ["نخ"]},  # Slightly different
            ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup
            config = EvaluationConfig(
                results_dir=Path(temp_dir), model_name="integration_test"
            )
            evaluator = SimpleEvaluator(config)

            # Create sample file
            sample_path = Path(temp_dir) / "test_sample.json"
            with open(sample_path, "w", encoding="utf-8") as f:
                json.dump(sample_data, f, ensure_ascii=False)

            # Run evaluation
            results = evaluator.run_evaluation(
                sample_path=sample_path,
                model_function=test_model,
                output_name="integration_test",
            )

            # Verify results
            assert results["evaluation_metadata"]["total_samples"] == 1
            assert results["metrics"]["total_samples"] == 1

            # Check that files were created
            result_files = list(Path(temp_dir).glob("*.json"))
            report_files = list(Path(temp_dir).glob("*.txt"))

            assert len(result_files) >= 1  # At least the main result file
            assert len(report_files) >= 1  # At least the report file
