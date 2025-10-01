import requests
import pandas as pd
import numpy as np
import re
import time
import random
import os
from pathlib import Path
import warnings
import geopandas as gpd
from shapely.geometry import Point
from typing import List, Optional, Union
from shapely.geometry import Polygon


# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print(
        "Warning: python-dotenv package not installed. Environment variables will not be loaded from .env file."
    )


class GeoUtils:
    """
    A utility class for geographical spatial data operations including:
    - Geocoding addresses to coordinates
    - Spatial data transformations
    - Geographic data processing
    """

    def __init__(self, geocoding_delay: float = 1.0, ors_api_key: Optional[str] = None):
        """
        Initialize the GeoUtils class.

        Args:
            geocoding_delay (float): Delay between geocoding requests in seconds
            ors_api_key (str, optional): OpenRouteService API key for geocoding.
                                        If None, will try to load from ORS_API_KEY environment variable.
        """
        self.geocoding_delay = geocoding_delay
        self.ors_api_key = ors_api_key or os.getenv("ORS_API_KEY1")
        self.ors_client = None

        # Initialize OpenRouteService client if API key is available
        if self.ors_api_key:
            try:
                import openrouteservice as ors

                self.ors_client = ors.Client(key=self.ors_api_key)
                print("OpenRouteService client initialized successfully.")
            except ImportError:
                print(
                    "Warning: openrouteservice package not installed. OpenRouteService geocoding will not be available."
                )
                self.ors_client = None
        else:
            print(
                "Warning: No OpenRouteService API key provided. Set ORS_API_KEY environment variable or pass ors_api_key parameter."
            )

    def geocode_nominatim(self, address: str) -> Optional[Point]:
        """
        Geocode address using Nominatim (OpenStreetMap) API.

        Args:
            address (str): Address to geocode

        Returns:
            Optional[Point]: Point geometry with longitude and latitude coordinates, or None if geocoding fails
        """

        if pd.isna(address) or not address:
            return None

        # Add Australia to improve geocoding accuracy
        if "australia" not in address.lower():
            address = f"{address}, Australia"

        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "au",  # Restrict to Australia
            "addressdetails": 1,
        }

        headers = {
            "User-Agent": "RentalAnalysis/1.0 (Educational Research)"  # Required by Nominatim
        }

        try:
            time.sleep(self.geocoding_delay)  # Respect rate limits
            response = requests.get(
                base_url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if data:
                result = data[0]
                # Create Point with longitude first, then latitude (x, y order)
                point = Point(float(result["lon"]), float(result["lat"]))
                print(f"Successfully geocoded address: {address}")
                return point
            else:
                # log status code and text
                print(f"No results found for address: {address}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error geocoding address '{address}': {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing geocoding result for '{address}': {e}")
            return None

    def geocode_ors(
        self, address: str, max_retries: int = 5, base_delay: float = 1.0
    ) -> Optional[Point]:
        """
        Geocode address using OpenRouteService API.
        Implements exponential backoff with jitter to handle rate limiting.
        Returns None immediately if quota is exceeded.

        Args:
            address (str): Address to geocode
            max_retries (int): Maximum number of retry attempts (default: 5)
            base_delay (float): Base delay in seconds for exponential backoff (default: 1.0)

        Returns:
            Optional[Point]: Point geometry with longitude and latitude coordinates, or None if geocoding fails
        """
        if not self.ors_client:
            print("OpenRouteService client not initialized. Please provide an API key.")
            return None

        if pd.isna(address) or not address:
            return None

        for attempt in range(max_retries + 1):
            try:
                geocode = self.ors_client.pelias_search(
                    text=address,
                    validate=False,
                )

                if geocode["features"]:
                    coords = geocode["features"][0]["geometry"]["coordinates"]
                    print(f"Successfully geocoded address: {address}")
                    return Point(coords[0], coords[1])
                else:
                    print(f"No results found for address: {address}")
                    return None

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
                    print(
                        f"Quota exceeded for OpenRouteService. Skipping address: {address}"
                    )
                    return None

                if attempt < max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    print(f"Attempt {attempt + 1} failed for {address}: {e}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    print(
                        f"Error getting coordinates for {address} after {max_retries + 1} attempts: {e}"
                    )
                    return None

        return None

    def geocode_ors_with_delay(self, address: str) -> Optional[Point]:
        """
        Wrapper function that adds a small delay between API calls for OpenRouteService geocoding.

        Args:
            address (str): Address to geocode

        Returns:
            Optional[Point]: Point geometry with coordinates, or None if geocoding fails
        """
        result = self.geocode_ors(address)
        # Add a small random delay (0.1-0.5 seconds) between calls
        time.sleep(random.uniform(0.1, 0.5))
        return result

    def extract_address_from_url(self, url: str) -> Optional[str]:
        """
        Extract and clean address from Domain.com.au URL format.

        This function handles both URL parsing and address cleaning to produce
        properly formatted addresses without needing further processing.

        Parameters:
        -----------
        url : str
            URL in format like '/4511-33-rose-lane-melbourne-vic-3000-16767655'

        Returns:
        --------
        Optional[str]
            Cleaned address string in format '33 Rose Lane, Melbourne, VIC 3000' or None if invalid
        """

        if pd.isna(url) or not isinstance(url, str):
            return None

        # Remove leading slash if present
        url = url.lstrip("/")

        # Split by dashes
        parts = url.split("-")

        if len(parts) < 4:
            return None

        # Extract postcode (second to last part)
        postcode = parts[-2]

        # Extract state (third to last part)
        state = parts[-3]

        # Extract suburb (fourth to last part)
        suburb = parts[-4]

        # Everything before suburb is the street address
        street_parts = parts[:-4]

        # Skip unit number (first part if it's a digit) and join remaining parts
        if street_parts and street_parts[0].isdigit():
            street_parts = street_parts[1:]

        # Join street parts and replace dashes with spaces
        street_address = " ".join(street_parts)

        # Clean the street address to remove unit numbers, apartment numbers, etc.
        cleaned_street = self.clean_street_address(street_address)

        # Create full address with cleaned street
        full_address = f"{cleaned_street}, {suburb.title()}, {state.upper()} {postcode}"

        return full_address

    def clean_street_address(self, street_address: str) -> str:
        """
        Clean street address to keep only the last street number and street name.

        Removes unit numbers, apartment numbers, and other prefixes while preserving:
        - Only the LAST street number (including alphanumeric like "12a")
        - Street names
        - Street types (St, Road, Avenue, etc.)

        Parameters:
        -----------
        street_address : str
            Raw street address (e.g., "unit 1 47 53 wyndham st")

        Returns:
        --------
        str
            Cleaned street address (e.g., "53 Wyndham St")
        """

        if not street_address or not isinstance(street_address, str):
            return street_address

        # Split into words
        words = street_address.split()

        if not words:
            return street_address

        # Common prefixes to remove (case insensitive)
        prefixes_to_remove = {
            "unit",
            "apt",
            "apartment",
            "suite",
            "level",
            "floor",
            "shop",
            "office",
            "rear",
            "front",
            "ground",
            "basement",
            "mezzanine",
            "penthouse",
            "villa",
            "townhouse",
            "house",
            "home",
            "property",
            "building",
        }

        # Remove prefixes from the beginning
        cleaned_words = []
        i = 0
        while i < len(words):
            word = words[i].lower()

            # Check if this word is a prefix to remove
            if word in prefixes_to_remove:
                # Skip this word and potentially the next one if it's a number
                i += 1
                # If the next word is a number, skip it too
                if i < len(words) and words[i].isdigit():
                    i += 1
            else:
                # This is not a prefix, start collecting words
                break

        # Collect the remaining words
        cleaned_words = words[i:]

        if not cleaned_words:
            return street_address  # Return original if everything was removed

        # Find the street number and street name
        # We want the last numeric/alphanumeric word as the street number
        # and everything after it as the street name

        street_number = None
        street_name_start = 0

        # Look for the last numeric/alphanumeric word in the cleaned words
        for i in range(len(cleaned_words) - 1, -1, -1):
            word = cleaned_words[i]
            # Check if this word contains a number (could be "53", "12a", "415a")
            if any(char.isdigit() for char in word):
                street_number = word
                street_name_start = i + 1
                break

        # If no street number found, return the cleaned words as is (title case)
        if street_number is None:
            return " ".join(word.title() for word in cleaned_words)

        # Extract street name (everything after the street number)
        street_name_words = cleaned_words[street_name_start:]

        if not street_name_words:
            # If no street name, just return the street number
            return street_number

        # Combine street number and street name
        street_name = " ".join(word.title() for word in street_name_words)
        return f"{street_number} {street_name}"

    def get_isochrone(
        self,
        coordinate,
        profile="driving-car",
        range_values=[300, 600, 900],
        validate=False,
        max_retries=5,
        base_delay=1.0,
    ):
        """
        Get isochrones for a single coordinate with multiple profiles and rate limiting.

        Args:
            coordinate (Point): Geometry Point object
            profiles (list): List of transportation profiles (default: ['driving-car', 'foot-walking'])
            range_values (list): List of time/distance values in seconds (default: [300, 600, 900])
            validate (bool): Whether to validate coordinates (default: False)
            attributes (list): List of attributes to request (default: None)
            max_retries (int): Maximum number of retry attempts
            base_delay (float): Base delay in seconds for exponential backoff

        Returns:
            dict: Dictionary with profile names as keys and isochrone results as values
        """

        print(
            f"Getting {profile} isochrone for coordinate: {coordinate.y, coordinate.x}"
        )

        for attempt in range(max_retries + 1):
            try:
                # Prepare the request parameters
                request_params = {
                    "locations": [
                        [coordinate.y, coordinate.x]
                    ],  # Single coordinate as required by API
                    "profile": profile,
                    "range": range_values,
                    "validate": validate,
                }

                # Make the isochrone request
                isochrone_result = self.ors_client.isochrones(**request_params)

                print(isochrone_result)

                # get the polygon for each range value
                results = []
                for feature in isochrone_result["features"]:
                    results.append(Polygon(feature["geometry"]["coordinates"][0]))

                print(f"Successfully generated {profile} isochrone")
                break

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
                    print(
                        f"Quota exceeded for OpenRouteService. Skipping {profile} isochrone request."
                    )
                    results = None
                    break

                if attempt < max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    print(f"Attempt {attempt + 1} failed for {profile} isochrone: {e}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    print(
                        f"Error getting {profile} isochrone after {max_retries + 1} attempts: {e}"
                    )
                    results = None

        print(f"Results: {results}")

        return results

    def get_isochrone_with_delay(
        self,
        coordinate,
        profile="driving-car",
        range_values=[300, 600, 900],
        validate=False,
    ):
        """
        Wrapper function that adds a small delay between API calls for isochrone requests.

        Args:
            coordinate (list or tuple): Single coordinate as [lon, lat] or (lon, lat)
            profiles (list): List of transportation profiles
            range_values (list): List of time/distance values in seconds
            validate (bool): Whether to validate coordinates
            attributes (list): List of attributes to request

        Returns:
            dict: Dictionary with profile names as keys and isochrone results as values
        """
        result = self.get_isochrone(
            coordinate=coordinate,
            profile=profile,
            range_values=range_values,
            validate=validate,
        )
        # Add a small random delay (0.1-0.5 seconds) between calls
        time.sleep(random.uniform(0.1, 0.5))
        return result
