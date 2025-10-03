import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import os
from typing import List, Tuple, Optional, Union
import time
import geopandas as gpd
from shapely.geometry import Point
import warnings


class GeoDatasets:
    """
    A general utility class for geographical spatial data operations including:
    - Geocoding addresses to coordinates
    - Managing postcode and suburb data
    - Spatial data transformations
    - Geographic data scraping and processing
    """

    def __init__(
        self,
        base_url: str = "https://www.mosque-finder.com.au/vic/postcode.html",
        geocoding_delay: float = 1.0,
    ):
        """
        Initialize the GeoDatasets class.

        Args:
            base_url (str): URL to scrape Victorian postcodes and suburbs from
            geocoding_delay (float): Delay between geocoding requests in seconds
        """
        self.base_url = base_url
        self.geocoding_delay = geocoding_delay
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def get_suburbs_and_postcodes(self, output_dir: str = "data/geo") -> str:
        """
        Scrape Victorian suburbs and postcodes from the mosque-finder website and save to CSV.

        Args:
            output_dir (str): Directory to save the CSV file

        Returns:
            str: Path to the saved CSV file
        """
        print("Starting to scrape Victorian suburbs and postcodes...")

        try:
            # Make request to the website
            print(f"Fetching data from: {self.base_url}")
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all postcode-suburb pairs
            # The data is in the format: * postcode: XXXX - Suburb: SuburbName
            postcode_suburb_pairs = []

            # Look for list items containing postcode and suburb information
            list_items = soup.find_all("li")

            for item in list_items:
                text = item.get_text(strip=True)

                # Match pattern: postcode: XXXX - Suburb: SuburbName
                pattern = r"postcode:\s*(\d{4})\s*-\s*Suburb:\s*(.+)"
                match = re.search(pattern, text)

                if match:
                    postcode = match.group(1)
                    suburb = match.group(2)
                    postcode_suburb_pairs.append((postcode, suburb))

            if not postcode_suburb_pairs:
                print(
                    "No postcode-suburb pairs found. Checking alternative patterns..."
                )

                # Alternative approach: look for any text containing postcode patterns
                all_text = soup.get_text()
                lines = all_text.split("\n")

                for line in lines:
                    line = line.strip()
                    if "postcode:" in line and "Suburb:" in line:
                        pattern = r"postcode:\s*(\d{4})\s*-\s*Suburb:\s*(.+)"
                        match = re.search(pattern, line)
                        if match:
                            postcode = match.group(1)
                            suburb = match.group(2)
                            postcode_suburb_pairs.append((postcode, suburb))

            if not postcode_suburb_pairs:
                raise ValueError(
                    "Could not find any postcode-suburb pairs in the HTML content"
                )

            print(f"Found {len(postcode_suburb_pairs)} postcode-suburb pairs")

            # Create DataFrame
            df = pd.DataFrame(postcode_suburb_pairs, columns=["postcode", "suburb"])

            # Remove duplicates while preserving order
            df = df.drop_duplicates().reset_index(drop=True)

            print(f"After removing duplicates: {len(df)} unique postcode-suburb pairs")

            # Create output directory if it doesn't exist
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                if e.errno == 17:  # File exists error
                    pass  # Directory already exists, which is fine
                else:
                    raise

            # Save to CSV
            output_file = os.path.join(output_dir, "vic_suburbs_postcodes.csv")
            df.to_csv(output_file, index=False, encoding="utf-8")

            print(f"Successfully saved data to: {output_file}")
            print(f"Data preview:")
            print(df.head(10))
            print(f"\nTotal records: {len(df)}")

            return output_file

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            raise
        except Exception as e:
            print(f"Error processing data: {e}")
            raise

    def get_suburbs_by_postcode(self, postcode: str, csv_file: str = None) -> List[str]:
        """
        Get all suburbs for a given postcode from the CSV file.

        Args:
            postcode (str): Postcode to search for
            csv_file (str): Path to CSV file. If None, uses default location.

        Returns:
            List[str]: List of suburbs for the given postcode
        """
        if csv_file is None:
            csv_file = "data/geo/vic_suburbs_postcodes.csv"

        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        df = pd.read_csv(csv_file)
        # Convert postcode to string for comparison
        suburbs = df[df["postcode"].astype(str) == str(postcode)]["suburb"].tolist()
        return suburbs

    def get_postcodes_by_suburb(self, suburb: str, csv_file: str = None) -> List[str]:
        """
        Get all postcodes for a given suburb from the CSV file.

        Args:
            suburb (str): Suburb name to search for
            csv_file (str): Path to CSV file. If None, uses default location.

        Returns:
            List[str]: List of postcodes for the given suburb
        """
        if csv_file is None:
            csv_file = "data/geo/vic_suburbs_postcodes.csv"

        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        df = pd.read_csv(csv_file)
        # Case-insensitive search
        postcodes = df[df["suburb"].str.lower() == suburb.lower()]["postcode"].tolist()
        return postcodes

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
                return point
            else:
                print(f"No results found for address: {address}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error geocoding address '{address}': {e}")
            return None
        except (ValueError, KeyError) as e:
            print(f"Error parsing geocoding result for '{address}': {e}")
            return None

    def geocode_addresses_to_geodataframe(
        self, addresses: List[str], address_column: str = "address"
    ) -> gpd.GeoDataFrame:
        """
        Geocode a list of addresses and return a GeoDataFrame.

        Args:
            addresses (List[str]): List of addresses to geocode
            address_column (str): Name of the address column in the resulting GeoDataFrame

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with addresses and their corresponding Point geometries
        """

        results = []
        geometries = []

        print(f"Geocoding {len(addresses)} addresses...")
        print("=" * 50)

        for i, address in enumerate(addresses):
            if i % 10 == 0:
                print(f"Processing address {i+1}/{len(addresses)}: {address}")

            point = self.geocode_nominatim(address)

            results.append({address_column: address, "geocoded": point is not None})

            if point:
                geometries.append(point)
            else:
                geometries.append(None)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(results, geometry=geometries, crs="EPSG:4326")

        successful = gdf["geocoded"].sum()
        print(f"\nGeocoding completed!")
        print(
            f"Successful: {successful}/{len(addresses)} ({successful/len(addresses)*100:.1f}%)"
        )

        return gdf

    def geocode_dataframe(
        self,
        df: pd.DataFrame,
        address_column: str = "address",
        geometry_column: str = "geometry",
    ) -> gpd.GeoDataFrame:
        """
        Geocode addresses in a DataFrame and return a GeoDataFrame.

        Args:
            df (pd.DataFrame): DataFrame containing addresses
            address_column (str): Name of the column containing addresses
            geometry_column (str): Name of the geometry column to create

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with geocoded addresses
        """

        if address_column not in df.columns:
            raise ValueError(
                f"Address column '{address_column}' not found in DataFrame"
            )

        # Create a copy of the dataframe
        result_df = df.copy()

        # Initialize geometry column
        geometries = []

        print(f"Geocoding {len(df)} addresses from DataFrame...")
        print("=" * 50)

        for i, (idx, row) in enumerate(df.iterrows()):
            if i % 10 == 0:
                print(f"Processing row {i+1}/{len(df)}")

            address = row[address_column]
            point = self.geocode_nominatim(address)
            geometries.append(point)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(result_df, geometry=geometries, crs="EPSG:4326")

        successful = gdf.geometry.notna().sum()
        print(f"\nGeocoding completed!")
        print(f"Successful: {successful}/{len(df)} ({successful/len(df)*100:.1f}%)")

        return gdf

    def extract_address_from_url(self, url: str) -> Optional[str]:
        """
        Extract address from Domain.com.au URL format.

        Args:
            url (str): URL in format like '/4511-33-rose-lane-melbourne-vic-3000-16767655'

        Returns:
            Optional[str]: Full address string, or None if extraction fails
        """

        if pd.isna(url) or not isinstance(url, str):
            return None

        # Remove leading slash if present
        url = url.lstrip("/")

        # Split by dashes
        parts = url.split("-")

        if len(parts) < 4:
            return None

        # Extract property ID (last part)
        property_id = parts[-1]

        # Extract postcode (second to last part)
        postcode = parts[-2]

        # Extract state (third to last part)
        state = parts[-3]

        # Extract suburb (fourth to last part)
        suburb = parts[-4]

        # Everything before suburb is the street address
        street_parts = parts[:-4]

        # Check if first part is a unit number (starts with digit)
        unit_number = None
        if street_parts and street_parts[0].isdigit():
            unit_number = street_parts[0]
            street_address = "-".join(street_parts[1:]) if len(street_parts) > 1 else ""
        else:
            street_address = "-".join(street_parts)

        # Create full address
        if unit_number:
            full_address = f"{unit_number}/{street_address}, {suburb.title()}, {state.upper()} {postcode}"
        else:
            full_address = (
                f"{street_address}, {suburb.title()}, {state.upper()} {postcode}"
            )

        return full_address

    def add_address_column_from_urls(
        self, df: pd.DataFrame, url_column: str = "url", address_column: str = "address"
    ) -> pd.DataFrame:
        """
        Add an address column to a DataFrame by extracting addresses from URLs.

        Args:
            df (pd.DataFrame): DataFrame containing URLs
            url_column (str): Name of the column containing URLs
            address_column (str): Name of the address column to create

        Returns:
            pd.DataFrame: DataFrame with added address column
        """

        if url_column not in df.columns:
            raise ValueError(f"URL column '{url_column}' not found in DataFrame")

        result_df = df.copy()
        result_df[address_column] = result_df[url_column].apply(
            self.extract_address_from_url
        )

        successful = result_df[address_column].notna().sum()
        print(
            f"Successfully extracted {successful:,} addresses out of {len(df):,} records"
        )
        print(f"Address extraction success rate: {successful/len(df)*100:.1f}%")

        return result_df

    def create_geodataframe_from_urls(
        self, df: pd.DataFrame, url_column: str = "url", address_column: str = "address"
    ) -> gpd.GeoDataFrame:
        """
        Create a GeoDataFrame from a DataFrame with URLs by extracting addresses and geocoding them.

        Args:
            df (pd.DataFrame): DataFrame containing URLs
            url_column (str): Name of the column containing URLs
            address_column (str): Name of the address column to create

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with geocoded addresses
        """

        # First extract addresses from URLs
        df_with_addresses = self.add_address_column_from_urls(
            df, url_column, address_column
        )

        # Then geocode the addresses
        gdf = self.geocode_dataframe(df_with_addresses, address_column)

        return gdf


def main():
    """
    Main function to demonstrate usage of the GeoDatasets class.
    """
    # Create instance of GeoDatasets
    geo_data = GeoDatasets()

    # Scrape and save data
    try:
        csv_file = geo_data.get_suburbs_and_postcodes()
        print(f"\nData successfully saved to: {csv_file}")

        # Example usage of other methods
        print("\nExample queries:")

        # Get suburbs for postcode 3000 (Melbourne CBD)
        suburbs_3000 = geo_data.get_suburbs_by_postcode("3000")
        print(f"Suburbs in postcode 3000: {suburbs_3000}")

        # Get postcodes for Melbourne
        melbourne_postcodes = geo_data.get_postcodes_by_suburb("Melbourne")
        print(f"Postcodes for Melbourne: {melbourne_postcodes}")

        # Example geocoding functionality
        print("\nExample geocoding:")

        # Test single address geocoding
        test_address = "33 Rose Lane, Melbourne, VIC 3000, Australia"
        point = geo_data.geocode_nominatim(test_address)
        if point:
            print(f"Geocoded '{test_address}' to: Point({point.x}, {point.y})")
        else:
            print(f"Failed to geocode: {test_address}")

        # Test batch geocoding
        test_addresses = [
            "33 Rose Lane, Melbourne, VIC 3000, Australia",
            "10 Speke Street, Beaufort, VIC 3373, Australia",
            "36/390 Burwood Highway, Burwood, VIC 3125, Australia",
        ]

        print(f"\nBatch geocoding {len(test_addresses)} addresses...")
        gdf = geo_data.geocode_addresses_to_geodataframe(test_addresses)
        print(f"Created GeoDataFrame with shape: {gdf.shape}")
        print(f"CRS: {gdf.crs}")

        # Test URL address extraction
        print("\nExample URL address extraction:")
        test_urls = [
            "/4511-33-rose-lane-melbourne-vic-3000-16767655",
            "/10-speke-street-beaufort-vic-3373-16781407",
            "/36-390-burwood-highway-burwood-vic-3125-8592618",
        ]

        for url in test_urls:
            address = geo_data.extract_address_from_url(url)
            print(f"URL: {url}")
            print(f"Extracted address: {address}")
            print()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
