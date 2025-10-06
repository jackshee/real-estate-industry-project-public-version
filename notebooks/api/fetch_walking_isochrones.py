#!/usr/bin/env python3
"""
Walking isochrone fetching script for rental listings data.

This script processes missing walking isochrones data by fetching walking
isochrones using the OpenRouteService API. It takes an API key and a path to
missing isochrones data as command line arguments.

Usage:
    # Using command line arguments
    python fetch_walking_isochrones.py --api-key <key> --input-path <path>

    # Using environment variables (recommended)
    python fetch_walking_isochrones.py --input-path <path>
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
            logging.FileHandler("walking_isochrone_fetch.log"),
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


def fetch_walking_isochrones(gdf, geoutils, batch_size=500):
    """
    Fetch walking isochrones for the given data.

    Args:
        gdf (geopandas.GeoDataFrame): Data with geometry column
        geoutils (GeoUtils): Initialized GeoUtils instance
        batch_size (int): Number of records to process at once

    Returns:
        pandas.DataFrame: Updated data with walking isochrones
    """
    logger = logging.getLogger(__name__)

    # Process in batches
    for i in range(0, len(gdf), batch_size):
        batch_end = min(i + batch_size, len(gdf))
        gdf_batch = gdf.iloc[i:batch_end].copy()

        logger.info(
            f"Processing walking isochrones for batch {i//batch_size + 1} (records {i+1}-{batch_end})"
        )

        try:
            # Fetch walking isochrones
            walking_result = gdf_batch["geometry"].apply(
                lambda x: geoutils.get_isochrone_with_delay(
                    profile="foot-walking", range_values=[300, 600, 900], coordinate=x
                )
            )

            # Convert results to DataFrame, handling None values
            walking_df = pd.DataFrame(
                walking_result.tolist(),
                columns=["walking_5min", "walking_10min", "walking_15min"],
            )

            # Replace None values with NaN
            walking_df = walking_df.where(pd.notnull(walking_df), None)

            # Update the batch with walking results
            gdf_batch.loc[:, ["walking_5min", "walking_10min", "walking_15min"]] = (
                walking_df.values
            )

            # Update the original dataframe
            gdf.iloc[i:batch_end] = gdf_batch

            logger.info(
                f"Successfully processed walking isochrones for batch {i//batch_size + 1}"
            )

        except Exception as e:
            logger.error(
                f"Error processing walking isochrones for batch {i//batch_size + 1}: {e}"
            )
            continue

    return gdf


def update_main_dataset(gdf_processed, main_dataset_path):
    """
    Update the main dataset with processed walking isochrone data.
    Only merges rows that have non-null walking isochrone data.

    Args:
        gdf_processed (geopandas.GeoDataFrame): Processed data with walking isochrones
        main_dataset_path (str): Path to the main dataset CSV file
    """
    logger = logging.getLogger(__name__)

    try:
        # Load the main dataset
        logger.info(f"Loading main dataset from: {main_dataset_path}")
        df_main = pd.read_csv(main_dataset_path)

        logger.info(
            f"Number of missing walking coordinates before imputation: {df_main['walking_5min'].isnull().sum()}"
        )

        # Select only the walking isochrone columns we need from processed data for the merge
        walking_cols = [
            "property_id",
            "walking_5min",
            "walking_10min",
            "walking_15min",
        ]
        gdf_subset = gdf_processed[walking_cols].copy()

        # Filter to only include rows that have at least one non-null walking isochrone value
        has_walking_data = (
            gdf_subset["walking_5min"].notna()
            | gdf_subset["walking_10min"].notna()
            | gdf_subset["walking_15min"].notna()
        )

        # Only keep rows with at least one non-null walking isochrone value
        gdf_subset_filtered = gdf_subset[has_walking_data].copy()

        logger.info(
            f"Filtered to {len(gdf_subset_filtered)} rows with non-null walking isochrone data out of {len(gdf_subset)} total processed rows"
        )

        if len(gdf_subset_filtered) == 0:
            logger.warning(
                "No rows with valid walking isochrone data to merge. Skipping dataset update."
            )
            return

        # Perform left join to update df with walking isochrone data
        df_updated = df_main.merge(
            gdf_subset_filtered, on="property_id", how="left", suffixes=("", "_new")
        )

        # Update the original columns with the new data where it's not null
        for col in ["walking_5min", "walking_10min", "walking_15min"]:
            # Only update where the original value is null and the new value is not null
            mask = df_updated[col].isnull() & df_updated[f"{col}_new"].notnull()
            df_updated.loc[mask, col] = df_updated.loc[mask, f"{col}_new"]

        # Drop the temporary columns
        df_updated = df_updated.drop(
            columns=[
                f"{col}_new"
                for col in ["walking_5min", "walking_10min", "walking_15min"]
            ]
        )

        logger.info(
            f"Number of missing walking coordinates after imputation: {df_updated['walking_5min'].isnull().sum()}"
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
        gdf_processed (geopandas.GeoDataFrame): Processed data with walking isochrones
    """
    logger = logging.getLogger(__name__)

    try:
        # Read the current missing isochrones file
        missing_isochrones = pd.read_csv(input_path)

        # Find which property_ids were successfully processed (have at least one non-null walking isochrone)
        has_walking_data = (
            gdf_processed["walking_5min"].notna()
            | gdf_processed["walking_10min"].notna()
            | gdf_processed["walking_15min"].notna()
        )

        # Get property_ids that were successfully processed
        successfully_processed_ids = set(
            gdf_processed[has_walking_data]["property_id"].tolist()
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
    """Main function to orchestrate the walking isochrone fetching process."""
    parser = argparse.ArgumentParser(
        description="Fetch walking isochrones for missing rental listings data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables (recommended - set ORS_API_KEY in .env)
  python fetch_walking_isochrones.py --input-path ../data/raw/missing_isochrones_0.csv
  
  # Using command line arguments
  python fetch_walking_isochrones.py --api-key abc123 --input-path ../data/raw/missing_isochrones_0.csv
  
  # With custom main dataset and testing with limited records
  python fetch_walking_isochrones.py --input-path ../data/raw/missing_isochrones_0.csv --max-records 50
        """,
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouteService API key for walking isochrones (or set ORS_API_KEY env var)",
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
        logger.info("Initializing GeoUtils instance for walking isochrones...")
        geoutils_walking = GeoUtils(ors_api_key=api_key)

        # Fetch walking isochrones
        logger.info("Starting walking isochrones fetch...")
        gdf = fetch_walking_isochrones(gdf, geoutils_walking, args.batch_size)

        # Update main dataset
        logger.info("Updating main dataset...")
        update_main_dataset(gdf, args.main_dataset)

        # Update missing isochrones file
        logger.info("Updating missing isochrones file...")
        update_missing_isochrones_file(args.input_path, gdf)

        logger.info("Walking isochrone fetching completed successfully!")

    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
