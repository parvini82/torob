"""Tests for the data processing modules.

This module tests the data downloading and sample generation functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from data import DownloadConfig, SampleConfig, DataDownloader, ToySampleGenerator, HighEntitySampleGenerator


class TestDownloadConfig:
    """Test cases for DownloadConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DownloadConfig(
            drive_file_id="test-id",
            data_dir=Path("/tmp/test")
        )

        assert config.drive_file_id == "test-id"
        assert config.data_dir == Path("/tmp/test")
        assert config.raw_data_dir == Path("/tmp/test/raw")
        assert "test-id" in config.google_drive_url

    def test_ensure_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "test_data"
            config = DownloadConfig(
                drive_file_id="test-id",
                data_dir=data_dir
            )

            assert not data_dir.exists()
            config.ensure_directories()
            assert data_dir.exists()
            assert config.raw_data_dir.exists()


class TestSampleConfig:
    """Test cases for SampleConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SampleConfig()

        assert config.target_sample_size == 300
        assert "defined" in config.group_composition
        assert "rare" in config.group_composition
        assert "unknown" in config.group_composition
        assert sum(config.group_composition.values()) == 1.0

    def test_custom_config(self):
        """Test custom configuration values."""
        custom_composition = {"a": 0.5, "b": 0.5}
        config = SampleConfig(
            target_sample_size=100,
            group_composition=custom_composition
        )

        assert config.target_sample_size == 100
        assert config.group_composition == custom_composition


class TestToySampleGenerator:
    """Test cases for ToySampleGenerator class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SampleConfig(
                target_sample_size=50,  # Small for testing
                processed_data_dir=Path(temp_dir)
            )

    @pytest.fixture
    def generator(self, config):
        """Provide ToySampleGenerator instance."""
        return ToySampleGenerator(config)

    @pytest.fixture
    def sample_products(self):
        """Provide sample product data for testing."""
        return [
            {
                "title": "پیراهن آبی مردانه",
                "group": "مردانه",
                "product": "پیراهن",
                "image_url": "https://example.com/image1.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["آبی"]},
                    {"name": "جنس", "values": ["پنبه"]},
                    {"name": "نوع کلی", "values": ["پیراهن"]}
                ]
            },
            {
                "title": "کفش ورزشی زنانه",
                "group": "زنانه",
                "product": "کفش",
                "image_url": "https://example.com/image2.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["مشکی"]},
                    {"name": "نوع کلی", "values": ["کفش"]},
                    {"name": "کاربری", "values": ["ورزشی"]}
                ]
            },
            {
                "title": "ساعت طلایی",
                "group": "نامشخص",
                "product": "ساعت مچی",
                "image_url": "https://example.com/image3.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["طلایی"]},
                    {"name": "جنس", "values": ["فلز"]},
                    {"name": "نوع کلی", "values": ["ساعت"]}
                ]
            }
        ] * 20  # Repeat to have enough samples

    def test_utility_methods(self, generator, sample_products):
        """Test utility methods for product analysis."""
        product = sample_products[0]

        # Test title length
        title_length = generator._get_title_length(product)
        assert title_length > 0

        # Test entity counting
        entity_count = generator._count_entities(product)
        assert entity_count == 3

        # Test entity names extraction
        entity_names = generator._get_entity_names(product)
        assert "رنگ" in entity_names
        assert "جنس" in entity_names

        # Test group name
        group_name = generator._get_group_name(product)
        assert group_name == "مردانه"

        # Test image validity
        is_valid = generator._is_image_url_valid(product)
        assert is_valid is True

    def test_generate_sample(self, generator, sample_products):
        """Test toy sample generation."""
        sample = generator.generate(sample_products, seed=42)

        assert len(sample) <= generator.config.target_sample_size
        assert len(sample) > 0

        # Verify all products have valid images
        for product in sample:
            assert generator._is_image_url_valid(product)

    def test_save_sample(self, generator):
        """Test sample saving functionality."""
        sample_data = [{"test": "data"}]

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generator.save(sample_data, output_path)

            assert output_path.exists()

            # Verify content
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            assert saved_data == sample_data

        finally:
            if output_path.exists():
                output_path.unlink()


class TestHighEntitySampleGenerator:
    """Test cases for HighEntitySampleGenerator class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SampleConfig(
                target_sample_size=20,  # Small for testing
                processed_data_dir=Path(temp_dir)
            )

    @pytest.fixture
    def generator(self, config):
        """Provide HighEntitySampleGenerator instance."""
        return HighEntitySampleGenerator(config, min_entities=2)

    @pytest.fixture
    def sample_products(self):
        """Provide sample product data with varying entity counts."""
        products = []

        # Products with many entities
        for i in range(10):
            products.append({
                "title": f"محصول {i}",
                "image_url": f"https://example.com/image{i}.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["آبی"]},
                    {"name": "جنس", "values": ["پنبه"]},
                    {"name": "نوع", "values": ["لباس"]},
                    {"name": "سایز", "values": ["لارج"]},
                ]
            })

        # Products with few entities
        for i in range(5):
            products.append({
                "title": f"محصول کم {i}",
                "image_url": f"https://example.com/low{i}.jpg",
                "entities": [
                    {"name": "رنگ", "values": ["قرمز"]}
                ]
            })

        return products

    def test_filter_by_entity_count(self, generator, sample_products):
        """Test filtering by entity count."""
        filtered = generator.filter_by_entity_count(sample_products)

        # Should only include products with >= 2 entities
        for product in filtered:
            entity_count = generator._count_entities(product)
            assert entity_count >= generator.min_entities

    def test_analyze_entity_distribution(self, generator, sample_products):
        """Test entity distribution analysis."""
        analysis = generator.analyze_entity_distribution(sample_products)

        assert "total_products" in analysis
        assert "min_entities" in analysis
        assert "max_entities" in analysis
        assert "avg_entities" in analysis
        assert analysis["total_products"] == len(sample_products)

    def test_generate_high_entity_sample(self, generator, sample_products):
        """Test high entity sample generation."""
        sample = generator.generate(sample_products, seed=42)

        # All products in sample should meet entity requirement
        for product in sample:
            entity_count = generator._count_entities(product)
            assert entity_count >= generator.min_entities

        assert len(sample) > 0
        assert len(sample) <= generator.config.target_sample_size


# Mock tests for DataDownloader (since it involves external calls)
class TestDataDownloader:
    """Test cases for DataDownloader class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield DownloadConfig(
                drive_file_id="test-id",
                data_dir=Path(temp_dir)
            )

    @pytest.fixture
    def downloader(self, config):
        """Provide DataDownloader instance."""
        return DataDownloader(config)

    def test_initialization(self, downloader, config):
        """Test downloader initialization."""
        assert downloader.config == config
        assert config.data_dir.exists()
        assert config.raw_data_dir.exists()

    @patch('data.downloader.subprocess.check_call')
    def test_install_gdown_success(self, mock_subprocess, downloader):
        """Test successful gdown installation."""
        # Mock successful installation
        mock_subprocess.return_value = None

        # Mock ImportError for initial import, then success
        with patch('builtins.__import__', side_effect=[ImportError, MagicMock()]):
            result = downloader._install_gdown()
            assert result is True

    def test_extract_zip_invalid_file(self, downloader):
        """Test ZIP extraction with invalid file."""
        invalid_path = Path("/nonexistent/file.zip")
        extract_to = Path("/tmp/extract")

        result = downloader._extract_zip(invalid_path, extract_to)
        assert result is False

    def test_discover_json_files(self, downloader):
        """Test JSON file discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some JSON files
            (temp_path / "test1.json").write_text('{"test": 1}')
            (temp_path / "test2.json").write_text('{"test": 2}')
            (temp_path / "not_json.txt").write_text('not json')

            json_files = downloader._discover_json_files(temp_path)

            assert len(json_files) == 2
            assert all(f.suffix == '.json' for f in json_files)

    def test_load_json_data(self, downloader):
        """Test JSON data loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test JSON files
            test_data1 = [{"id": 1, "name": "test1"}]
            test_data2 = [{"id": 2, "name": "test2"}]

            json_file1 = temp_path / "data1.json"
            json_file2 = temp_path / "data2.json"

            with open(json_file1, 'w', encoding='utf-8') as f:
                json.dump(test_data1, f)

            with open(json_file2, 'w', encoding='utf-8') as f:
                json.dump(test_data2, f)

            json_files = [json_file1, json_file2]
            products = downloader._load_json_data(json_files)

            assert len(products) == 2
            assert products[0]["id"] == 1
            assert products[1]["id"] == 2
