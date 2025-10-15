"""
Download utilities for data acquisition from various sources.

This module provides the DownloadUtils class for downloading and processing
data from government websites, APIs, and other data sources.
"""

import os
import zipfile
import re
import glob
import time
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np


class DownloadUtils:
    """
    Utility class for downloading data from various sources.

    This class provides methods for:
    - Creating data directory structures
    - Downloading files from URLs
    - Scraping time series data from web tables
    - Saving processed data to CSV files
    """

    def __init__(self, base_data_dir="../data/"):
        """
        Initialize the DownloadUtils class.

        Args:
            base_data_dir (str): Base directory for data storage
        """
        self.base_data_dir = base_data_dir
        self.create_data_folders()

    def create_data_folders(self):
        """
        Create folders for each stage of the ETL pipeline.

        Creates the following directory structure:
        - landing/
        - raw/
        - curated/
        - analysis/
        """
        # Check if data directory exists, if not create it
        if not os.path.exists(self.base_data_dir):
            os.makedirs(self.base_data_dir)

        # Create folders for each stage of the ETL pipeline
        for stage in ["landing", "raw", "curated", "analysis"]:
            stage_path = os.path.join(self.base_data_dir, stage)
            if not os.path.exists(stage_path):
                os.makedirs(stage_path)

    def download_file(self, url, output_path, file_type, verbose=False):
        """
        Download a file from a URL to a specified output path.

        Args:
            url (str): The URL of the file to download
            output_path (str): The local path where the file will be saved
            file_type (str): The file extension/type (e.g., 'csv', 'json', 'xlsx')
            verbose (bool): If True, show timing information and detailed output
        """
        # Generate output file path
        output_file_path = f"{output_path}.{file_type}"

        # Check if output file already exists
        if not os.path.exists(output_file_path):
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            if verbose:
                print(f"Downloading from: {url}")
                start_time = time.time()

            # Download the file from the URL and save it to the output file path
            urlretrieve(url, output_file_path)

            if verbose:
                end_time = time.time()
                download_time = end_time - start_time
                file_size = os.path.getsize(output_file_path) / (
                    1024 * 1024
                )  # Size in MB
                print(
                    f"✅ Downloaded {os.path.basename(output_file_path)} ({file_size:.2f} MB) in {download_time:.2f}s"
                )
            else:
                print(f"File downloaded and saved to {output_file_path}")
        else:
            if verbose:
                file_size = os.path.getsize(output_file_path) / (
                    1024 * 1024
                )  # Size in MB
                print(
                    f"⚠️  File already exists: {os.path.basename(output_file_path)} ({file_size:.2f} MB)"
                )
            else:
                print(f"File already exists at {output_file_path}")

    def scrape_time_series_data(
        self, url, data_name, value_columns=None, aggregate_method="mean", verbose=False
    ):
        """
        General function to scrape time series data from Victorian government tables
        and aggregate by quarter.

        Args:
            url (str): URL of the webpage containing the time series table
            data_name (str): Name for the dataset (used for output file naming)
            value_columns (list): List of column indices to extract (default: all columns after date)
            aggregate_method (str): Method for aggregation ('mean', 'last', 'first')
            verbose (bool): If True, show timing information and detailed output

        Returns:
            pd.DataFrame: DataFrame with quarterly aggregated data
        """
        try:
            if verbose:
                print(f"Scraping {data_name} data from: {url}")
                start_time = time.time()

            # Make request to the website
            response = requests.get(url)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the table containing data
            table = soup.find("table")
            if not table:
                raise ValueError("No table found on the webpage")

            # Extract header row to understand column structure
            header_row = table.find("tr")
            headers = [
                th.get_text(strip=True) for th in header_row.find_all(["th", "td"])
            ]

            # If no value_columns specified, use all columns after the first (date) column
            if value_columns is None:
                value_columns = list(range(1, len(headers)))

            # Extract table data
            rows = table.find_all("tr")[1:]  # Skip header row
            all_data = []

            for row in rows:
                cells = row.find_all("td")
                if len(cells) > 0:
                    date_str = cells[0].get_text(strip=True)

                    # Skip rows with missing date
                    if not date_str:
                        continue

                    row_data = {"date": date_str}

                    # Extract specified columns
                    for col_idx in value_columns:
                        if col_idx < len(cells):
                            value_str = cells[col_idx].get_text(strip=True)
                            col_name = (
                                headers[col_idx]
                                if col_idx < len(headers)
                                else f"value_{col_idx}"
                            )

                            # Handle missing values
                            if value_str and value_str.strip() != "":
                                try:
                                    row_data[col_name] = float(value_str)
                                except ValueError:
                                    # Skip rows with non-numeric values
                                    row_data = None
                                    break
                            else:
                                row_data[col_name] = None

                    if row_data is not None:
                        all_data.append(row_data)

            if not all_data:
                raise ValueError("No valid data found in the table")

            # Convert to DataFrame
            df = pd.DataFrame(all_data)

            # Convert date column to datetime
            df["date"] = pd.to_datetime(df["date"])

            # Create year and quarter columns
            df["year"] = df["date"].dt.year
            df["quarter"] = df["date"].dt.quarter

            # Group by year and quarter and aggregate
            agg_dict = {}
            for col in df.columns:
                if col not in ["date", "year", "quarter"]:
                    if aggregate_method == "mean":
                        agg_dict[col] = "mean"
                    elif aggregate_method == "last":
                        agg_dict[col] = "last"
                    elif aggregate_method == "first":
                        agg_dict[col] = "first"

            quarterly_data = df.groupby(["year", "quarter"]).agg(agg_dict).reset_index()

            # Create a proper date column for quarters
            quarterly_data["quarter_date"] = pd.to_datetime(
                quarterly_data["year"].astype(str)
                + "-"
                + (quarterly_data["quarter"] * 3).astype(str)
                + "-01"
            )

            # Sort by date
            quarterly_data = quarterly_data.sort_values("quarter_date")

            # Prepare final output
            final_columns = ["quarter_date", "year", "quarter"]
            for col in quarterly_data.columns:
                if col not in ["quarter_date", "year", "quarter"]:
                    final_columns.append(col)

            final_data = quarterly_data[final_columns].copy()
            final_data.rename(columns={"quarter_date": "date"}, inplace=True)

            if verbose:
                end_time = time.time()
                scrape_time = end_time - start_time
                print(
                    f"✅ Scraped {data_name} data ({len(final_data)} records) in {scrape_time:.2f}s"
                )

            return final_data

        except Exception as e:
            if verbose:
                end_time = time.time()
                scrape_time = end_time - start_time
                print(
                    f"❌ Error scraping {data_name} data after {scrape_time:.2f}s: {e}"
                )
            else:
                print(f"Error scraping {data_name} data: {e}")
            return None

    def save_time_series_data(self, data, data_name, output_dir):
        """
        Save time series data to CSV with appropriate naming.

        Args:
            data (pd.DataFrame): The data to save
            data_name (str): Name for the dataset
            output_dir (str): Output directory path

        Returns:
            str: Path to saved file or None if failed
        """
        if data is not None:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Save to CSV
            output_path = os.path.join(output_dir, f"quarterly_{data_name}.csv")
            data.to_csv(output_path, index=False)

            print(f"Successfully scraped and saved {data_name} data to {output_path}")
            print(f"Data contains {len(data)} quarterly records")
            print(f"Date range: {data['date'].min()} to {data['date'].max()}")
            print("\nFirst 5 records:")
            print(data.head())
            print("\nLast 5 records:")
            print(data.tail())
            print("\n" + "=" * 50 + "\n")

            return output_path
        else:
            print(f"Failed to scrape {data_name} data")
            return None

    def download_rent_data(self, verbose=False):
        """Download moving annual rent data from DFFH."""
        directory = os.path.join(
            self.base_data_dir, "landing", "rent", "rent_by_suburb"
        )
        url = "https://www.dffh.vic.gov.au/moving-annual-rents-suburb-march-quarter-2023-excel"
        self.download_file(url, directory, "xlsx", verbose=verbose)

    def download_latest_rent_data(self, verbose=False):
        """Download the latest moving annual rent file (March 2025)."""
        filename = "moving_annual_median_weekly_rent_by_suburb"
        directory = os.path.join(
            self.base_data_dir, "landing", "moving_annual_rent", filename
        )
        url = "https://www.dffh.vic.gov.au/moving-annual-rent-suburb-march-quarter-2025-excel"

        if verbose:
            print(f"Downloading latest moving annual rent file: {filename}")
            print(f"URL: {url}")

        try:
            self.download_file(url, directory, "xlsx", verbose=verbose)
            if verbose:
                print("✅ Successfully downloaded latest moving annual rent file!")
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")

    def download_public_transport_data(self, verbose=False):
        """Download public transport stops and lines data from VIC Gov."""
        # Download stops
        stops_directory = os.path.join(
            self.base_data_dir, "landing", "ptv", "public_transport_stops"
        )
        stops_url = "https://opendata.transport.vic.gov.au/dataset/6d36dfd9-8693-4552-8a03-05eb29a391fd/resource/afa7b823-0c8b-47a1-bc40-ada565f684c7/download/public_transport_stops.geojson"
        self.download_file(stops_url, stops_directory, "geojson", verbose=verbose)

        # Download lines
        lines_directory = os.path.join(
            self.base_data_dir, "landing", "ptv", "public_transport_lines"
        )
        lines_url = "https://opendata.transport.vic.gov.au/dataset/6d36dfd9-8693-4552-8a03-05eb29a391fd/resource/52e5173e-b5d5-4b65-9b98-89f225fc529c/download/public_transport_lines.geojson"
        self.download_file(lines_url, lines_directory, "geojson", verbose=verbose)

    def download_school_locations(self, verbose=False):
        """Download school locations data for 2023, 2024, and 2025."""
        urls = {
            2023: "https://www.education.vic.gov.au/Documents/about/research/datavic/dv346-schoollocations2023.csv",
            2024: "https://www.education.vic.gov.au/Documents/about/research/datavic/dv378_DataVic-SchoolLocations-2024.csv",
            2025: "https://www.education.vic.gov.au/Documents/about/research/datavic/dv402-SchoolLocations2025.csv",
        }

        for year, url in urls.items():
            directory = os.path.join(
                self.base_data_dir, "landing", "schools", f"school_locations_{year}"
            )
            self.download_file(url, directory, "csv", verbose=verbose)

    def scrape_unemployment_data(self, verbose=False):
        """Scrape unemployment rate data from Victorian labour market website."""
        if verbose:
            print("=== SCRAPING UNEMPLOYMENT RATE DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_labour_market"
        data = self.scrape_time_series_data(
            url=url,
            data_name="unemployment_rate",
            value_columns=[1],  # Only unemployment rate column
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "unemployment_rate")
        return self.save_time_series_data(data, "unemployment_rate", output_dir)

    def scrape_interest_rates_data(self, verbose=False):
        """Scrape interest rates data."""
        if verbose:
            print("=== SCRAPING INTEREST RATES DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_interest_rates"
        data = self.scrape_time_series_data(
            url=url,
            data_name="interest_rates",
            value_columns=[1, 2, 3],  # Mortgage rates, Savings rates, Cash rate
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "interest_rates")
        return self.save_time_series_data(data, "interest_rates", output_dir)

    def scrape_price_data(self, verbose=False):
        """Scrape price data."""
        if verbose:
            print("=== SCRAPING PRICE DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_prices"
        data = self.scrape_time_series_data(
            url=url,
            data_name="price_data",
            value_columns=[1, 2, 3],  # CPI (%/y), WPI (%/y), PPI, Final Demand (%/y)
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "price_data")
        return self.save_time_series_data(data, "price_data", output_dir)

    def scrape_economic_activity_data(self, verbose=False):
        """Scrape economic activity data."""
        if verbose:
            print("=== SCRAPING ECONOMIC ACTIVITY DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_economic_activity"
        data = self.scrape_time_series_data(
            url=url,
            data_name="economic_activity",
            value_columns=[2, 3],  # SFD (%/y), GSP quarterly components (%/y)
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "economic_activity")
        return self.save_time_series_data(data, "economic_activity", output_dir)

    def scrape_population_data(self, verbose=False):
        """Scrape population dynamics data."""
        if verbose:
            print("=== SCRAPING POPULATION DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_contribution_to_population_growth"
        data = self.scrape_time_series_data(
            url=url,
            data_name="population",
            value_columns=[
                1,
                2,
                3,
                4,
            ],  # Population (%/y), Natural increase (pp/y), Net overseas migration (pp/y), Net interstate migration (pp/y)
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "population")
        return self.save_time_series_data(data, "population_dynamics", output_dir)

    def scrape_investment_data(self, verbose=False):
        """Scrape investment data."""
        if verbose:
            print("=== SCRAPING INVESTMENT DATA ===")
        url = "https://djsir-data.github.io/djprecodash/tables/djsir_contribution_to_growth"
        data = self.scrape_time_series_data(
            url=url,
            data_name="investment",
            value_columns=[
                1,
                2,
                3,
                4,
                5,
            ],  # State final demand (%/y), Household consumption (pp/y), Dwelling investment (pp/y), Business investment (pp/y), Government spending (pp/y)
            aggregate_method="mean",
            verbose=verbose,
        )
        output_dir = os.path.join(self.base_data_dir, "landing", "investment")
        return self.save_time_series_data(data, "investment", output_dir)

    def download_all_data(self, verbose=False):
        """
        Download all available data sources.

        Args:
            verbose (bool): If True, show timing information and detailed output
        """
        if verbose:
            print("🚀 Starting comprehensive data download with verbose output...")
            overall_start_time = time.time()
        else:
            print("Starting comprehensive data download...")

        # Download static files
        if verbose:
            print("\n📁 --- Downloading Static Data Files ---")
            static_start_time = time.time()
        else:
            print("\n--- Downloading Static Data Files ---")

        self.download_rent_data(verbose=verbose)
        self.download_latest_rent_data(verbose=verbose)
        self.download_public_transport_data(verbose=verbose)
        self.download_school_locations(verbose=verbose)
        self.download_open_space_data(verbose=verbose)

        if verbose:
            static_end_time = time.time()
            static_time = static_end_time - static_start_time
            print(f"✅ Static files download completed in {static_time:.2f}s")

        # Scrape time series data
        if verbose:
            print("\n📊 --- Scraping Time Series Data ---")
            scrape_start_time = time.time()
        else:
            print("\n--- Scraping Time Series Data ---")

        self.scrape_unemployment_data(verbose=verbose)
        self.scrape_interest_rates_data(verbose=verbose)
        self.scrape_price_data(verbose=verbose)
        self.scrape_economic_activity_data(verbose=verbose)
        self.scrape_population_data(verbose=verbose)
        self.scrape_investment_data(verbose=verbose)

        if verbose:
            scrape_end_time = time.time()
            scrape_time = scrape_end_time - scrape_start_time
            print(f"✅ Time series data scraping completed in {scrape_time:.2f}s")

            overall_end_time = time.time()
            total_time = overall_end_time - overall_start_time
            print(f"\n🎉 All data download completed in {total_time:.2f}s")
        else:
            print("\nData download completed!")

    def download_population_census_data(
        self, sal_start=20001, sal_end=22944, verbose=False
    ):
        """
        Download 2021 census demographic data by suburb (SAL codes).

        Args:
            sal_start (int): Starting SAL code (default: 20001)
            sal_end (int): Ending SAL code (default: 22944)
            verbose (bool): If True, show timing information and detailed output
        """
        if verbose:
            print("=== DOWNLOADING POPULATION CENSUS DATA ===")
            start_time = time.time()

        # Create directory for population data
        population_dir = os.path.join(
            self.base_data_dir, "landing", "population_by_suburb"
        )
        os.makedirs(population_dir, exist_ok=True)

        # Store SAL codes for suburbs that do not have data available
        no_data = []
        downloaded_count = 0

        for i in range(sal_start, sal_end + 1):
            sal_code = f"SAL{i}"
            url_template = f"https://abs.gov.au/census/find-census-data/community-profiles/2021/{sal_code}/download/GCP_{sal_code}.xlsx"
            output_file_path = os.path.join(
                population_dir, f"{sal_code}_population.xlsx"
            )

            # Check if output file already exists
            if not os.path.exists(output_file_path):
                # Download postcode data with exception handling
                try:
                    urlretrieve(url_template, output_file_path)
                    downloaded_count += 1
                    if verbose and downloaded_count % 50 == 0:
                        print(f"✅ Downloaded {downloaded_count} files...")
                except Exception as e:
                    if verbose:
                        print(f"❌ Error for SAL {i}: {e}")
                    # Some suburbs have no data available
                    no_data.append(i)
            else:
                if verbose and i % 100 == 0:
                    print(f"File already exists: {sal_code}_population.xlsx")

        if verbose:
            end_time = time.time()
            download_time = end_time - start_time
            print(f"\n✅ Downloaded {downloaded_count} files in {download_time:.2f}s")
            print(f"❌ Failed downloads: {len(no_data)}")
        else:
            print(f"\nDownloaded {downloaded_count} files")
            print(f"Failed downloads: {len(no_data)}")

        return no_data

    def download_open_space_data(self, verbose=False):
        """Download open space data."""
        directory = os.path.join(
            self.base_data_dir, "landing", "open_space", "open_space"
        )
        url = "https://opendata.arcgis.com/datasets/da1c06e3ab6948fcb56de4bb3c722449_0.csv"
        self.download_file(url, directory, "csv", verbose=verbose)
