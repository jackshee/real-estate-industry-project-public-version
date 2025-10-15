"""
Data loading utilities for CSV files in the data directories.

This module provides the LoadUtils class for loading and managing CSV files
from various data directories in the project.
"""

import os
import glob
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging


class LoadUtils:
    """
    Utility class for loading CSV files from data directories.

    This class provides methods for:
    - Loading CSV files from specific data directories
    - Loading all CSV files from a directory
    - Loading files with specific patterns
    - Managing data loading with error handling
    """

    def __init__(self, base_data_dir: str = "data/"):
        """
        Initialize the LoadUtils class.

        Args:
            base_data_dir (str): Base directory for data storage
        """
        self.base_data_dir = Path(base_data_dir)
        self.logger = logging.getLogger(__name__)

    def load_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Load a single CSV file.

        Args:
            file_path (Union[str, Path]): Path to the CSV file
            **kwargs: Additional arguments to pass to pd.read_csv()

        Returns:
            pd.DataFrame: Loaded CSV data

        Raises:
            FileNotFoundError: If the file doesn't exist
            pd.errors.EmptyDataError: If the file is empty
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(file_path, **kwargs)
            self.logger.info(
                f"Successfully loaded CSV: {file_path} ({len(df)} rows, {len(df.columns)} columns)"
            )
            return df
        except Exception as e:
            self.logger.error(f"Error loading CSV {file_path}: {e}")
            raise

    def load_landing_economic_activity(self) -> pd.DataFrame:
        """Load economic activity data from landing directory."""
        file_path = (
            self.base_data_dir
            / "landing"
            / "economic_activity"
            / "quarterly_economic_activity.csv"
        )
        return self.load_csv(file_path)

    def load_landing_interest_rates(self) -> pd.DataFrame:
        """Load interest rates data from landing directory."""
        file_path = (
            self.base_data_dir
            / "landing"
            / "interest_rates"
            / "quarterly_interest_rates.csv"
        )
        return self.load_csv(file_path)

    def load_landing_investment(self) -> pd.DataFrame:
        """Load investment data from landing directory."""
        file_path = (
            self.base_data_dir / "landing" / "investment" / "quarterly_investment.csv"
        )
        return self.load_csv(file_path)

    def load_landing_population(self) -> pd.DataFrame:
        """Load population dynamics data from landing directory."""
        file_path = (
            self.base_data_dir
            / "landing"
            / "population"
            / "quarterly_population_dynamics.csv"
        )
        return self.load_csv(file_path)

    def load_landing_price_data(self) -> pd.DataFrame:
        """Load price data from landing directory."""
        file_path = (
            self.base_data_dir / "landing" / "price_data" / "quarterly_price_data.csv"
        )
        return self.load_csv(file_path)

    def load_landing_unemployment_rate(self) -> pd.DataFrame:
        """Load unemployment rate data from landing directory."""
        file_path = (
            self.base_data_dir
            / "landing"
            / "unemployment_rate"
            / "quarterly_unemployment_rate.csv"
        )
        return self.load_csv(file_path)

    def load_landing_schools(
        self, year: Optional[int] = None
    ) -> Union[pd.DataFrame, Dict[int, pd.DataFrame]]:
        """
        Load school locations data from landing directory.

        Args:
            year (Optional[int]): Specific year to load (2023, 2024, or 2025).
                                 If None, loads all available years.

        Returns:
            Union[pd.DataFrame, Dict[int, pd.DataFrame]]: Single DataFrame if year specified,
                                                         or dict of DataFrames by year
        """
        schools_dir = self.base_data_dir / "landing" / "schools"

        if year is not None:
            file_path = schools_dir / f"school_locations_{year}.csv"
            return self.load_csv(file_path)
        else:
            # Load all available years
            school_files = {}
            for year in [2023, 2024, 2025]:
                file_path = schools_dir / f"school_locations_{year}.csv"
                if file_path.exists():
                    school_files[year] = self.load_csv(file_path)
                else:
                    self.logger.warning(
                        f"School data for year {year} not found: {file_path}"
                    )
            return school_files

    def load_landing_ptv_stops(self) -> pd.DataFrame:
        """Load PTV stops data from landing directory (GeoJSON format)."""
        file_path = (
            self.base_data_dir / "landing" / "ptv" / "public_transport_stops.geojson"
        )
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            import geopandas as gpd

            gdf = gpd.read_file(file_path)
            self.logger.info(
                f"Successfully loaded PTV stops: {file_path} ({len(gdf)} rows)"
            )
            return gdf
        except ImportError:
            self.logger.error("geopandas is required to load GeoJSON files")
            raise
        except Exception as e:
            self.logger.error(f"Error loading PTV stops {file_path}: {e}")
            rais

    def load_landing_rent_data(self) -> pd.DataFrame:
        """
        Load moving annual rent data from landing directory.
        Note: This is an Excel file, not CSV.
        """
        file_path = (
            self.base_data_dir
            / "landing"
            / "moving_annual_rent"
            / "moving_annual_median_weekly_rent_by_suburb.xlsx"
        )
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = pd.read_excel(file_path)
            self.logger.info(
                f"Successfully loaded rent data: {file_path} ({len(df)} rows, {len(df.columns)} columns)"
            )
            return df
        except Exception as e:
            self.logger.error(f"Error loading rent data {file_path}: {e}")
            raise

    def load_all_landing_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load all available data from the landing directory.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary with descriptive keys and loaded DataFrames
        """
        data = {}

        # Load all CSV files
        try:
            data["economic_activity"] = self.load_landing_economic_activity()
        except Exception as e:
            self.logger.warning(f"Could not load economic activity data: {e}")

        try:
            data["interest_rates"] = self.load_landing_interest_rates()
        except Exception as e:
            self.logger.warning(f"Could not load interest rates data: {e}")

        try:
            data["investment"] = self.load_landing_investment()
        except Exception as e:
            self.logger.warning(f"Could not load investment data: {e}")

        try:
            data["population"] = self.load_landing_population()
        except Exception as e:
            self.logger.warning(f"Could not load population data: {e}")

        try:
            data["price_data"] = self.load_landing_price_data()
        except Exception as e:
            self.logger.warning(f"Could not load price data: {e}")

        try:
            data["unemployment_rate"] = self.load_landing_unemployment_rate()
        except Exception as e:
            self.logger.warning(f"Could not load unemployment rate data: {e}")

        try:
            data["schools"] = self.load_landing_schools()
        except Exception as e:
            self.logger.warning(f"Could not load schools data: {e}")

        try:
            data["ptv_stops"] = self.load_landing_ptv_stops()
        except Exception as e:
            self.logger.warning(f"Could not load PTV stops data: {e}")

        try:
            data["ptv_lines"] = self.load_landing_ptv_lines()
        except Exception as e:
            self.logger.warning(f"Could not load PTV lines data: {e}")

        try:
            data["rent_data"] = self.load_landing_rent_data()
        except Exception as e:
            self.logger.warning(f"Could not load rent data: {e}")

        self.logger.info(
            f"Successfully loaded {len(data)} datasets from landing directory"
        )
        return data

    def load_csvs_from_directory(
        self, directory: Union[str, Path], pattern: str = "*.csv", **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Load all CSV files from a directory.

        Args:
            directory (Union[str, Path]): Directory path
            pattern (str): File pattern to match (default: "*.csv")
            **kwargs: Additional arguments to pass to pd.read_csv()

        Returns:
            Dict[str, pd.DataFrame]: Dictionary with filenames as keys and DataFrames as values
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        csv_files = list(directory.glob(pattern))
        if not csv_files:
            self.logger.warning(
                f"No CSV files found in {directory} with pattern {pattern}"
            )
            return {}

        data = {}
        for file_path in csv_files:
            try:
                # Use filename without extension as key
                key = file_path.stem
                data[key] = self.load_csv(file_path, **kwargs)
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
                continue

        self.logger.info(f"Successfully loaded {len(data)} CSV files from {directory}")
        return data

    def get_available_files(
        self, directory: Union[str, Path], pattern: str = "*.csv"
    ) -> List[Path]:
        """
        Get list of available files in a directory matching a pattern.

        Args:
            directory (Union[str, Path]): Directory path
            pattern (str): File pattern to match

        Returns:
            List[Path]: List of matching file paths
        """
        directory = Path(directory)
        if not directory.exists():
            return []

        files = list(directory.glob(pattern))
        return sorted(files)

    def load_population_by_suburb(
        self, limit: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load population by suburb data (with optional limit for testing).

        Args:
            limit (Optional[int]): Limit number of files to load (for testing)

        Returns:
            Dict[str, pd.DataFrame]: Dictionary with filenames as keys and DataFrames as values
        """
        pop_dir = self.base_data_dir / "landing" / "population_by_suburb"

        if not pop_dir.exists():
            raise FileNotFoundError(f"Directory not found: {pop_dir}")

        csv_files = list(pop_dir.glob("*.csv"))
        if limit:
            csv_files = csv_files[:limit]

        if not csv_files:
            self.logger.warning(f"No CSV files found in {pop_dir}")
            return {}

        data = {}
        for file_path in csv_files:
            try:
                key = file_path.stem
                data[key] = self.load_csv(file_path)
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
                continue

        self.logger.info(
            f"Successfully loaded {len(data)} population files from {pop_dir}"
        )
        return data

    def merge_batches(
        self, input_dir: Union[str, Path], pattern: str = "*.csv", verbose: bool = True
    ) -> pd.DataFrame:
        """
        Merge multiple CSV files from a directory into a single DataFrame.

        Parameters:
        -----------
        input_dir : Union[str, Path]
            Directory containing the CSV files to merge
        pattern : str, optional
            Glob pattern to match files (default: "*.csv")
        verbose : bool, optional
            Print detailed progress information (default: True)

        Returns:
        --------
        pd.DataFrame
            The merged/concatenated dataframe
        """
        input_dir = Path(input_dir)

        if verbose:
            print(f"Starting merge process...")
            print(f"Input directory: {input_dir}")
            print(f"File pattern: {pattern}")
            print("-" * 60)

        # Get all matching CSV files
        file_pattern = str(input_dir / pattern)
        csv_files = glob.glob(file_pattern)
        csv_files.sort()  # Sort to ensure consistent order

        if not csv_files:
            raise ValueError(f"No files found matching pattern: {file_pattern}")

        if verbose:
            print(f"Found {len(csv_files)} files to merge:")
            for file in csv_files:
                print(f"  - {os.path.basename(file)}")
            print()

        # Read and concatenate all CSV files
        dataframes = []
        total_rows = 0

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                dataframes.append(df)
                total_rows += len(df)
                if verbose:
                    print(f"  Loaded: {os.path.basename(file_path)} ({len(df):,} rows)")
            except Exception as e:
                print(f"  ERROR loading {file_path}: {e}")
                continue

        if not dataframes:
            raise ValueError("No dataframes loaded successfully!")

        # Concatenate all dataframes
        if verbose:
            print(f"\nMerging {len(dataframes)} dataframes...")

        merged_df = pd.concat(dataframes, ignore_index=True)

        if verbose:
            print(f"{'=' * 60}")
            print(f"✓ Merge completed successfully!")
            print(f"✓ Total rows: {len(merged_df):,}")
            print(f"✓ Total columns: {len(merged_df.columns)}")
            print(f"✓ Column names: {list(merged_df.columns)}")
            print(f"{'=' * 60}")

        return merged_df

    def load_geocoded_coordinates(self) -> pd.DataFrame:
        """
        Load geocoded coordinates for wayback listings by merging batch files.

        Returns:
            pd.DataFrame: Geocoded coordinates with property_id, latitude, longitude, and coordinates
        """
        coordinates_dir = self.base_data_dir / "processed" / "coordinates"
        return self.merge_batches(coordinates_dir, pattern="batch_*.csv", verbose=True)
