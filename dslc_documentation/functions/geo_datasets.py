import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from typing import List, Tuple
import time


class GeoDatasets:
    """
    A class to scrape and manage geographical datasets for Victorian suburbs and postcodes.
    """

    def __init__(
        self, base_url: str = "https://www.mosque-finder.com.au/vic/postcode.html"
    ):
        """
        Initialize the GeoDatasets class.

        Args:
            base_url (str): URL to scrape Victorian postcodes and suburbs from
        """
        self.base_url = base_url
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

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
