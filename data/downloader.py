"""Data downloading and extraction utilities.

This module provides functionality to download data from Google Drive
and extract ZIP files for processing. Operates independently from
sample generation.
"""

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from .config import DownloadConfig


class DataDownloader:
    """Handles downloading and extraction of dataset files from Google Drive.

    This class provides methods to:
    - Install required dependencies (gdown)
    - Download files from Google Drive
    - Extract ZIP archives
    - Load and validate JSON data
    """

    def __init__(self, config: DownloadConfig):
        """Initialize downloader with configuration.

        Args:
            config: DownloadConfig instance with paths and settings
        """
        self.config = config
        self.config.ensure_directories()

    def _install_gdown(self) -> bool:
        """Install gdown package if not already available.

        Returns:
            bool: True if installation successful or already installed
        """
        try:
            pass

            print("✓ gdown is already installed")
            return True
        except ImportError:
            print("Installing gdown package...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
                print("✓ Successfully installed gdown")
                return True
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install gdown: {e}")
                return False

    def _download_from_drive(self, output_path: Path) -> bool:
        """Download file from Google Drive.

        Args:
            output_path: Path where to save the downloaded file

        Returns:
            bool: True if download successful
        """
        if not self._install_gdown():
            return False

        try:
            import gdown

            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"Downloading from Google Drive to {output_path}...")
            gdown.download(self.config.google_drive_url, str(output_path), quiet=False)

            if output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"✓ Successfully downloaded {file_size_mb:.2f} MB")
                return True
            else:
                print("✗ Download completed but file not found")
                return False

        except Exception as e:
            print(f"✗ Error downloading file: {e}")
            return False

    def _extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """Extract ZIP file to specified directory.

        Args:
            zip_path: Path to ZIP file
            extract_to: Directory to extract files to

        Returns:
            bool: True if extraction successful
        """
        try:
            print(f"Extracting {zip_path} to {extract_to}...")

            # Create extraction directory
            extract_to.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)

            print(f"✓ Successfully extracted to: {extract_to}")
            return True

        except Exception as e:
            print(f"✗ Error extracting ZIP: {e}")
            return False

    def _discover_json_files(self, directory: Path) -> List[Path]:
        """Find all JSON files in directory and subdirectories.

        Args:
            directory: Directory to search

        Returns:
            List of Path objects for found JSON files
        """
        json_files = list(directory.rglob("*.json"))
        print(f"Found {len(json_files)} JSON files")

        for idx, file_path in enumerate(json_files, 1):
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  {idx}. {file_path.name} ({file_size_mb:.2f} MB)")

        return json_files

    def _load_json_data(self, json_files: List[Path]) -> List[Dict[str, Any]]:
        """Load data from multiple JSON files.

        Args:
            json_files: List of JSON file paths

        Returns:
            List of product dictionaries from all files
        """
        all_products = []

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle both array of objects and single object
                if isinstance(data, list):
                    products = data
                elif isinstance(data, dict):
                    products = [data]
                else:
                    print(f"  ⚠ Unexpected data type in {json_file.name}: {type(data)}")
                    continue

                all_products.extend(products)
                print(f"  ✓ Loaded {len(products)} products from {json_file.name}")

            except Exception as e:
                print(f"  ✗ Error loading {json_file.name}: {e}")

        print(f"\n✓ Total products loaded: {len(all_products)}")
        return all_products

    def download(self) -> List[Dict[str, Any]]:
        """Complete pipeline to download, extract and load dataset.

        Returns:
            List of product dictionaries

        Raises:
            RuntimeError: If any step of the download process fails
        """
        print("=" * 60)
        print("DATA DOWNLOAD PIPELINE")
        print("=" * 60)

        # Define paths
        zip_file_path = self.config.raw_data_dir / "dataset.zip"
        extract_dir = self.config.raw_data_dir / "extracted"

        # Step 1: Download from Google Drive
        print("\n[STEP 1] Downloading dataset from Google Drive...")
        if not self._download_from_drive(zip_file_path):
            raise RuntimeError("Failed to download dataset")

        # Step 2: Extract ZIP file
        print("\n[STEP 2] Extracting ZIP file...")
        if not self._extract_zip(zip_file_path, extract_dir):
            raise RuntimeError("Failed to extract dataset")

        # Step 3: Discover JSON files
        print("\n[STEP 3] Discovering JSON files...")
        json_files = self._discover_json_files(extract_dir)

        if not json_files:
            raise RuntimeError("No JSON files found in extracted data")

        # Step 4: Load JSON data
        print("\n[STEP 4] Loading JSON data...")
        all_products = self._load_json_data(json_files)

        if not all_products:
            raise RuntimeError("No products loaded from JSON files")

        print(f"✓ Download completed: {len(all_products)} products ready")
        return all_products
