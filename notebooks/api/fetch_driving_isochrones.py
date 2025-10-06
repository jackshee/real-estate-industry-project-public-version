#!/usr/bin/env python3
"""
Driving isochrone fetching script for rental listings data.

This script processes missing driving isochrones data by fetching driving
isochrones using the OpenRouteService API. It takes an API key and a path to
missing isochrones data as command line arguments.

Usage:
    # Using command line arguments
    python fetch_driving_isochrones.py --api-key <key> --input-path <path>

    # Using environment variables (recommended)
    python fetch_driving_isochrones.py --input-path <path>
"""

import argparse
import sys
import os
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from shapely.geometry import Point
from shapely import wkt
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import GeoUtils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.geo import GeoUtils


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("driving_isochrone_fetch.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_missing_isochrones_data(input_path):
    """
    Load and process missing isochrones data.

    Args:
        input_path (str): Path to the missing isochrones CSV file

    Returns:
        geopandas.GeoDataFrame: Processed data with geometry column
    """
    logger = logging.getLogger(__name__)

    try:
        # Read the CSV file
        logger.info(f"Loading missing isochrones data from: {input_path}")
        gdf = gpd.read_file(input_path)

        # Convert property_id to int
        gdf["property_id"] = gdf["property_id"].astype(int)

        # Convert coordinates to Point objects
        sample_coords = gdf["coordinates"].iloc[0]
        logger.info(f"Sample coordinate format: {sample_coords}")

        if isinstance(sample_coords, str) and sample_coords.startswith("POINT"):
            # Handle WKT POINT format: "POINT (lon lat)"
            gdf["geometry"] = gdf["coordinates"].apply(lambda coord: wkt.loads(coord))
            logger.info("Successfully converted WKT POINT strings to Point objects")
        else:
            raise ValueError("Unexpected coordinate format. Expected WKT POINT format.")

        logger.info(
            f"Loaded {len(gdf)} records with {gdf['geometry'].notna().sum()} valid points"
        )
        return gdf

    except Exception as e:
        logger.error(f"Error loading missing isochrones data: {e}")
        raise


def fetch_driving_isochrones(gdf, geoutils, batch_size=500):
    """
    Fetch driving isochrones for the given data.

    Args:
        gdf (geopandas.GeoDataFrame): Data with geometry column
        geoutils (GeoUtils): Initialized GeoUtils instance
        batch_size (int): Number of records to process at once

    Returns:
        pandas.DataFrame: Updated data with driving isochrones
    """
    logger = logging.getLogger(__name__)

    # Process in batches
    for i in range(0, len(gdf), batch_size):
        batch_end = min(i + batch_size, len(gdf))
        gdf_batch = gdf.iloc[i:batch_end].copy()

        logger.info(
            f"Processing driving isochrones for batch {i//batch_size + 1} (records {i+1}-{batch_end})"
        )

        try:
            # Fetch driving isochrones
            driving_result = gdf_batch["geometry"].apply(
                lambda x: geoutils.get_isochrone_with_delay(
                    profile="driving-car", range_values=[300, 600, 900], coordinate=x
                )
            )

            # Convert results to DataFrame, handling None values
            driving_df = pd.DataFrame(
                driving_result.tolist(),
                columns=["driving_5min", "driving_10min", "driving_15min"],
            )

            # Replace None values with NaN
            driving_df = driving_df.where(pd.notnull(driving_df), None)

            # Update the batch with driving results
            gdf_batch.loc[:, ["driving_5min", "driving_10min", "driving_15min"]] = (
                driving_df.values
            )

            # Update the original dataframe
            gdf.iloc[i:batch_end] = gdf_batch

            logger.info(
                f"Successfully processed driving isochrones for batch {i//batch_size + 1}"
            )

        except Exception as e:
            logger.error(
                f"Error processing driving isochrones for batch {i//batch_size + 1}: {e}"
            )
            continue

    return gdf


def update_main_dataset(gdf_processed, main_dataset_path):
    """
    Update the main dataset with processed driving isochrone data.
    Only merges rows that have non-null driving isochrone data.

    Args:
        gdf_processed (geopandas.GeoDataFrame): Processed data with driving isochrones
        main_dataset_path (str): Path to the main dataset CSV file
    """
    logger = logging.getLogger(__name__)

    try:
        # Load the main dataset
        logger.info(f"Loading main dataset from: {main_dataset_path}")
        df_main = pd.read_csv(main_dataset_path)

        logger.info(
            f"Number of missing driving coordinates before imputation: {df_main['driving_5min'].isnull().sum()}"
        )

        # Select only the driving isochrone columns we need from processed data for the merge
        driving_cols = [
            "property_id",
            "driving_5min",
            "driving_10min",
            "driving_15min",
        ]
        gdf_subset = gdf_processed[driving_cols].copy()

        # Filter to only include rows that have at least one non-null driving isochrone value
        has_driving_data = (
            gdf_subset["driving_5min"].notna()
            | gdf_subset["driving_10min"].notna()
            | gdf_subset["driving_15min"].notna()
        )

        # Only keep rows with at least one non-null driving isochrone value
        gdf_subset_filtered = gdf_subset[has_driving_data].copy()

        logger.info(
            f"Filtered to {len(gdf_subset_filtered)} rows with non-null driving isochrone data out of {len(gdf_subset)} total processed rows"
        )

        if len(gdf_subset_filtered) == 0:
            logger.warning(
                "No rows with valid driving isochrone data to merge. Skipping dataset update."
            )
            return

        # Perform left join to update df with driving isochrone data
        df_updated = df_main.merge(
            gdf_subset_filtered, on="property_id", how="left", suffixes=("", "_new")
        )

        # Update the original columns with the new data where it's not null
        for col in ["driving_5min", "driving_10min", "driving_15min"]:
            # Only update where the original value is null and the new value is not null
            mask = df_updated[col].isnull() & df_updated[f"{col}_new"].notnull()
            df_updated.loc[mask, col] = df_updated.loc[mask, f"{col}_new"]

        # Drop the temporary columns
        df_updated = df_updated.drop(
            columns=[
                f"{col}_new"
                for col in ["driving_5min", "driving_10min", "driving_15min"]
            ]
        )

        logger.info(
            f"Number of missing driving coordinates after imputation: {df_updated['driving_5min'].isnull().sum()}"
        )

        # Save the updated dataset
        df_updated.to_csv(main_dataset_path, index=False)
        logger.info(f"Updated main dataset saved to: {main_dataset_path}")

        # Create backup
        backup_path = main_dataset_path.replace(".csv", "_backup.csv")
        df_updated.to_csv(backup_path, index=False)
        logger.info(f"Backup created at: {backup_path}")

    except Exception as e:
        logger.error(f"Error updating main dataset: {e}")
        raise


def update_missing_isochrones_file(input_path, gdf_processed):
    """
    Update the missing isochrones file by removing records that were successfully processed.

    Args:
        input_path (str): Path to the missing isochrones CSV file
        gdf_processed (geopandas.GeoDataFrame): Processed data with driving isochrones
    """
    logger = logging.getLogger(__name__)

    try:
        # Read the current missing isochrones file
        missing_isochrones = pd.read_csv(input_path)

        # Find which property_ids were successfully processed (have at least one non-null driving isochrone)
        has_driving_data = (
            gdf_processed["driving_5min"].notna()
            | gdf_processed["driving_10min"].notna()
            | gdf_processed["driving_15min"].notna()
        )

        # Get property_ids that were successfully processed
        successfully_processed_ids = set(
            gdf_processed[has_driving_data]["property_id"].tolist()
        )

        # Remove successfully processed records from missing isochrones
        remaining_records = missing_isochrones[
            ~missing_isochrones["property_id"].isin(successfully_processed_ids)
        ]

        # Save the updated file
        remaining_records.to_csv(input_path, index=False)
        logger.info(
            f"Updated missing isochrones file. Removed {len(successfully_processed_ids)} successfully processed records, {len(remaining_records)} remaining"
        )

    except Exception as e:
        logger.error(f"Error updating missing isochrones file: {e}")
        raise


def main():
    """Main function to orchestrate the driving isochrone fetching process."""
    parser = argparse.ArgumentParser(
        description="Fetch driving isochrones for missing rental listings data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables (recommended - set ORS_API_KEY in .env)
  python fetch_driving_isochrones.py --input-path ../data/raw/missing_isochrones_0.csv
  
  # Using command line arguments
  python fetch_driving_isochrones.py --api-key abc123 --input-path ../data/raw/missing_isochrones_0.csv
  
  # With custom main dataset and testing with limited records
  python fetch_driving_isochrones.py --input-path ../data/raw/missing_isochrones_0.csv --max-records 50
        """,
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouteService API key for driving isochrones (or set ORS_API_KEY env var)",
    )
    parser.add_argument(
        "--input-path", required=True, help="Path to the missing isochrones CSV file"
    )
    parser.add_argument(
        "--main-dataset",
        default="../data/curated/rent_features/cleaned_listings_sampled.csv",
        help="Path to the main dataset CSV file (default: ../data/curated/rent_features/cleaned_listings_sampled.csv)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of records to process in each batch (default: 500)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum number of records to process (default: all records)",
    )

    args = parser.parse_args()

    # Set up logging
    logger = setup_logging()

    # Get API key from arguments or environment variables
    api_key = args.api_key or os.getenv("ORS_API_KEY")

    # Validate API key is provided
    if not api_key:
        logger.error(
            "API key not provided. Use --api-key or set ORS_API_KEY environment variable"
        )
        sys.exit(1)

    try:
        # Validate input file exists
        if not os.path.exists(args.input_path):
            logger.error(f"Input file does not exist: {args.input_path}")
            sys.exit(1)

        # Validate main dataset file exists
        if not os.path.exists(args.main_dataset):
            logger.error(f"Main dataset file does not exist: {args.main_dataset}")
            sys.exit(1)

        # Load missing isochrones data
        gdf = load_missing_isochrones_data(args.input_path)

        # Limit records if specified
        if args.max_records:
            gdf = gdf.head(args.max_records)
            logger.info(f"Limited processing to {len(gdf)} records")

        # Initialize GeoUtils instance
        logger.info("Initializing GeoUtils instance for driving isochrones...")
        geoutils_driving = GeoUtils(ors_api_key=api_key)

        # Fetch driving isochrones
        logger.info("Starting driving isochrones fetch...")
        gdf = fetch_driving_isochrones(gdf, geoutils_driving, args.batch_size)

        # Update main dataset
        logger.info("Updating main dataset...")
        update_main_dataset(gdf, args.main_dataset)

        # Update missing isochrones file
        logger.info("Updating missing isochrones file...")
        update_missing_isochrones_file(args.input_path, gdf)

        logger.info("Driving isochrone fetching completed successfully!")

    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
