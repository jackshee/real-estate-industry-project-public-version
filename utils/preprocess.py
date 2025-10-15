import pandas as pd
import pickle
import os
import numpy as np
import glob
import re
from pathlib import Path
from shapely.geometry import Point


class PreprocessUtils:
    """
    A utility class for preprocessing operations on data.
    """

    def __init__(self, mapping_path="../data/processed/mapping.pkl"):
        """
        Initialize the PreprocessUtils class.

        Parameters:
        -----------
        mapping_path : str
            Path to the suburb mapping pickle file
        """
        self.mapping_path = mapping_path
        self.suburb_mapping = None
        self.inverted_suburb_mapping = None

    def _load_suburb_mapping(self):
        """
        Load the suburb mapping from pickle file if not already loaded.
        """
        if self.suburb_mapping is None:
            self.suburb_mapping = pickle.load(open(self.mapping_path, "rb"))
            self._create_inverted_mapping()

    def _create_inverted_mapping(self):
        """
        Create inverted dictionary for reverse mapping (value -> key).
        Handle case where values might be lists.
        """
        self.inverted_suburb_mapping = {}
        for key, value in self.suburb_mapping.items():
            if isinstance(value, list):
                # If value is a list, map each item in the list to the key
                for item in value:
                    self.inverted_suburb_mapping[item] = key
            else:
                # If value is a single item, map it directly
                self.inverted_suburb_mapping[value] = key

    def map_suburb(self, suburb_series):
        """
        Map suburbs to their standardized names using the suburb mapping.

        Parameters:
        -----------
        suburb_series : pd.Series
            A pandas Series containing suburb names

        Returns:
        --------
        pd.Series
            A pandas Series with mapped suburb names
        """
        # Load the mapping if not already loaded
        self._load_suburb_mapping()

        # Create a copy to avoid modifying the original
        suburb_series_copy = suburb_series.copy()

        # Ensure lowercasing
        suburb_series_copy = suburb_series_copy.str.lower()

        # Create mapped_suburb column using the inverted dictionary
        mapped_suburb = suburb_series_copy.map(self.inverted_suburb_mapping)

        # Fill NaN values (unmapped suburbs) with the original lowercased suburb
        mapped_suburb = mapped_suburb.fillna(suburb_series_copy)

        return mapped_suburb

    def map_property_type(self, property_type_series):
        """
        Map property types to standardized categories (house, flat, or unknown).

        Parameters:
        -----------
        property_type_series : pd.Series
            A pandas Series containing property type values

        Returns:
        --------
        pd.Series
            A pandas Series with mapped property type categories
        """
        # Create a copy to avoid modifying the original
        property_type_copy = property_type_series.copy()

        # Convert to lower casing
        property_type_copy = property_type_copy.str.lower()

        # Create a mapping dictionary
        property_type_mapping = {
            "house": [
                "house",
                "new house land",
                "townhouse",
                "villa",
                "semi-detached",
                "terrace",
                "duplex",
            ],
            "flat": [
                "apartment unit flat",
                "studio",
                "new apartments off the plan",
                "penthouse",
            ],
        }

        # Create inverted mapping (property type -> category)
        inverted_property_type_mapping = {}
        for category, property_types in property_type_mapping.items():
            for prop_type in property_types:
                inverted_property_type_mapping[prop_type] = category

        # Map property types to categories
        house_flat_other = property_type_copy.map(inverted_property_type_mapping)

        # Fill NaN values with "unknown"
        house_flat_other = house_flat_other.fillna("unknown")

        return house_flat_other

    def extract_rental_price(self, rental_price_series):
        """
        Extract weekly rent from rental price strings.

        Parameters:
        -----------
        rental_price_series : pd.Series
            A pandas Series containing rental price strings

        Returns:
        --------
        pd.Series
            A pandas Series with weekly rent values (NaN for unknown frequencies)
        """
        # Create a copy to avoid modifying the original
        rental_price_copy = rental_price_series.copy()

        # Remove '$' and ',' from rental_price
        rental_price_copy = rental_price_copy.replace("[\$,]", "", regex=True).astype(
            str
        )

        # Convert to lowercase
        rental_price_copy = rental_price_copy.str.lower()

        # Remove spaces in rental_price
        rental_price_copy = rental_price_copy.str.replace(" ", "", regex=False)

        # Extract numeric value from rental_price (based on the first number found)
        price_value = rental_price_copy.str.extract(r"(\d+(?:\.\d+)?)")[0].astype(float)

        freq_keywords = [
            "pw",
            "perweek",
            "weekly",
            "p/w",
            "wk",
            "p.w.",
            "/wk",
            "/w",
            "/week",
            "p.w",
            "permonth",
            "pm",
            "calendar",
            "monthly",
            "calender",
            "percalendarmonth",
            "percalendermonth",
        ]

        # Extract frequency keyword after the number
        price_frequency = rental_price_copy.str.extract(
            r"(\d+(?:\.\d+)?)+(" + "|".join(freq_keywords) + ")", expand=False
        )[1]

        # Map known patterns to standardized categories
        frequency_mapping = {
            "pw": "weekly",
            "p.w.": "weekly",
            "perweek": "weekly",
            "weekly": "weekly",
            "p/w": "weekly",
            "wk": "weekly",
            "p.w": "weekly",
            "/wk": "weekly",
            "/w": "weekly",
            "/week": "weekly",
            "pm": "monthly",
            "permonth": "monthly",
            "calendar": "monthly",
            "calender": "monthly",
            "monthly": "monthly",
            "percalendarmonth": "monthly",
            "percalendermonth": "monthly",
        }

        price_frequency = price_frequency.map(frequency_mapping)

        # If price is purely numeric (digits and full stops), assume weekly
        numeric_mask = rental_price_copy.str.match(r"^[\d\.]+$")
        price_frequency.loc[numeric_mask & price_frequency.isna()] = "weekly"

        # Assign 'unknown' to unmatched entries
        price_frequency = price_frequency.fillna("unknown")

        # Convert to categorical type
        price_frequency = pd.Categorical(
            price_frequency, categories=["weekly", "monthly", "unknown"]
        )

        # Create weekly_rent based on price_frequency
        weekly_rent = pd.Series(index=rental_price_series.index, dtype=float)

        # Calculate weekly rent
        weekly_mask = price_frequency == "weekly"
        monthly_mask = price_frequency == "monthly"
        unknown_mask = price_frequency == "unknown"

        weekly_rent.loc[weekly_mask] = price_value.loc[weekly_mask]
        weekly_rent.loc[monthly_mask] = price_value.loc[monthly_mask] / 4
        weekly_rent.loc[unknown_mask] = None

        return weekly_rent

    def impute_by_property_type_mode(
        self, df, column_name, property_type_column="property_type"
    ):
        """
        Impute missing values in a column by using the mode for each property_type.

        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame containing the data
        column_name : str
            Name of the column to impute (e.g., 'bedrooms')
        property_type_column : str, optional
            Name of the property type column (default: 'property_type')

        Returns:
        --------
        pd.Series
            Series with imputed values
        """
        # Calculate mode for each property_type
        mode_by_type = df.groupby(property_type_column)[column_name].agg(
            lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        )

        # Get overall mode as fallback
        overall_mode = (
            df[column_name].mode()[0] if len(df[column_name].mode()) > 0 else None
        )

        # Create a copy of the column to avoid SettingWithCopyWarning
        result = df[column_name].copy()

        # Fill missing values based on property_type
        for prop_type in df[property_type_column].unique():
            mask = (df[property_type_column] == prop_type) & (df[column_name].isna())
            fill_value = mode_by_type.get(prop_type, overall_mode)
            if mask.sum() > 0:
                print(
                    f"Property type: {prop_type}, {column_name} imputed with {fill_value}"
                )
            if fill_value is not None:
                result.loc[mask] = fill_value

        return result

    def split_into_batches(self, df, batch_size, output_dir):
        """
        Split a DataFrame into smaller CSV files with specified batch size.

        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame to split into batches
        batch_size : int
            Number of rows per batch file
        output_dir : str
            Directory path where batch files will be saved

        Returns:
        --------
        list
            List of file paths for the saved batch files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Calculate number of batches needed
        num_batches = (len(df) + batch_size - 1) // batch_size

        # List to store file paths
        batch_files = []

        # Split and save batches
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]

            # Create filename with batch number
            filename = f"batch_{i+1:04d}.csv"
            filepath = os.path.join(output_dir, filename)

            # Save batch to CSV
            batch_df.to_csv(filepath, index=False)
            batch_files.append(filepath)

            print(f"Saved {filename}: {len(batch_df)} rows")

        print(f"\nTotal batches created: {num_batches}")
        print(f"Output directory: {output_dir}")

        return batch_files

    def impute_by_nearest_point(
        self, df, column_names, coordinates_column="coordinates", suburb_column="suburb"
    ):
        """
        Impute missing values in one or more columns by finding the nearest non-null point within the same suburb.

        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame containing the data
        column_names : str or list of str
            Name(s) of the column(s) to impute (e.g., 'driving_5min' or ['driving_5min', 'walking_5min'])
        coordinates_column : str, optional
            Name of the column containing Shapely Point objects (default: 'coordinates')
        suburb_column : str, optional
            Name of the suburb column (default: 'suburb')

        Returns:
        --------
        pd.Series or pd.DataFrame
            Series with imputed values if single column, DataFrame if multiple columns
        """
        # Convert single column name to list for uniform processing
        if isinstance(column_names, str):
            column_names = [column_names]
            return_series = True
        else:
            return_series = False

        # Create copies of the columns to avoid modifying the original
        results = {}
        for col in column_names:
            results[col] = df[col].copy()

        # Find rows where ANY of the columns have null values
        any_null_mask = pd.Series(False, index=df.index)
        for col in column_names:
            any_null_mask |= results[col].isna()

        null_indices = df[any_null_mask].index

        print(f"Imputing null values in {len(column_names)} column(s): {column_names}")
        print(f"Total rows with null values to impute: {len(null_indices)}")

        # Counter for tracking imputation
        imputed_count = 0
        not_imputed_count = 0

        # Iterate through each row with null value
        for idx in null_indices:
            # Check if any column needs imputation for this row
            needs_imputation = any(
                results[col].loc[idx] is pd.NA or pd.isna(results[col].loc[idx])
                for col in column_names
            )

            if not needs_imputation:
                continue

            # Get the suburb and coordinates of the current row
            current_suburb = df.loc[idx, suburb_column]
            current_coords = df.loc[idx, coordinates_column]

            # Find rows in the same suburb (excluding current row)
            same_suburb_mask = (df[suburb_column] == current_suburb) & (df.index != idx)

            # Further filter to only include rows where ALL columns have non-null values
            for col in column_names:
                same_suburb_mask &= results[col].notna()

            same_suburb_data = df[same_suburb_mask]

            if len(same_suburb_data) > 0:
                # Calculate distances to all points in the same suburb with non-null values
                distances = same_suburb_data[coordinates_column].apply(
                    lambda point: current_coords.distance(point)
                )

                # Find the index of the nearest point
                nearest_idx = distances.idxmin()

                # Impute each column from the nearest point
                for col in column_names:
                    if pd.isna(results[col].loc[idx]):
                        results[col].loc[idx] = results[col].loc[nearest_idx]

                imputed_count += 1
            else:
                # Fallback: search globally if no data in same suburb
                global_mask = df.index != idx

                # Filter to only include rows where ALL columns have non-null values
                for col in column_names:
                    global_mask &= results[col].notna()

                global_data = df[global_mask]

                if len(global_data) > 0:
                    # Calculate distances to all points globally with non-null values
                    distances = global_data[coordinates_column].apply(
                        lambda point: current_coords.distance(point)
                    )

                    # Find the index of the nearest point
                    nearest_idx = distances.idxmin()

                    # Impute each column from the nearest point
                    for col in column_names:
                        if pd.isna(results[col].loc[idx]):
                            results[col].loc[idx] = results[col].loc[nearest_idx]

                    imputed_count += 1
                else:
                    # No data available anywhere with non-null values
                    not_imputed_count += 1

        print(
            f"Successfully imputed: {imputed_count} rows, Could not impute (no data available): {not_imputed_count}"
        )

        # Return Series if single column, DataFrame if multiple columns
        if return_series:
            return results[column_names[0]]
        else:
            return pd.DataFrame(results)

    def merge_batches(self, input_dir, pattern="*.csv", verbose=True):
        """
        Merge multiple CSV files from a directory into a single DataFrame.

        Parameters:
        -----------
        input_dir : str
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

    def extract_suburb_name(self, df):
        """
        Extract the suburb name from the localities excel spreadsheet.

        Args:
            df (pd.DataFrame): DataFrame from G02 sheet

        Returns:
            str: Suburb name
        """
        # Suburb info is always in row 2, first column
        cell_value = str(df.iloc[1, 0])

        # Regex: capture everything before (SALxxxxx)
        match = re.search(r"(.+?)\s+\(SAL\d+\)", cell_value)
        if match:
            suburb = match.group(1).strip()
            return suburb
        return "Unknown"

    def process_census_excel_to_csv(
        self, file_path, selected_sheets, sal_code, suburb, base_data_dir="../data/"
    ):
        """
        Process census Excel files and convert selected sheets to CSV format.

        Args:
            file_path (str): Path to the Excel file
            selected_sheets (list): List of sheet names to process
            sal_code (str): SAL code for the suburb
            suburb (str): Suburb name
            base_data_dir (str): Base data directory path
        """
        population_dir = os.path.join(base_data_dir, "landing", "population_by_suburb")

        for sheet in selected_sheets:
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)

            if sheet == "G02":
                # Left side table (col 0 = name, col 1 = value)
                left = df[[0, 1]].dropna().rename(columns={0: "Statistic", 1: "Value"})

                # Right side table (col 3 = name, col 4 = value)
                right = df[[3, 4]].dropna().rename(columns={3: "Statistic", 4: "Value"})

                # Combine both
                g02_cleaned = pd.concat([left, right], ignore_index=True)
                g02_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_median_stats.csv"
                )
                if not os.path.exists(output_path):
                    g02_cleaned.to_csv(output_path, index=False)

            elif sheet == "G04":
                # Find where "Age (years):" appears → start of table
                start_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("Age", na=False)
                    ].tolist()[0]
                    + 1
                )

                # Slice everything below that row
                table = df.iloc[start_row:, :]

                # Define the 3 blocks of columns (start_col, end_col)
                blocks = [(0, 3), (5, 8), (10, 13)]

                persons_dfs = []
                for start, end in blocks:
                    temp = table.iloc[:, start : end + 1].copy()
                    temp.columns = ["Age group", "Males", "Females", "Persons"]

                    # Drop rows where both Age group and Persons are empty
                    temp = temp.dropna(subset=["Age group", "Persons"], how="any")

                    # Keep only the relevant columns
                    persons_dfs.append(temp[["Age group", "Persons"]])

                # Combine all blocks vertically
                persons_only = pd.concat(persons_dfs, ignore_index=True)
                g04_cleaned = persons_only.reset_index(drop=True)
                g04_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_population_breakdown.csv"
                )
                if not os.path.exists(output_path):
                    g04_cleaned.to_csv(output_path, index=False)

            elif sheet == "G17":
                start_row = (
                    df.index[
                        df.iloc[:, 1].astype(str).str.contains("PERSONS", na=False)
                    ].tolist()[0]
                    + 1
                )
                end_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("This table", na=False)
                    ].tolist()[0]
                    - 1
                )

                # Slice everything between these rows
                g17_cleaned = df.iloc[start_row + 1 : end_row, :]
                g17_cleaned.columns = [
                    "Price Range",
                    "15-19",
                    "20-24",
                    "25-34",
                    "35-44",
                    "45-54",
                    "55-64",
                    "65-74",
                    "75-84",
                    "85+",
                    "Total",
                ]
                # Drop empty row
                g17_cleaned = g17_cleaned.dropna(subset=["Price Range"])
                g17_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_personal_income.csv"
                )
                if not os.path.exists(output_path):
                    g17_cleaned.to_csv(output_path, index=False)

            elif sheet == "G33":
                start_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("Negative", na=False)
                    ].tolist()[0]
                    + 1
                )
                end_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("Total", na=False)
                    ].tolist()[0]
                    + 1
                )

                # Slice everything between these rows
                g33_cleaned = df.iloc[start_row + 1 : end_row, :]
                g33_cleaned.columns = [
                    "Income",
                    "Family Households",
                    "Non-family Households",
                    "Total",
                ]

                # Drop empty rows
                g33_cleaned = g33_cleaned.dropna(subset=["Income"])
                g33_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_household_income.csv"
                )
                if not os.path.exists(output_path):
                    g33_cleaned.to_csv(output_path, index=False)

            elif sheet == "G36":
                # Find the start and end of the table
                start_idx = df[
                    df[0].str.contains("Occupied private dwellings", na=False)
                ].index[0]
                end_idx = df[
                    df[0].str.contains("Total private dwellings", na=False)
                ].index[0]

                # Extract only the table rows
                table_df = df.iloc[start_idx : end_idx + 1, :3]  # first 3 columns

                # Set proper column names
                table_df.columns = ["Dwelling Type", "Dwellings", "Persons"]

                # Remove empty rows
                table_df = table_df.dropna(subset=["Dwelling Type"])

                # Drop "Occupied private dwellings:" header row
                table_df = table_df.drop(
                    table_df[
                        table_df["Dwelling Type"] == "Occupied private dwellings:"
                    ].index
                ).reset_index(drop=True)

                current_section = None
                new_labels = []

                # Define the "global totals" that should not be prefixed
                global_totals = [
                    "Total occupied private dwellings",
                    "Unoccupied private dwellings",
                    "Total private dwellings",
                    "Dwelling structure not stated",
                ]

                for val in table_df["Dwelling Type"]:
                    if pd.isna(val):
                        new_labels.append(val)
                    elif isinstance(val, str) and val.endswith(":"):
                        # Section header
                        current_section = val.replace(":", "")
                        new_labels.append(None)
                    elif val == "Total":
                        # Totals inside a section
                        new_labels.append(f"{current_section} - Total")
                    elif val in global_totals:
                        # Reset section for these
                        current_section = None
                        new_labels.append(val)
                    else:
                        # Normal row
                        if current_section:
                            new_labels.append(f"{current_section} - {val}")
                        else:
                            new_labels.append(val)

                table_df["Dwelling Type"] = new_labels
                g36_cleaned = table_df.dropna(subset=["Dwelling Type"]).reset_index(
                    drop=True
                )
                g36_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_dwelling_structure.csv"
                )
                if not os.path.exists(output_path):
                    g36_cleaned.to_csv(output_path, index=False)

            elif sheet == "G49":
                start_row = (
                    df.index[
                        df.iloc[:, 1].astype(str).str.contains("PERSONS", na=False)
                    ].tolist()[0]
                    + 1
                )
                end_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("This table", na=False)
                    ].tolist()[0]
                    - 1
                )

                # Slice everything between these rows
                g49_cleaned = df.iloc[start_row + 1 : end_row, :]
                g49_cleaned.columns = [
                    "Highest Education Level",
                    "15-24",
                    "25-34",
                    "35-44",
                    "45-54",
                    "55-64",
                    "65-74",
                    "75-84",
                    "85+",
                    "Total",
                ]
                # Drop empty row
                g49_cleaned = g49_cleaned.dropna(
                    subset=["Highest Education Level"]
                ).reset_index(drop=True)
                # Drop certificate header and total rows
                g49_cleaned = g49_cleaned.drop([4, 8])
                g49_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(
                    population_dir, f"{sal_code}_education_level.csv"
                )
                if not os.path.exists(output_path):
                    g49_cleaned.to_csv(output_path, index=False)

            elif sheet == "G60":
                start_row = (
                    df.index[
                        df.iloc[:, 1].astype(str).str.contains("PERSONS", na=False)
                    ].tolist()[0]
                    + 1
                )
                end_row = (
                    df.index[
                        df.iloc[:, 0].astype(str).str.contains("This table", na=False)
                    ].tolist()[0]
                    - 1
                )

                # Slice everything between these rows
                g60_cleaned = df.iloc[start_row + 1 : end_row, :]
                g60_cleaned.columns = [
                    "Age",
                    "Managers",
                    "Proffesionals",
                    "Trades workers",
                    "Community workers",
                    "Administrative Workers",
                    "Sales Workers",
                    "Drivers",
                    "Labourers",
                    "Not Stated",
                    "Total",
                ]
                # Drop empty row
                g60_cleaned = g60_cleaned.dropna(subset=["Age"]).reset_index(drop=True)
                g60_cleaned["Suburb"] = suburb

                # Save the CSV if it doesn't already exist
                output_path = os.path.join(population_dir, f"{sal_code}_job_type.csv")
                if not os.path.exists(output_path):
                    g60_cleaned.to_csv(output_path, index=False)

    def process_all_census_data(
        self,
        no_data_list=None,
        sal_start=20001,
        sal_end=22944,
        base_data_dir="../data/",
    ):
        """
        Process all downloaded census Excel files and convert them to CSV format.

        Args:
            no_data_list (list): List of SAL codes that don't have data
            sal_start (int): Starting SAL code (default: 20001)
            sal_end (int): Ending SAL code (default: 22944)
            base_data_dir (str): Base data directory path
        """
        print("=== PROCESSING CENSUS DATA TO CSV ===")

        if no_data_list is None:
            no_data_list = []

        population_dir = os.path.join(base_data_dir, "landing", "population_by_suburb")
        selected_sheets = ["G02", "G04", "G17", "G33", "G36", "G49", "G60"]

        processed_count = 0

        for i in range(sal_start, sal_end + 1):
            if i not in no_data_list:
                sal_code = f"SAL{i}"
                file_path = os.path.join(population_dir, f"{sal_code}_population.xlsx")

                if os.path.exists(file_path):
                    try:
                        # Retrieve the suburb name
                        df = pd.read_excel(file_path, sheet_name="G02", header=None)
                        suburb = self.extract_suburb_name(df)

                        # Process the Excel file to CSV
                        self.process_census_excel_to_csv(
                            file_path, selected_sheets, sal_code, suburb, base_data_dir
                        )
                        processed_count += 1

                        if processed_count % 100 == 0:
                            print(f"Processed {processed_count} files...")

                    except Exception as e:
                        print(f"Error processing {sal_code}: {e}")

        print(f"Successfully processed {processed_count} census files")

    def merge_census_csv_files(self, base_data_dir="../data/"):
        """
        Merge all individual census CSV files into consolidated datasets.

        Args:
            base_data_dir (str): Base data directory path
        """
        print("=== MERGING CENSUS CSV FILES ===")

        population_dir = os.path.join(base_data_dir, "landing", "population_by_suburb")
        landing_dir = os.path.join(base_data_dir, "landing")

        # Define the file patterns and output names
        file_patterns = {
            "median_stats": "*_median_stats.csv",
            "population_breakdown": "*_population_breakdown.csv",
            "personal_income": "*_personal_income.csv",
            "household_income": "*_household_income.csv",
            "dwelling_structure": "*_dwelling_structure.csv",
            "job_type": "*_job_type.csv",
            "education_level": "*_education_level.csv",
        }

        for dataset_name, pattern in file_patterns.items():
            all_files = glob.glob(os.path.join(population_dir, pattern))

            if all_files:
                try:
                    df = pd.concat(
                        (pd.read_csv(f) for f in all_files), ignore_index=True
                    )
                    output_path = os.path.join(landing_dir, f"{dataset_name}.csv")

                    if not os.path.exists(output_path):
                        df.to_csv(output_path, index=False)
                        print(f"✅ Created {dataset_name}.csv with {len(df)} records")
                    else:
                        print(f"⚠️  {dataset_name}.csv already exists")

                except Exception as e:
                    print(f"❌ Error merging {dataset_name}: {e}")
            else:
                print(f"⚠️  No files found for pattern: {pattern}")

    def process_census_data_workflow(
        self,
        no_data_list=None,
        sal_start=20001,
        sal_end=22944,
        base_data_dir="../data/",
    ):
        """
        Complete workflow to process census data from Excel files to consolidated CSV files.

        Args:
            no_data_list (list): List of SAL codes that don't have data
            sal_start (int): Starting SAL code (default: 20001)
            sal_end (int): Ending SAL code (default: 22944)
            base_data_dir (str): Base data directory path
        """
        print("Starting complete census data processing workflow...")

        # Step 1: Process Excel files to CSV
        self.process_all_census_data(no_data_list, sal_start, sal_end, base_data_dir)

        # Step 2: Merge CSV files
        self.merge_census_csv_files(base_data_dir)

        print("Census data processing completed!")
