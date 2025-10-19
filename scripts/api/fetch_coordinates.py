#!/usr/bin/env python3
"""
Geocode addresses using OpenRouteService API
"""

import argparse
import os
import sys
import logging
import time
import random
from pathlib import Path

import pandas as pd
import openrouteservice as ors
from shapely.geometry import Point
from dotenv import load_dotenv


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}")


def load_input_data(input_file_path, address_column):
    """Load input CSV file with addresses to geocode"""
    input_path = Path(input_file_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    logger.info(f"Loading input data from {input_file_path}")
    df = pd.read_csv(input_file_path, low_memory=False)

    if address_column not in df.columns:
        raise ValueError(
            f"Address column '{address_column}' not found in CSV file. Available columns: {df.columns.tolist()}"
        )

    logger.info(f"Loaded {len(df)} records from input file")
    return df


def geocode_ors(client, address, max_retries=5, base_delay=1.0):
    """
    Geocode address using OpenRouteService API.
    Implements exponential backoff with jitter to handle rate limiting.
    Returns None immediately if quota is exceeded.

    Args:
        client: OpenRouteService client instance
        address (str): Address to geocode
        max_retries (int): Maximum number of retry attempts (default: 5)
        base_delay (float): Base delay in seconds for exponential backoff (default: 1.0)

    Returns:
        tuple: (longitude, latitude, success_status) or (None, None, False) if geocoding fails
    """
    if pd.isna(address) or not address:
        return None, None, False

    for attempt in range(max_retries + 1):
        try:
            geocode = client.pelias_search(
                text=address,
                validate=False,
            )

            if geocode["features"]:
                coords = geocode["features"][0]["geometry"]["coordinates"]
                logger.info(f"Successfully geocoded address: {address}")
                return coords[0], coords[1], True  # longitude, latitude
            else:
                logger.warning(f"No results found for address: {address}")
                return None, None, False

        except Exception as e:
            error_str = str(e).lower()

            # Check for quota/quota exceeded errors - return None immediately
            if any(
                quota_error in error_str
                for quota_error in [
                    "quota",
                    "quota exceeded",
                    "rate limit exceeded",
                    "limit exceeded",
                ]
            ):
                logger.error(
                    f"Quota exceeded for OpenRouteService. Skipping address: {address}"
                )
                return None, None, False

            if attempt < max_retries:
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed for {address}: {e}")
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logger.error(
                    f"Error getting coordinates for {address} after {max_retries + 1} attempts: {e}"
                )
                return None, None, False

    return None, None, False


def geocode_with_delay(client, address, delay_range=(0.1, 0.5)):
    """
    Wrapper function that adds a small delay between API calls for OpenRouteService geocoding.

    Args:
        client: OpenRouteService client instance
        address (str): Address to geocode
        delay_range (tuple): Min and max delay in seconds (default: 0.1-0.5)

    Returns:
        tuple: (longitude, latitude, success_status)
    """
    result = geocode_ors(client, address)
    # Add a small random delay between calls to avoid rate limiting
    time.sleep(random.uniform(*delay_range))
    return result


def process_addresses(df, address_column, client, use_delay=True):
    """
    Process all addresses in the dataframe and geocode them.

    Args:
        df: Input dataframe
        address_column: Name of column containing addresses
        client: OpenRouteService client instance
        use_delay: Whether to add delay between API calls (default: True)

    Returns:
        DataFrame with added coordinate columns
    """
    logger.info(f"Processing {len(df)} addresses...")

    # Initialize new columns
    df["longitude"] = None
    df["latitude"] = None
    df["coordinates"] = None
    df["geocode_success"] = False

    successful = 0
    failed = 0

    for idx, row in df.iterrows():
        address = row[address_column]

        try:
            if use_delay:
                lon, lat, success = geocode_with_delay(client, address)
            else:
                lon, lat, success = geocode_ors(client, address)

            if success:
                df.loc[idx, "longitude"] = lon
                df.loc[idx, "latitude"] = lat
                df.loc[idx, "coordinates"] = f"POINT ({lon} {lat})"
                df.loc[idx, "geocode_success"] = True
                successful += 1
                logger.info(
                    f"[{idx+1}/{len(df)}] Successfully geocoded: {address} -> ({lon:.6f}, {lat:.6f})"
                )
            else:
                failed += 1
                logger.warning(f"[{idx+1}/{len(df)}] Failed to geocode: {address}")

            # Log progress every 10 addresses
            if (idx + 1) % 10 == 0:
                logger.info(
                    f"Progress: {idx+1}/{len(df)} addresses processed (Success: {successful}, Failed: {failed})"
                )

        except Exception as e:
            logger.error(f"Error processing address at index {idx}: {e}")
            failed += 1
            continue

    logger.info(
        f"Geocoding completed: {successful} successful, {failed} failed out of {len(df)} total"
    )
    return df


def save_results(df, output_path):
    """Save results to CSV file"""
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    if not output_path.parent.exists():
        logger.info(f"Creating output directory: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving results to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved successfully")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Geocode addresses using OpenRouteService API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable for API key
  python fetch_coordinates.py --input-file data/raw/missing_coordinates/batch_0001.csv \\
                               --api-key ORS_API_KEY1

  # Using direct API key
  python fetch_coordinates.py --input-file data/raw/missing_coordinates/batch_0001.csv \\
                               --api-key 5b3ce3597851110001cf6248abc123def456 \\
                               --address-column address

  # Custom output directory
  python fetch_coordinates.py --input-file data/raw/missing_coordinates/batch_0001.csv \\
                               --api-key ORS_API_KEY1 \\
                               --output-dir data/processed/coordinates
        """,
    )

    parser.add_argument(
        "--input-file", required=True, help="Path to input CSV file with addresses"
    )

    parser.add_argument(
        "--api-key",
        required=True,
        help="OpenRouteService API key environment variable name (e.g., ORS_API_KEY1) or direct API key",
    )

    parser.add_argument(
        "--address-column",
        default="address",
        help="Column name containing addresses to geocode (default: address)",
    )

    parser.add_argument(
        "--output-dir",
        default="data/processed/coordinates",
        help="Output directory for results (default: data/processed/coordinates)",
    )

    parser.add_argument(
        "--no-delay",
        action="store_true",
        help="Disable delay between API calls (not recommended)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Maximum number of retry attempts per address (default: 5)",
    )

    args = parser.parse_args()

    # Load environment variables
    load_environment()

    # Get API key - either from environment variable name or direct key
    if args.api_key.startswith("ORS_API_KEY"):
        # It's an environment variable name
        api_key = os.getenv(args.api_key)
        if not api_key:
            logger.error(f"Environment variable {args.api_key} not found")
            sys.exit(1)
        logger.info(f"Using API key from environment variable {args.api_key}")
    else:
        # It's a direct API key
        api_key = args.api_key
        logger.info("Using direct API key")

    logger.info(f"API key starts with: {api_key[:10]}...")

    try:
        # Initialize ORS client
        client = ors.Client(key=api_key)
        logger.info("Initialized OpenRouteService client")

        # Load input data
        df = load_input_data(args.input_file, args.address_column)

        # Process addresses
        processed_df = process_addresses(
            df, args.address_column, client, use_delay=not args.no_delay
        )

        # Generate output filename
        input_filename = Path(args.input_file).stem
        output_filename = f"{input_filename}_geocoded.csv"
        output_path = Path(args.output_dir) / output_filename

        # Save results
        save_results(processed_df, output_path)

        # Print summary
        success_count = processed_df["geocode_success"].sum()
        total_count = len(processed_df)
        logger.info(
            f"Processing completed successfully! Geocoded {success_count}/{total_count} addresses ({success_count/total_count*100:.1f}%)"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
