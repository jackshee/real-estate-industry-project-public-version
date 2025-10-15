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
import os
import glob
import pandas as pd
from pathlib import Path
from typing import Optional

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from utils.download import DownloadUtils
from utils.preprocess import PreprocessUtils
from utils.geo import GeoUtils
from utils.load import LoadUtils


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
    geo_utils = GeoUtils()

    # Process live listings
    logging.info("Processing live listings...")
    try:
        df_live = pd.read_csv("data/raw/domain/rental_listings_2025_09.csv")
        df_live_processed = preprocessor.preprocess_live_listings(df_live)
        
        # Select relevant columns
        relevant_columns = [
            'property_id','rental_price', 
            'suburb', 'postcode', 'property_type', 'year', 'quarter',
            'bedrooms', 'bathrooms', 'car_spaces',
            'age_0_to_19', 'age_20_to_39', 'age_40_to_59', 'age_60_plus',
            'agency_name', 'appointment_only', 'avg_days_on_market',
            'description', 'family_percentage',
            'first_listed_date',
            'latitude', 'longitude', 'listing_status', 'long_term_resident', 
            'median_rent_price', 'median_sold_price', 'number_sold',
            'renter_percentage', 'single_percentage'
        ]
        
        available_columns = [col for col in relevant_columns if col in df_live_processed.columns]
        df_live_final = df_live_processed[available_columns].dropna()
        
        # Save processed live listings
        os.makedirs("data/processed/domain", exist_ok=True)
        df_live_final.to_csv("data/processed/domain/live_listings.csv", index=False)
        logging.info(f"Processed live listings: {df_live_final.shape[0]} rows")
        
    except FileNotFoundError:
        logging.warning("Live listings file not found, skipping live listings processing")
        df_live_final = None

    # Process wayback listings
    logging.info("Processing wayback listings...")
    try:
        # Get all wayback CSV files
        csv_files = glob.glob("data/raw/domain/rental_listings_*.csv")
        csv_files = [f for f in csv_files if "rental_listings_2025_09.csv" not in f]
        
        if csv_files:
            dataframes = []
            for csv_file in sorted(csv_files):
                filename = os.path.basename(csv_file)
                parts = filename.replace('.csv', '').split('_')
                year = parts[2]
                month = parts[3]
                
                month_to_quarter = {'03': 1, '06': 2, '09': 3, '12': 4}
                quarter = month_to_quarter.get(month, 'Unknown')
                
                df = pd.read_csv(csv_file)
                df['year'] = int(year)
                df['quarter'] = quarter
                dataframes.append(df)
            
            # Preprocess wayback listings
            df_wayback_processed = preprocessor.preprocess_wayback_listings(dataframes, geo_utils)
            
            # Save processed wayback listings
            df_wayback_processed.to_csv("data/processed/domain/wayback_listings.csv", index=False)
            logging.info(f"Processed wayback listings: {df_wayback_processed.shape[0]} rows")
            
            # Set up geocoding batches
            os.makedirs("data/raw/missing_coordinates", exist_ok=True)
            preprocessor.split_into_batches(
                df_wayback_processed[['property_id', 'address']], 
                1000, 
                "data/raw/missing_coordinates"
            )
            logging.info("Created geocoding batches for wayback listings")
            
        else:
            logging.warning("No wayback listing files found")
            df_wayback_processed = None
            
    except Exception as e:
        logging.error(f"Error processing wayback listings: {e}")
        df_wayback_processed = None

    # Combine datasets if both are available
    if df_live_final is not None and df_wayback_processed is not None:
        logging.info("Combining live and wayback listings...")
        try:
            # Check if geocoded coordinates exist
            if os.path.exists("data/processed/coordinates/geocoded_wayback_listings.csv"):
                df_coordinates = pd.read_csv("data/processed/coordinates/geocoded_wayback_listings.csv")
                df_wayback_with_coords = df_wayback_processed.merge(df_coordinates, on='property_id', how='left')
                df_wayback_with_coords = df_wayback_with_coords[df_wayback_with_coords['coordinates'].notna()]
                df_wayback_with_coords = df_wayback_with_coords.drop(columns=['address'])
                
                # Prepare live listings
                df_live_for_combine = df_live_final.copy()
                if 'coordinates' in df_live_for_combine.columns:
                    df_live_for_combine = df_live_for_combine.drop(columns=['coordinates'])
                
                from shapely.geometry import Point
                df_live_for_combine['coordinates'] = df_live_for_combine.apply(
                    lambda row: Point(row['latitude'], row['longitude']), axis=1
                )
                
                # Combine and sample
                df_combined = preprocessor.combine_and_sample_listings(
                    df_live_for_combine, 
                    df_wayback_with_coords, 
                    sample_ratio=0.5
                )
                
                # Save combined dataset
                df_combined.to_csv("data/processed/domain/cleaned_listings_sampled.csv", index=False)
                logging.info(f"Combined and sampled dataset: {df_combined.shape[0]} rows")
                
            else:
                logging.warning("Geocoded coordinates not found, skipping dataset combination")
                
        except Exception as e:
            logging.error(f"Error combining datasets: {e}")

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


def run_data_loading_pipeline(args: argparse.Namespace) -> None:
    """Run the data loading pipeline."""
    logging.info("Starting data loading pipeline...")

    # Initialize load utils
    loader = LoadUtils(base_data_dir=args.data_dir)

    # Add your data loading operations here
    # Example:
    # all_data = loader.load_all_landing_data()
    # economic_data = loader.load_landing_economic_activity()
    # schools_data = loader.load_landing_schools(year=2024)
    # etc.

    logging.info("Data loading pipeline completed.")


def run_full_pipeline(args: argparse.Namespace) -> None:
    """Run the complete data pipeline."""
    logging.info("Starting full data pipeline...")

    if args.download_only:
        run_download_pipeline(args)
    elif args.preprocess_only:
        run_preprocessing_pipeline(args)
    elif args.geospatial_only:
        run_geospatial_pipeline(args)
    elif args.load_only:
        run_data_loading_pipeline(args)
    else:
        # Run all pipelines in sequence
        run_download_pipeline(args)
        run_preprocessing_pipeline(args)
        run_geospatial_pipeline(args)
        run_data_loading_pipeline(args)

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
        "--load-only",
        action="store_true",
        help="Run only the data loading pipeline",
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
