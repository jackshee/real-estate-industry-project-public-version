#!/usr/bin/env python3
"""
POI features fetching script for rental listings data using OpenStreetMap Overpass API.

This script fetches POI (Points of Interest) features for property listings using the
OpenStreetMap Overpass API. It can process single listings or batches of listings.

Usage:
    # Single listing example
    python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv --max-records 1

    # Multiple listings (5 records)
    python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv --max-records 5

    # All listings in file
    python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv
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
from shapely.geometry import Point
from geopy.distance import geodesic
from requests.exceptions import RequestException


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("poi_fetch.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


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


def extract_file_number(input_file_path: str) -> str:
    """Extract the number from input filename"""
    import re

    filename = Path(input_file_path).name
    # Look for pattern like missing_isochrones_123.csv or cleaned_listings_sampled.csv
    match = re.search(r"(\d+)", filename)
    if match:
        return match.group(1)
    else:
        # Use filename without extension as identifier
        return filename.replace(".csv", "")


def overpass_post(query, session=None, retries=5, pause=10):
    """Make a POST request to Overpass API with retry logic"""
    url = "https://overpass-api.de/api/interpreter"
    backoff = pause
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            resp = session.post(url, data={"data": query}, timeout=23)
            if resp.status_code in (429, 502, 504):
                retry_after = int(resp.headers.get("Retry-After", backoff))
                time.sleep(retry_after)
                backoff = min(backoff * 2, 60)
                continue
            resp.raise_for_status()
            return resp
        except RequestException as err:
            last_error = err
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
    raise RuntimeError(f"Overpass request failed after {retries} retries: {last_error}")


def collect_pois_for_listing(listing_row, tags, dist=2000, retries=5):
    """Collect POIs for a single listing"""
    logger = logging.getLogger(__name__)

    pid = listing_row["property_id"]
    lat1 = listing_row.geometry.y
    lon1 = listing_row.geometry.x

    logger.info(f"Processing property_id: {pid}")
    logger.info(f"Coordinates - Latitude: {lat1}, Longitude: {lon1}")

    rows = []

    with requests.Session() as session:
        session.headers.update(
            {"User-Agent": "project-poi-fetcher/1.0 tramaccidents@gmail.com"}
        )

        query = f"""
        [out:json][timeout:25];
        nwr["amenity"~"{tags}"](around:{dist},{lat1},{lon1});
        out center;
        """

        try:
            resp = overpass_post(query, session=session, retries=retries)

            for element in resp.json().get("elements", []):
                props = element.get("tags", {})
                lat = element.get("lat") or element["center"]["lat"]
                lon = element.get("lon") or element["center"]["lon"]
                rows.append(
                    {
                        "PropertyID": pid,
                        "name": props.get("name", "Unnamed"),
                        "amenity": props.get("amenity"),
                        "geometry": Point(lon, lat),
                        "distance_m": geodesic((lat1, lon1), (lat, lon)).meters,
                    }
                )

            logger.info(f"Found {len(rows)} POIs for property_id: {pid}")

        except RuntimeError as err:
            logger.error(f"Failed to fetch POIs for property_id {pid}: {err}")
            return None

    if not rows:
        cols = ["PropertyID", "name", "amenity", "geometry", "distance_m"]
        pois_gdf = gpd.GeoDataFrame(columns=cols, geometry="geometry", crs="EPSG:4326")
    else:
        pois_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")

    return pois_gdf


def process_single_listing(
    listings_gdf: gpd.GeoDataFrame,
    tags: str,
    dist: int,
    output_dir: str,
    file_number: str,
) -> Optional[Dict[str, Any]]:
    """Process a single listing to demonstrate the functionality"""
    logger = logging.getLogger(__name__)

    if len(listings_gdf) == 0:
        logger.error("No listings to process")
        return None

    # Take the first listing
    listing = listings_gdf.iloc[0]

    logger.info("Processing single listing...")
    logger.info(f"Listing property_id: {listing.get('property_id', 'N/A')}")

    # Collect POIs
    pois_gdf = collect_pois_for_listing(listing, tags, dist)

    if pois_gdf is not None and len(pois_gdf) > 0:
        logger.info(f"Successfully collected {len(pois_gdf)} POI features!")

        # Create property summary
        property_summary = create_property_summary(pois_gdf)

        # Save the data
        output_path = Path(output_dir) / f"poi_features_{file_number}.csv"
        save_poi_data(property_summary, str(output_path))

        return property_summary
    else:
        logger.error("Failed to collect POI data or no POIs found")
        return None


def process_multiple_listings(
    listings_gdf: gpd.GeoDataFrame,
    tags: str,
    dist: int,
    max_records: int = None,
    output_dir: str = "data/processed/poi_features",
    file_number: str = "unknown",
) -> None:
    """Process multiple listings with error handling"""
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
    logger.info(f"Processing {total_listings} listings")

    all_property_summaries = []
    successful_count = 0
    failed_count = 0

    for idx, (_, listing) in enumerate(listings_to_process.iterrows()):
        logger.info(f"Processing listing {idx + 1}/{total_listings}")

        try:
            # Collect POIs for this listing
            pois_gdf = collect_pois_for_listing(listing, tags, dist)

            if pois_gdf is not None and len(pois_gdf) > 0:
                # Create property summary
                property_summary = create_property_summary(pois_gdf)
                all_property_summaries.append(property_summary)
                successful_count += 1
                logger.info(f"Successfully processed listing {idx + 1}")
            else:
                # Create empty summary for failed listing
                empty_summary = pd.DataFrame({"PropertyID": [listing["property_id"]]})
                all_property_summaries.append(empty_summary)
                failed_count += 1
                logger.warning(f"No POIs found for listing {idx + 1}")

        except Exception as e:
            logger.error(f"Error processing listing {idx + 1}: {e}")
            # Create empty summary for failed listing
            empty_summary = pd.DataFrame({"PropertyID": [listing["property_id"]]})
            all_property_summaries.append(empty_summary)
            failed_count += 1

        # Add a small delay between requests to be respectful to the API
        if idx < total_listings - 1:  # Don't delay after the last listing
            time.sleep(0.5)  # 500ms delay between requests

    # Combine all property summaries
    if all_property_summaries:
        combined_summary = pd.concat(all_property_summaries, ignore_index=True)

        # Save the consolidated data
        output_path = Path(output_dir) / f"poi_features_{file_number}.csv"
        save_poi_data(combined_summary, str(output_path))

        logger.info(f"Successfully processed {successful_count} listings")
        logger.info(f"Failed listings: {failed_count}")
        logger.info(f"Output saved to {output_path}")
    else:
        logger.error("No property summaries to save")


def create_property_summary(pois_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """Create property summary with counts and distances for each amenity type"""
    if len(pois_gdf) == 0:
        return pd.DataFrame(columns=["PropertyID"])

    # Group by PropertyID and amenity, then aggregate
    agg = (
        pois_gdf.groupby(["PropertyID", "amenity"])
        .agg(count=("name", "count"), min_distance_m=("distance_m", "min"))
        .reset_index()
    )

    # Create wide format for counts
    count_wide = (
        agg.pivot(index="PropertyID", columns="amenity", values="count")
        .add_prefix("count_")
        .fillna(0)
    )

    # Create wide format for distances
    dist_wide = (
        agg.pivot(index="PropertyID", columns="amenity", values="min_distance_m")
        .add_prefix("min_dist_")
        .fillna(0)
    )

    # Combine count and distance features
    property_summary = count_wide.join(dist_wide).reset_index()

    return property_summary


def save_poi_data(property_summary: pd.DataFrame, output_path: str) -> None:
    """Save POI data to CSV file"""
    logger = logging.getLogger(__name__)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    property_summary.to_csv(output_path, index=False)
    logger.info(f"POI data saved to {output_path}")
    logger.info(
        f"Saved {len(property_summary)} property records with {len(property_summary.columns)} features"
    )


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Fetch POI features for property listings using OpenStreetMap Overpass API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single listing
  python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv --max-records 1
  
  # Multiple listings (5 records)
  python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv --max-records 5
  
  # All listings in file
  python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv
  
  # Custom distance and tags
  python fetch_osm_poi_features.py --input-file data/curated/rent_features/cleaned_listings_sampled.csv --max-records 3 --distance 1000 --tags "restaurant|cafe|bank"
        """,
    )

    parser.add_argument(
        "--input-file", required=True, help="Path to input listings CSV file"
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum number of records to process (default: all records)",
    )

    parser.add_argument(
        "--distance",
        type=int,
        default=2000,
        help="Search distance in metres around each property (default: 2000)",
    )

    parser.add_argument(
        "--tags",
        default="theatre|cafe|nightclub|kindergarten|doctors|fuel|bank|library|cinema|restaurant|atm|bar|fast_food|pharmacy|veterinary|taxi|brothel|university|police|events_venue|college|car_rental|clinic|community_centre|courier|food_court|social_facility|parking_space|hospital|waste_disposal|parcel_locker|charging_station|coworking_space|meeting_point|motorcycle_parking|childcare|social_centre|music_venue|healthcare|waste_transfer_station|casino|fire_station|student_accommodation|retail|prison|nursing_home|events_centre|exhibition_centre|conference_centre|biergarten|bus_station",
        help="Amenity tags to search for (default: comprehensive list of amenities)",
    )

    parser.add_argument(
        "--output-dir",
        default="data/processed/poi_features",
        help="Output directory for POI data (default: data/processed/poi_features)",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of retries for failed API requests (default: 5)",
    )

    args = parser.parse_args()

    # Set up logging
    logger = setup_logging()

    logger.info(f"Starting POI feature extraction")
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Distance: {args.distance}m")
    logger.info(f"Tags: {args.tags}")
    logger.info(f"Output directory: {args.output_dir}")

    try:
        # Load listings data
        listings_gdf = load_listings_data(args.input_file)

        # Extract file number from input filename
        file_number = extract_file_number(args.input_file)
        logger.info(f"Using file identifier: {file_number}")

        # Process based on number of records
        if args.max_records == 1 or len(listings_gdf) == 1:
            logger.info("Processing single listing...")
            process_single_listing(
                listings_gdf, args.tags, args.distance, args.output_dir, file_number
            )
        else:
            logger.info(
                f"Processing {args.max_records or len(listings_gdf)} listings..."
            )
            process_multiple_listings(
                listings_gdf,
                args.tags,
                args.distance,
                args.max_records,
                args.output_dir,
                file_number,
            )

        logger.info("Processing completed successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
