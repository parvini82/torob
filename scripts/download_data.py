#!/usr/bin/env python3
"""Download dataset from Google Drive.

Usage:
    python scripts/download_data.py
"""

from pathlib import Path
from data import DataDownloader, DownloadConfig

project_root = Path(__file__).resolve().parent.parent


def main():
    """Download and extract dataset from Google Drive."""

    # Configuration
    config = DownloadConfig(
        drive_file_id="1Coixw-ZELOorizi4K-RSBtzDnRAQ2c_g",  # Your existing file ID
        data_dir=Path(project_root / "data"),
    )

    # Download
    downloader = DataDownloader(config)
    try:
        products = downloader.download()
        print(f"\n🎉 Success! Downloaded {len(products)} products")
        return products
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    main()
