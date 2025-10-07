#!/usr/bin/env python3
"""
Fixed version of fetch_routes.py using openrouteservice Python client
"""

import argparse
import os
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import geopandas as gpd
import openrouteservice as ors
from sklearn.neighbors import BallTree
from shapely.wkt import loads
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


def load_poi_data(poi_file_path, coordinate_column="coordinates"):
    """Load POI data from either GeoJSON or CSV file"""
    poi_path = Path(poi_file_path)

    if not poi_path.exists():
        raise FileNotFoundError(f"POI file not found: {poi_file_path}")

    logger.info(f"Loading POI data from {poi_file_path}")

    if poi_path.suffix.lower() == ".geojson":
        poi_gdf = gpd.read_file(poi_file_path)
        poi_gdf = poi_gdf.to_crs(epsg=4326)
        logger.info(f"Loaded {len(poi_gdf)} POI records from GeoJSON")

    elif poi_path.suffix.lower() == ".csv":
        poi_df = pd.read_csv(poi_file_path)

        if coordinate_column not in poi_df.columns:
            raise ValueError(
                f"Coordinate column '{coordinate_column}' not found in CSV file"
            )

        poi_df["geometry"] = poi_df[coordinate_column].apply(loads)
        poi_gdf = gpd.GeoDataFrame(poi_df, geometry="geometry", crs="EPSG:4326")
        logger.info(f"Loaded {len(poi_gdf)} POI records from CSV")

    else:
        raise ValueError(f"Unsupported file format: {poi_path.suffix}")

    return poi_gdf


def load_listings_data(listings_file_path):
    """Load property listings data"""
    listings_path = Path(listings_file_path)

    if not listings_path.exists():
        raise FileNotFoundError(f"Listings file not found: {listings_file_path}")

    logger.info(f"Loading listings data from {listings_file_path}")

    cleaned_listings = pd.read_csv(listings_file_path, low_memory=False)

    def fix_wkt_coordinates(wkt_string):
        """Fix WKT coordinates from (lat lon) to (lon lat) format"""
        # Extract coordinates from POINT (lat lon) format
        import re

        match = re.search(r"POINT \(([^)]+)\)", wkt_string)
        if match:
            coords = match.group(1).strip().split()
            if len(coords) == 2:
                lat, lon = coords
                # Swap to (lon lat) format
                return f"POINT ({lon} {lat})"
        return wkt_string

    # Fix the WKT coordinate format
    cleaned_listings["geometry"] = cleaned_listings["coordinates"].apply(
        lambda x: loads(fix_wkt_coordinates(x))
    )
    cleaned_listings_gdf = gpd.GeoDataFrame(
        cleaned_listings, geometry="geometry", crs="EPSG:4326"
    )

    logger.info(f"Loaded {len(cleaned_listings_gdf)} listing records")
    return cleaned_listings_gdf


def create_ball_tree(poi_gdf):
    """Create BallTree for efficient nearest neighbor search"""
    # Use [lat, lon] format for BallTree (y, x coordinates)
    poi_rad = np.radians(np.c_[poi_gdf.geometry.y, poi_gdf.geometry.x])
    tree = BallTree(poi_rad, metric="haversine")
    logger.info(f"Created BallTree with {len(poi_gdf)} POI points")
    return tree


def shortlist_pois(point, tree, poi_gdf, k=6, max_km=2.0):
    """Find POIs within specified distance of a point"""
    # Use [lat, lon] format (y, x coordinates)
    pt = np.radians([[point.y, point.x]])
    dist, idx = tree.query(pt, k=k)
    dist_km = dist[0] * 6371.0088
    mask = dist_km <= max_km

    logger.debug(
        f"Found {mask.sum()} POIs within {max_km}km of point lat={point.y:.4f}, lon={point.x:.4f}"
    )
    return poi_gdf.iloc[idx[0][mask]]


def calculate_routes_ors(source, targets, client):
    """Calculate routing distances using openrouteservice Python client"""
    try:
        # Prepare coordinates: [lon, lat] format for ORS
        coordinates = [[source.x, source.y]] + [[pt.x, pt.y] for pt in targets]

        logger.debug(f"Calculating routes from {len(coordinates)} points")

        matrix = client.distance_matrix(
            locations=coordinates,
            profile="driving-car",
            metrics=["distance", "duration"],
            validate=False,
        )

        distances = matrix["distances"][0][1:]  # Skip first (source to itself)
        durations = matrix["durations"][0][1:]  # Skip first (source to itself)

        logger.debug(f"Got {len(distances)} distances and {len(durations)} durations")
        return distances, durations

    except Exception as e:
        logger.error(f"ORS API error: {e}")
        raise


def process_listings(listings_gdf, poi_gdf, tree, client, max_km=3.0, k=10):
    """Process listings to find nearest POI and calculate routing distances"""
    logger.info(f"Processing {len(listings_gdf)} listings...")

    # Initialize new columns
    listings_gdf["StationID"] = None
    listings_gdf["min_route_dist_m"] = None
    listings_gdf["min_route_dur_s"] = None

    rows_processed = 0
    rows_with_poi = 0

    # Debug first listing to verify coordinate handling
    first_row = listings_gdf.iloc[0]
    logger.info(
        f"First listing coordinates: lat={first_row.geometry.y:.4f}, lon={first_row.geometry.x:.4f}"
    )

    # Check bounds
    poi_bounds = poi_gdf.total_bounds
    logger.info(
        f"POI bounds: lat [{poi_bounds[1]:.4f}, {poi_bounds[3]:.4f}], lon [{poi_bounds[0]:.4f}, {poi_bounds[2]:.4f}]"
    )

    for idx, row in listings_gdf.iterrows():
        try:
            # Find nearby POIs
            candidates = shortlist_pois(row.geometry, tree, poi_gdf, k=k, max_km=max_km)

            if candidates.empty:
                logger.debug(f"No POIs found within {max_km}km for listing {idx}")
                continue

            rows_with_poi += 1
            logger.info(f"Found {len(candidates)} POI candidates for listing {idx}")

            # Calculate routing distances using ORS client
            distances, durations = calculate_routes_ors(
                row.geometry, candidates.geometry, client
            )

            # Find the closest POI by duration
            best_idx = int(np.argmin(durations))
            chosen = candidates.iloc[best_idx]

            # Update the listing with routing data
            listings_gdf.loc[idx, "StationID"] = chosen.get(
                "STOP_ID", chosen.get("id", best_idx)
            )
            listings_gdf.loc[idx, "min_route_dist_m"] = distances[best_idx]
            listings_gdf.loc[idx, "min_route_dur_s"] = durations[best_idx]

            rows_processed += 1
            logger.info(
                f"Successfully processed listing {idx}: StationID={chosen.get('STOP_ID', best_idx)}, distance={distances[best_idx]}m, duration={durations[best_idx]}s"
            )

            if rows_processed % 10 == 0:
                logger.info(
                    f"Processed {rows_processed}/{len(listings_gdf)} listings..."
                )

        except Exception as e:
            logger.error(f"Error processing listing {idx}: {e}")
            continue

    logger.info(
        f"Successfully processed {rows_processed} listings with {rows_with_poi} having nearby POIs"
    )
    return listings_gdf


def save_results(listings_gdf, output_path):
    """Save results to CSV file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving results to {output_path}")

    # Convert geometry back to WKT string for CSV compatibility
    output_df = listings_gdf.copy()
    output_df["coordinates"] = output_df["geometry"].apply(lambda x: x.wkt)
    output_df = output_df.drop(columns=["geometry"])

    output_df.to_csv(output_path, index=False)
    logger.info(f"Results saved successfully")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Fixed version: Fetch routing distances from property listings to POI locations using OpenRouteService Python client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using GeoJSON POI file
  python fetch_routes_fixed.py --input-listings-file data/raw/missing_routes/missing_routes_0.csv \\
                              --input-poi-file data/landing/ptv/public_transport_stops.geojson

  # Using CSV POI file
  python fetch_routes_fixed.py --input-listings-file data/raw/missing_routes/missing_routes_0.csv \\
                              --input-poi-file data/landing/ptv/stops.csv \\
                              --coordinate-column coordinates
        """,
    )

    parser.add_argument(
        "--input-listings-file", required=True, help="Path to input listings CSV file"
    )

    parser.add_argument(
        "--input-poi-file", required=True, help="Path to POI file (GeoJSON or CSV)"
    )

    parser.add_argument(
        "--coordinate-column",
        default="coordinates",
        help="Column name containing coordinates in CSV POI file (default: coordinates)",
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouteService API key environment variable name (e.g., ORS_API_KEY1) or direct API key",
    )

    parser.add_argument(
        "--output-dir",
        default="../data/processed/routes/ptv",
        help="Output directory for results (default: ../data/processed/routes/ptv)",
    )

    parser.add_argument(
        "--max-km",
        type=float,
        default=3.0,
        help="Maximum search radius in kilometers (default: 3.0)",
    )

    parser.add_argument(
        "--k-nearest",
        type=int,
        default=10,
        help="Maximum number of nearest POIs to consider (default: 10)",
    )

    args = parser.parse_args()

    # Load environment variables
    load_environment()

    # Get API key - either from environment variable name or direct key
    if args.api_key:
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
    else:
        # Fallback to default environment variable
        api_key = os.getenv("ORS_API_KEY")
        if not api_key:
            logger.error(
                "API key not provided. Use --api-key argument with environment variable name (e.g., ORS_API_KEY1) or direct API key"
            )
            sys.exit(1)
        logger.info("Using API key from default ORS_API_KEY environment variable")
    
    logger.info(f"API key starts with: {api_key[:10]}...")

    try:
        # Initialize ORS client
        client = ors.Client(key=api_key)
        logger.info("Initialized OpenRouteService client")

        # Load data
        poi_gdf = load_poi_data(args.input_poi_file, args.coordinate_column)
        listings_gdf = load_listings_data(args.input_listings_file)

        # Create BallTree for efficient nearest neighbor search
        tree = create_ball_tree(poi_gdf)

        # Process listings
        processed_listings = process_listings(
            listings_gdf, poi_gdf, tree, client, max_km=args.max_km, k=args.k_nearest
        )

        # Generate output filename
        input_filename = Path(args.input_listings_file).stem
        output_filename = f"{input_filename}_with_routes.csv"
        output_path = Path(args.output_dir) / output_filename

        # Save results
        save_results(processed_listings, output_path)

        logger.info("Processing completed successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
