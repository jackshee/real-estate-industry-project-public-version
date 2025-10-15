#!/usr/bin/env python3
"""
Data pipeline script for downloading and preprocessing rental market data.

This script orchestrates the complete data pipeline:
1. Downloads data from various sources using DownloadUtils
2. Preprocesses the data using PreprocessUtils
3. Handles geospatial operations using GeoUtils

Usage:
    python scripts/run_data_pipeline.py                    # Run full pipeline
    python scripts/run_data_pipeline.py --download-only    # Run only downloads
    python scripts/run_data_pipeline.py --preprocess-only  # Run only preprocessing
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from utils.download import DownloadUtils
from utils.preprocess import PreprocessUtils
from utils.geo import GeoUtils


def run_download_pipeline(args: argparse.Namespace) -> None:
    """Run the data download pipeline."""
    logging.info("Starting data download pipeline...")

    # Initialize download utils
    downloader = DownloadUtils(base_data_dir=args.data_dir)

    # Add your download steps here
    # Example:
    # downloader.download_economic_data()
    # downloader.download_rental_listings()
    # etc.

    logging.info("Download pipeline completed.")


def run_preprocessing_pipeline(args: argparse.Namespace) -> None:
    """Run the data preprocessing pipeline."""
    logging.info("Starting data preprocessing pipeline...")

    # Initialize preprocessing utils
    preprocessor = PreprocessUtils()

    # Add your preprocessing steps here
    # Example:
    # preprocessor.clean_rental_listings()
    # preprocessor.merge_datasets()
    # etc.

    logging.info("Preprocessing pipeline completed.")


def run_geospatial_pipeline(args: argparse.Namespace) -> None:
    """Run the geospatial operations pipeline."""
    logging.info("Starting geospatial operations pipeline...")

    # Initialize geo utils
    geo_utils = GeoUtils()

    # Add your geospatial operations here
    # Example:
    # geo_utils.process_coordinates()
    # geo_utils.generate_isochrones()
    # etc.

    logging.info("Geospatial pipeline completed.")


def run_full_pipeline(args: argparse.Namespace) -> None:
    """Run the complete data pipeline."""
    logging.info("Starting full data pipeline...")

    if args.download_only:
        run_download_pipeline(args)
    elif args.preprocess_only:
        run_preprocessing_pipeline(args)
    elif args.geospatial_only:
        run_geospatial_pipeline(args)
    else:
        # Run all pipelines in sequence
        run_download_pipeline(args)
        run_preprocessing_pipeline(args)
        run_geospatial_pipeline(args)

    logging.info("Full pipeline completed.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the complete data pipeline for rental market analysis."
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="../data/",
        help="Base directory for data storage",
    )

    parser.add_argument(
        "--download-only", action="store_true", help="Run only the download pipeline"
    )

    parser.add_argument(
        "--preprocess-only",
        action="store_true",
        help="Run only the preprocessing pipeline",
    )

    parser.add_argument(
        "--geospatial-only",
        action="store_true",
        help="Run only the geospatial operations pipeline",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for the script",
    )

    return parser.parse_args()


def configure_logging(level: str) -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )


def main() -> None:
    """Main entry point for the data pipeline script."""
    args = parse_args()
    configure_logging(args.log_level)
    run_full_pipeline(args)


if __name__ == "__main__":
    main()
