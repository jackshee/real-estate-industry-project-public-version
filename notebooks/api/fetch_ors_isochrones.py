#!/usr/bin/env python3
"""
Direct isochrone fetching script for rental listings data using OpenRouteService API.

This script fetches driving isochrones for property listings using the OpenRouteService API
directly via HTTP requests. It can process single listings or batches of listings.

Usage:
    # Single listing example
    python fetch_isochrones_direct.py --input-file data/raw/missing_routes/missing_routes_0.csv --max-records 1

    # Multiple listings (5 records)
    python fetch_isochrones_direct.py --input-file data/raw/missing_routes/missing_routes_0.csv --max-records 5

    # All listings in file
    python fetch_isochrones_direct.py --input-file data/raw/missing_routes/missing_routes_0.csv
"""

import argparse
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import geopandas as gpd
import requests
from shapely.wkt import loads
from dotenv import load_dotenv


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("isochrone_fetch.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger = logging.getLogger(__name__)
        logger.warning(f"No .env file found at {env_path}")


def load_listings_data(listings_file_path: str) -> gpd.GeoDataFrame:
    """Load property listings data and convert coordinates to geometry"""
    logger = logging.getLogger(__name__)

    listings_path = Path(listings_file_path)
    if not listings_path.exists():
        raise FileNotFoundError(f"Listings file not found: {listings_file_path}")

    logger.info(f"Loading listings data from {listings_file_path}")

    # Read CSV file
    cleaned_listings = pd.read_csv(listings_file_path, low_memory=False)

    def fix_wkt_coordinates(wkt_string):
        """Fix WKT coordinates from (lat lon) to (lon lat) format"""
        import re

        match = re.search(r"POINT \(([^)]+)\)", wkt_string)
        if match:
            coords = match.group(1).strip().split()
            if len(coords) == 2:
                lat, lon = coords
                # Swap to (lon lat) format
                return f"POINT ({lon} {lat})"
        return wkt_string

    # Fix the WKT coordinate format and create geometry
    cleaned_listings["geometry"] = cleaned_listings["coordinates"].apply(
        lambda x: loads(fix_wkt_coordinates(x))
    )
    cleaned_listings_gdf = gpd.GeoDataFrame(
        cleaned_listings, geometry="geometry", crs="EPSG:4326"
    )

    logger.info(f"Loaded {len(cleaned_listings_gdf)} listing records")
    return cleaned_listings_gdf


def extract_coordinates_from_geometry(geometry) -> List[float]:
    """Extract [lon, lat] coordinates from shapely Point geometry"""
    return [geometry.x, geometry.y]


def extract_file_number(input_file_path: str) -> str:
    """Extract the number from input filename like missing_isochrones_X.csv"""
    import re

    filename = Path(input_file_path).name
    # Look for pattern like missing_isochrones_123.csv
    match = re.search(r"missing_isochrones_(\d+)\.csv", filename)
    if match:
        return match.group(1)
    else:
        # Fallback: try to extract any number from filename
        match = re.search(r"(\d+)", filename)
        if match:
            return match.group(1)
        else:
            return "unknown"


def fetch_single_isochrone(
    coordinates: List[float],
    api_key: str,
    profile: str = "driving",
    ranges: List[int] = [300, 600, 900],
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Fetch isochrone for a single location using OpenRouteService API with rate limit handling

    Args:
        coordinates: [lon, lat] format
        api_key: OpenRouteService API key
        ranges: List of range values in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary containing isochrone data or None if failed
    """
    logger = logging.getLogger(__name__)

    body = {"locations": [coordinates], "range": ranges}

    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        "Authorization": api_key,
        "Content-Type": "application/json; charset=utf-8",
    }

    # API endpoint based on profile
    if profile == "walking":
        url = "https://api.openrouteservice.org/v2/isochrones/foot-walking"
    else:  # driving
        url = "https://api.openrouteservice.org/v2/isochrones/driving-car"

    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Fetching isochrone for coordinates: {coordinates} (attempt {attempt + 1})"
            )

            response = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=30,
            )

            logger.debug(f"Response status: {response.status_code} {response.reason}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limit exceeded. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}"
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(
                    f"API request failed: {response.status_code} {response.reason}"
                )
                logger.error(f"Response text: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching isochrone (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return None

    return None


def fetch_batch_isochrones(
    coordinates_list: List[List[float]],
    api_key: str,
    profile: str = "driving",
    ranges: List[int] = [300, 600, 900],
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    Fetch isochrones for multiple locations using OpenRouteService API with rate limit handling

    Args:
        coordinates_list: List of [lon, lat] coordinate pairs
        api_key: OpenRouteService API key
        ranges: List of range values in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary containing isochrone data or None if failed
    """
    logger = logging.getLogger(__name__)

    body = {"locations": coordinates_list, "range": ranges}

    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        "Authorization": api_key,
        "Content-Type": "application/json; charset=utf-8",
    }

    # API endpoint based on profile
    if profile == "walking":
        url = "https://api.openrouteservice.org/v2/isochrones/foot-walking"
    else:  # driving
        url = "https://api.openrouteservice.org/v2/isochrones/driving-car"

    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Fetching isochrones for {len(coordinates_list)} locations (attempt {attempt + 1})"
            )

            response = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=60,
            )

            logger.debug(f"Response status: {response.status_code} {response.reason}")

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limit exceeded. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}"
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(
                    f"API request failed: {response.status_code} {response.reason}"
                )
                logger.error(f"Response text: {response.text}")
                return None

        except Exception as e:
            logger.error(
                f"Error fetching batch isochrones (attempt {attempt + 1}): {e}"
            )
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return None

    return None


def process_single_listing(
    listings_gdf: gpd.GeoDataFrame,
    api_key: str,
    output_dir: str,
    file_number: str,
    profile: str = "driving",
) -> Optional[Dict[str, Any]]:
    """Process a single listing to demonstrate the functionality"""
    logger = logging.getLogger(__name__)

    if len(listings_gdf) == 0:
        logger.error("No listings to process")
        return None

    # Take the first listing
    listing = listings_gdf.iloc[0]
    coordinates = extract_coordinates_from_geometry(listing.geometry)

    logger.info(f"Processing single listing with coordinates: {coordinates}")
    logger.info(f"Listing property_id: {listing.get('property_id', 'N/A')}")

    # Fetch isochrone
    isochrone_data = fetch_single_isochrone(coordinates, api_key, profile)

    if isochrone_data:
        logger.info("Successfully fetched isochrone data!")
        logger.info(f"Number of features: {len(isochrone_data.get('features', []))}")

        # Print some details about the isochrone
        for i, feature in enumerate(isochrone_data.get("features", [])):
            properties = feature.get("properties", {})
            logger.info(
                f"Feature {i+1}: range={properties.get('value', 'N/A')} seconds"
            )

        # Save the data
        output_path = Path(output_dir) / f"isochrone_{file_number}.csv"
        save_isochrone_data(isochrone_data, str(output_path), listings_gdf)

        return isochrone_data
    else:
        logger.error("Failed to fetch isochrone data")
        return None


def process_multiple_listings(
    listings_gdf: gpd.GeoDataFrame,
    api_key: str,
    max_records: int = None,
    output_dir: str = "data/processed/isochrones",
    file_number: str = "unknown",
    profile: str = "driving",
) -> None:
    """Process multiple listings in batches of 5 with error handling"""
    logger = logging.getLogger(__name__)

    if len(listings_gdf) == 0:
        logger.error("No listings to process")
        return

    # Limit to max_records if specified
    if max_records:
        listings_to_process = listings_gdf.head(max_records)
    else:
        listings_to_process = listings_gdf

    total_listings = len(listings_to_process)
    logger.info(f"Processing {total_listings} listings in batches of 5")

    # Process in batches of 5
    batch_size = 5
    total_requests = 0
    successful_batches = 0
    failed_batches = 0

    # Create a list to store all results (successful and failed)
    all_results = []

    for batch_start in range(0, total_listings, batch_size):
        batch_end = min(batch_start + batch_size, total_listings)
        batch_listings = listings_to_process.iloc[batch_start:batch_end]

        logger.info(
            f"Processing batch {batch_start//batch_size + 1}: listings {batch_start+1}-{batch_end}"
        )

        # Extract coordinates for this batch
        coordinates_list = [
            extract_coordinates_from_geometry(row.geometry)
            for _, row in batch_listings.iterrows()
        ]

        logger.info(
            f"Extracted coordinates for {len(coordinates_list)} listings in this batch"
        )
        for i, coords in enumerate(coordinates_list):
            logger.info(f"  Listing {batch_start + i + 1}: {coords}")

        # Fetch batch isochrones
        isochrone_data = fetch_batch_isochrones(coordinates_list, api_key, profile)
        total_requests += 1

        if isochrone_data and isochrone_data.get("features"):
            logger.info(
                f"Successfully fetched batch isochrone data! (Request #{total_requests})"
            )
            logger.info(
                f"Number of features: {len(isochrone_data.get('features', []))}"
            )

            # Store successful batch data
            all_results.append(
                {
                    "type": "success",
                    "isochrone_data": isochrone_data,
                    "listings_data": batch_listings,
                    "batch_start": batch_start,
                    "batch_end": batch_end,
                }
            )
            successful_batches += 1
        else:
            logger.error(
                f"Failed to fetch batch isochrone data for batch {batch_start//batch_size + 1}"
            )

            # Create null entries for failed batch
            all_results.append(
                {
                    "type": "failed",
                    "isochrone_data": None,
                    "listings_data": batch_listings,
                    "batch_start": batch_start,
                    "batch_end": batch_end,
                }
            )
            failed_batches += 1

        # Add a small delay between batches to help with rate limiting
        if (
            batch_start + batch_size < total_listings
        ):  # Don't delay after the last batch
            time.sleep(0.5)  # 500ms delay between batches

    # Consolidate all data (successful and failed)
    logger.info(
        f"Consolidating data from {successful_batches} successful batches and {failed_batches} failed batches"
    )

    # Combine all features from successful batches
    combined_features = []
    combined_listings = []

    for result in all_results:
        if result["type"] == "success":
            # Add successful isochrone features
            combined_features.extend(result["isochrone_data"].get("features", []))
            # Add corresponding listings
            combined_listings.append(result["listings_data"])
        else:
            # Add null features for failed batch
            batch_size_actual = result["batch_end"] - result["batch_start"]
            for i in range(batch_size_actual):
                # Create 3 null features per listing (5min, 10min, 15min)
                for range_minutes in [5, 10, 15]:
                    null_feature = {
                        "type": "Feature",
                        "properties": {"value": range_minutes * 60},
                        "geometry": {"type": "Polygon", "coordinates": [[]]},
                    }
                    combined_features.append(null_feature)
            # Add corresponding listings
            combined_listings.append(result["listings_data"])

    # Create combined isochrone data
    combined_isochrone_data = {
        "type": "FeatureCollection",
        "features": combined_features,
    }

    # Combine all listings data
    if combined_listings:
        final_combined_listings = pd.concat(combined_listings, ignore_index=True)
    else:
        final_combined_listings = listings_to_process

    # Save the consolidated data
    output_path = Path(output_dir) / f"isochrone_{file_number}.csv"
    save_isochrone_data(
        combined_isochrone_data, str(output_path), final_combined_listings
    )

    logger.info(f"Total API requests made: {total_requests}")
    logger.info(
        f"Successfully processed {len(combined_features)} isochrone features from {successful_batches} successful batches"
    )
    logger.info(f"Failed batches: {failed_batches}")
    logger.info(
        f"Output file will have {len(final_combined_listings)} rows (same as input)"
    )


def save_isochrone_data(
    isochrone_data: Dict[str, Any],
    output_path: str,
    listings_data: Optional[gpd.GeoDataFrame] = None,
) -> None:
    """Save isochrone data to CSV file with polygon columns"""
    logger = logging.getLogger(__name__)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract features and organize by range
    features = isochrone_data.get("features", [])

    # Group features by location index (for batch processing)
    # Each location gets 3 features (5min, 10min, 15min)
    locations_data = {}

    for i, feature in enumerate(features):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        range_value = properties.get("value", 0)
        # Calculate location index: every 3 features belong to one location
        location_index = i // 3

        # Convert range to minutes for column naming
        range_minutes = int(range_value / 60)

        # Extract coordinates and create polygon WKT
        coordinates = geometry.get("coordinates", [])
        if coordinates and len(coordinates) > 0 and len(coordinates[0]) > 0:
            # Convert GeoJSON coordinates to WKT POLYGON format
            # GeoJSON coordinates are [lon, lat] pairs
            coord_pairs = []
            for coord in coordinates[0]:  # First ring of polygon
                coord_pairs.append(f"{coord[0]} {coord[1]}")

            polygon_wkt = f"POLYGON (({', '.join(coord_pairs)}))"
        else:
            # Handle null/empty polygons
            polygon_wkt = ""

        # Initialize location data if not exists
        if location_index not in locations_data:
            locations_data[location_index] = {}

        locations_data[location_index][range_minutes] = polygon_wkt

    # Create DataFrame with polygon columns
    rows = []
    for location_index in sorted(locations_data.keys()):
        row_data = {}

        # Add polygon data
        for minutes in [5, 10, 15]:
            column_name = f"{minutes}min"
            row_data[column_name] = locations_data[location_index].get(minutes, "")

        # Add property and coordinate data if available
        if listings_data is not None and location_index < len(listings_data):
            listing = listings_data.iloc[location_index]
            row_data["property_id"] = listing.get("property_id", "")
            row_data["coordinates"] = listing.get("coordinates", "")

        rows.append(row_data)

    df = pd.DataFrame(rows)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Isochrone data saved to {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Fetch isochrones for property listings using OpenRouteService API (driving or walking)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single listing with driving profile (default)
  python fetch_isochrones_direct_driving.py --input-file data/raw/missing_isochrones/missing_isochrones_0.csv --max-records 1
  
  # Walking profile with specific API key
  python fetch_isochrones_direct_driving.py --input-file data/raw/missing_isochrones/missing_isochrones_0.csv --max-records 5 --profile walking --api-key APIKEY1
  
  # Driving profile with API key 2
  python fetch_isochrones_direct_driving.py --input-file data/raw/missing_isochrones/missing_isochrones_0.csv --profile driving --api-key APIKEY2
        """,
    )

    parser.add_argument(
        "--input-file", required=True, help="Path to input listings CSV file"
    )

    parser.add_argument(
        "--api-key",
        help="API key identifier (e.g., 'APIKEY1' for ORS_API_KEY1, 'APIKEY2' for ORS_API_KEY2, etc.)",
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum number of records to process (default: all records)",
    )

    parser.add_argument(
        "--profile",
        choices=["driving", "walking"],
        default="driving",
        help="Transportation profile: 'driving' or 'walking' (default: driving)",
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for isochrone data (default: data/processed/isochrones/{profile})",
    )

    parser.add_argument(
        "--ranges",
        nargs="+",
        type=int,
        default=[300, 600, 900],
        help="Range values in seconds for isochrones (default: 300 600 900)",
    )

    args = parser.parse_args()

    # Set output directory based on profile if not specified
    if not args.output_dir:
        args.output_dir = f"data/processed/isochrones/{args.profile}"

    # Set up logging
    logger = setup_logging()

    # Load environment variables
    load_environment()

    # Get API key
    api_key = None
    if args.api_key:
        # Extract number from APIKEYX format
        if args.api_key.startswith("APIKEY"):
            try:
                key_number = args.api_key[6:]  # Remove "APIKEY" prefix
                env_var_name = f"ORS_API_KEY{key_number}"
                api_key = os.getenv(env_var_name)
                if api_key:
                    logger.info(f"Using API key from {env_var_name}")
                else:
                    logger.error(
                        f"API key not found in environment variable {env_var_name}"
                    )
                    sys.exit(1)
            except Exception as e:
                logger.error(
                    f"Invalid API key format: {args.api_key}. Expected format: APIKEY1, APIKEY2, etc."
                )
                sys.exit(1)
        else:
            # Use the provided value directly
            api_key = args.api_key
            logger.info("Using provided API key")
    else:
        # Try default ORS_API_KEY
        api_key = os.getenv("ORS_API_KEY")
        if api_key:
            logger.info("Using default ORS_API_KEY")
        else:
            # Use the API key from the example for demonstration
            api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImQwOWQ4M2M3NTNjNzQ0NWM5MTZkMzk4Y2NhNmI1MTlhIiwiaCI6Im11cm11cjY0In0="
            logger.warning(
                "Using demonstration API key. For production, use --api-key APIKEY1 or set ORS_API_KEY environment variable"
            )

    logger.info(f"API key starts with: {api_key[:10]}...")

    try:
        # Load listings data
        listings_gdf = load_listings_data(args.input_file)

        # Extract file number from input filename
        file_number = extract_file_number(args.input_file)
        logger.info(f"Using file number: {file_number}")

        # Process based on number of records
        if len(listings_gdf) == 1:
            logger.info("Processing single listing...")
            process_single_listing(
                listings_gdf, api_key, args.output_dir, file_number, args.profile
            )
        else:
            logger.info(f"Processing {len(listings_gdf)} listings...")
            process_multiple_listings(
                listings_gdf,
                api_key,
                args.max_records,  # Pass max_records if specified, None otherwise
                args.output_dir,
                file_number,
                args.profile,
            )

        logger.info("Processing completed successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
