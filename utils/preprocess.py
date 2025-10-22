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

    def excel_to_csv(self, file_path, selected_sheets, sal_code, suburb):
        """
        Creates flat CSVs for data stored in multisheet Excel documents.

        Args:
            file_path (str): Path to the Excel file
            selected_sheets (list): List of sheet names to process
            sal_code (str): SAL code for the suburb
            suburb (str): Suburb name
        """
        # Create base output directory if it doesn't exist
        base_output_dir = "../data/raw/census"
        os.makedirs(base_output_dir, exist_ok=True)

        for sheet in selected_sheets:
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)

            if sheet == "G02":
                # Left side table (col 0 = name, col 1 = value)
                left = df[[0, 1]].dropna().rename(columns={0: "Statistic", 1: "Value"})

                # Right side table (col 3 = name, col 4 = value)
                right = df[[3, 4]].dropna().rename(columns={3: "Statistic", 4: "Value"})

                # Combine both
                g02_cleaned = pd.concat([left, right], ignore_index=True)
                # add sheet identifier
                g02_cleaned["Suburb"] = suburb

                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "median_stats")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{sal_code}_median_stats.csv")
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

                # Reset index
                g04_cleaned = persons_only.reset_index(drop=True)

                # add sheet identifier
                g04_cleaned["Suburb"] = suburb
                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "population_breakdown")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir, f"{sal_code}_population_breakdown.csv"
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
                # drop empty row
                g17_cleaned = g17_cleaned.dropna(subset=["Price Range"])

                # add suburb name
                g17_cleaned["Suburb"] = suburb
                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "personal_income")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir, f"{sal_code}_personal_income.csv"
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

                # drop empty rows
                g33_cleaned = g33_cleaned.dropna(subset=["Income"])
                # add suburb name
                g33_cleaned["Suburb"] = suburb

                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "household_income")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir, f"{sal_code}_household_income.csv"
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
                table_df = df.iloc[
                    start_idx : end_idx + 1, :3
                ]  # first 3 columns (Description, Dwellings, Persons)

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

                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "dwelling_structure")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir, f"{sal_code}_dwelling_structure.csv"
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
                # drop empty row
                g49_cleaned = g49_cleaned.dropna(
                    subset=["Highest Education Level"]
                ).reset_index(drop=True)
                # drop certificate header and total rows
                g49_cleaned = g49_cleaned.drop([4, 8])

                # add suburb name
                g49_cleaned["Suburb"] = suburb

                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "education_level")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir, f"{sal_code}_education_level.csv"
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
                # drop empty row
                g60_cleaned = g60_cleaned.dropna(subset=["Age"]).reset_index(drop=True)

                # add suburb name
                g60_cleaned["Suburb"] = suburb
                # save the csv if it doesn't already exist
                output_dir = os.path.join(base_output_dir, "job_type")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{sal_code}_job_type.csv")
                if not os.path.exists(output_path):
                    g60_cleaned.to_csv(output_path, index=False)

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
        base_data_dir="../data/",
    ):
        """
        Process all downloaded census Excel files and convert them to CSV format.

        Args:
            base_data_dir (str): Base data directory path
        """
        print("=== PROCESSING CENSUS DATA TO CSV ===")

        population_dir = os.path.join(base_data_dir, "landing", "population_by_suburb")
        selected_sheets = ["G02", "G04", "G17", "G33", "G36", "G49", "G60"]

        processed_count = 0

        # Get all Excel files in the population directory
        excel_files = [f for f in os.listdir(population_dir) if f.endswith(".xlsx")]
        excel_files.sort()  # Process in alphabetical order

        print(f"Found {len(excel_files)} Excel files to process")

        for file_name in excel_files:
            file_path = os.path.join(population_dir, file_name)
            try:
                # Extract SAL code from filename (e.g., "SAL20001_population.xlsx" -> "SAL20001")
                sal_code = file_name.replace("_population.xlsx", "")

                # Retrieve the suburb name
                df = pd.read_excel(file_path, sheet_name="G02", header=None)
                suburb = self.extract_suburb_name(df)

                # Process the Excel file to CSV
                self.excel_to_csv(file_path, selected_sheets, sal_code, suburb)
                processed_count += 1

                if processed_count % 100 == 0:
                    print(f"Processed {processed_count} files...")

            except Exception as e:
                print(f"Error processing {file_name}: {e}")

        print(f"Successfully processed {processed_count} census files")

    def merge_census_csv_files(self, base_data_dir="../data/"):
        """
        Merge all individual census CSV files into consolidated datasets.

        Args:
            base_data_dir (str): Base data directory path
        """
        print("=== MERGING CENSUS CSV FILES ===")

        population_dir = os.path.join(base_data_dir, "raw", "census")

        processed_dir = os.path.join(base_data_dir, "processed", "census")

        # Create processed directory if it doesn't exist
        os.makedirs(processed_dir, exist_ok=True)

        # Define the subdirectories and their corresponding dataset names
        dataset_directories = {
            "median_stats": "median_stats",
            "population_breakdown": "population_breakdown",
            "personal_income": "personal_income",
            "household_income": "household_income",
            "dwelling_structure": "dwelling_structure",
            "job_type": "job_type",
            "education_level": "education_level",
        }

        for dataset_name, subdirectory in dataset_directories.items():
            subdirectory_path = os.path.join(population_dir, subdirectory)
            if os.path.exists(subdirectory_path):
                all_files = glob.glob(os.path.join(subdirectory_path, "*.csv"))
            else:
                all_files = []

            if all_files:
                try:
                    df = pd.concat(
                        (pd.read_csv(f) for f in all_files), ignore_index=True
                    )
                    output_path = os.path.join(processed_dir, f"{dataset_name}.csv")

                    if not os.path.exists(output_path):
                        df.to_csv(output_path, index=False)
                        print(f"✅ Created {dataset_name}.csv with {len(df)} records")
                    else:
                        print(f"⚠️  {dataset_name}.csv already exists")

                except Exception as e:
                    print(f"❌ Error merging {dataset_name}: {e}")
            else:
                print(f"⚠️  No files found in subdirectory: {subdirectory}")

    def process_census_data_workflow(
        self,
        base_data_dir="../data/",
    ):
        """
        Complete workflow to process census data from Excel files to consolidated CSV files.

        Args:
            base_data_dir (str): Base data directory path
        """
        print("Starting complete census data processing workflow...")

        # Step 1: Process Excel files to CSV
        self.process_all_census_data(base_data_dir)

        # Step 2: Merge CSV files
        self.merge_census_csv_files(base_data_dir)

        print("Census data processing completed!")

    def parse_property_features(self, feature_string):
        """
        Parse property_features column to extract bedrooms, bathrooms, car_spaces, and land_area.

        Format: 'bedrooms, ,bathrooms, ,car_spaces,' or 'bedrooms, ,bathrooms, ,car_spaces, ,XXXm²,'
                or 'bedrooms, ,bathrooms, ,car_spaces, ,X.XXha,'
        Missing values are represented by '−'
        Land area can be in m² or ha (hectares are converted to m²: 1 ha = 10,000 m²)

        Returns: pd.Series with four integer values (bedrooms, bathrooms, car_spaces, land_area)
        """
        # Split by ', ,'
        parts = feature_string.split(", ,")

        # Initialize values
        bedrooms = None
        bathrooms = None
        car_spaces = None
        land_area = None

        # Extract bedrooms (index 0)
        if len(parts) > 0:
            val = parts[0].strip().rstrip(",")
            # Check if this is just a land area value (like '12.51ha,')
            if "ha" in val or "m²" in val:
                # This entire string is just land area, extract it
                if "ha" in val:
                    land_area_str = val.replace("ha", "").replace(",", "").strip()
                    if land_area_str and land_area_str != "−":
                        land_area = int(
                            float(land_area_str) * 10000
                        )  # Convert ha to m²
                elif "m²" in val:
                    land_area_str = val.replace("m²", "").replace(",", "").strip()
                    if land_area_str and land_area_str != "−":
                        land_area = int(land_area_str)
            else:
                bedrooms = None if val == "−" or val == "" else int(val)

        # Extract bathrooms (index 1)
        if len(parts) > 1:
            val = parts[1].strip().rstrip(",")
            bathrooms = None if val == "−" or val == "" else int(val)

        # Extract car_spaces (index 2)
        if len(parts) > 2:
            val = parts[2].strip().rstrip(",")
            car_spaces = None if val == "−" or val == "" else int(val)

        # Extract land_area (index 3, if present and not already extracted)
        if land_area is None and len(parts) > 3:
            val = parts[3].strip().rstrip(",")
            if "ha" in val:
                # Remove 'ha' and extract number (handle commas and decimals like '12.51ha')
                land_area_str = val.replace("ha", "").replace(",", "").strip()
                if land_area_str and land_area_str != "−":
                    land_area = int(
                        float(land_area_str) * 10000
                    )  # Convert ha to m², then to int
            elif "m²" in val:
                # Remove 'm²' and extract number (handle commas in numbers like '5,030m²')
                land_area_str = val.replace("m²", "").replace(",", "").strip()
                if land_area_str and land_area_str != "−":
                    land_area = int(land_area_str)

        return pd.Series([bedrooms, bathrooms, car_spaces, land_area])

    def preprocess_live_listings(self, df):
        """
        Preprocess live listings data from Domain website.

        Args:
            df: DataFrame with live listings data

        Returns:
            Preprocessed DataFrame
        """
        # Convert column names to lowercase with snake case
        df.columns = df.columns.str.lower().str.replace(" ", "_")

        # Remove rows where property_id is null
        df = df[df["property_id"].notna()]

        # Convert property_id to Int64
        df["property_id"] = df["property_id"].astype("Int64")

        # Remove rows where property_features is null
        df = df[df["property_features"].notna()]

        # Drop the bathrooms, bedrooms, car_spaces, land_area columns (will be recreated from property_features)
        df = df.drop(
            columns=["bathrooms", "bedrooms", "car_spaces", "land_area"],
            errors="ignore",
        )

        # Drop rows with not permitted property_type
        permitted_types = [
            "house",
            "new house & land",
            "townhouse",
            "villa",
            "semi-detached",
            "terrace",
            "duplex",
            "apartment / unit / flat",
            "studio",
            "new apartments / off the plan",
            "penthouse",
        ]

        # Remove rows where description is null
        df = df[df["description"].notna()]

        df["property_type"] = df["property_type"].str.lower()
        df = df[df["property_type"].isin(permitted_types)]

        # Map property types
        df["house_flat_other"] = self.map_property_type(df["property_type"])

        # Map suburbs
        df["suburb"] = self.map_suburb(df["suburb"])

        # Remove suburbs with count less than 10
        suburb_counts = df["suburb"].value_counts()
        valid_suburbs = suburb_counts[suburb_counts > 10].index
        df = df[df["suburb"].isin(valid_suburbs)]

        # Parse property features
        df[["bedrooms", "bathrooms", "car_spaces", "land_area"]] = df[
            "property_features"
        ].apply(self.parse_property_features)

        # Convert to nullable integer type (Int64) to preserve NaNs while using integer type
        df["bedrooms"] = df["bedrooms"].astype("Int64")
        df["bathrooms"] = df["bathrooms"].astype("Int64")
        df["car_spaces"] = df["car_spaces"].astype("Int64")
        df["land_area"] = df["land_area"].astype("Int64")

        # Drop land_area since mostly missing and difficult to fill
        df = df.drop(columns=["land_area"])

        # Impute missing values by property type mode
        df["bedrooms"] = self.impute_by_property_type_mode(df, "bedrooms")
        df["bathrooms"] = self.impute_by_property_type_mode(df, "bathrooms")
        df["car_spaces"] = self.impute_by_property_type_mode(df, "car_spaces")

        # Impute appointment_only
        df["appointment_only"] = df["appointment_only"].fillna(
            df["appointment_only"].mode()[0]
        )

        # Convert date columns to datetime
        df["updated_date"] = pd.to_datetime(df["updated_date"], format="mixed")
        df["first_listed_date"] = pd.to_datetime(
            df["first_listed_date"], format="mixed"
        )
        df["last_sold_date"] = pd.to_datetime(df["last_sold_date"], format="mixed")

        # Convert updated_date to year and quarter
        df["year"] = df["updated_date"].dt.year
        df["quarter"] = df["updated_date"].dt.quarter

        # Extract weekly rent from rental_price column
        df["rental_price"] = self.extract_rental_price(df["rental_price"])

        # Drop rows with unknown frequencies
        df = df[df["rental_price"].notna()]

        return df

    def preprocess_wayback_listings(self, df_list, geo_utils):
        """
        Preprocess wayback listings data from Domain website.

        Args:
            df_list: List of DataFrames with wayback listings data
            geo_utils: GeoUtils instance for address extraction

        Returns:
            Preprocessed DataFrame
        """
        # Stack all dataframes together
        df = pd.concat(df_list, ignore_index=True)

        # Map suburbs
        df["suburb"] = self.map_suburb(df["suburb"])

        # Remove suburbs with count less than 10
        suburb_counts = df["suburb"].value_counts()
        valid_suburbs = suburb_counts[suburb_counts > 10].index
        df = df[df["suburb"].isin(valid_suburbs)]

        # Drop land_area column
        df = df.drop(columns=["land_area"])

        # Convert bedrooms, bathrooms, car_spaces to Int64
        df["bedrooms"] = df["bedrooms"].astype("Int64")
        df["bathrooms"] = df["bathrooms"].astype("Int64")
        df["car_spaces"] = df["car_spaces"].astype("Int64")

        # Impute missing values by property type mode
        df["bedrooms"] = self.impute_by_property_type_mode(df, "bedrooms")
        df["bathrooms"] = self.impute_by_property_type_mode(df, "bathrooms")
        df["car_spaces"] = self.impute_by_property_type_mode(df, "car_spaces")

        # Extract weekly rent from rental_price column
        df["rental_price"] = self.extract_rental_price(df["rental_price"])

        # Drop rows with unknown frequencies
        df = df[df["rental_price"].notna()]

        # Extract address from url
        df["address"] = df["url"].apply(geo_utils.extract_address_from_url)

        # Drop unnecessary columns
        df = df.drop(
            columns=[
                "url",
                "property_features",
                "postcode",
                "scraped_date",
                "wayback_url",
                "wayback_time",
            ]
        )

        # Remove duplicates, keeping first occurrence (most recent)
        df = df.sort_values(by=["year", "quarter"], ascending=False)
        df = df.drop_duplicates(subset=["property_id"], keep="first")

        # Drop remaining nulls
        df = df.dropna()

        return df

    def combine_and_sample_listings(self, live_df, wayback_df, sample_ratio=0.5):
        """
        Combine live and wayback listings, then perform stratified sampling.

        Args:
            live_df: Preprocessed live listings DataFrame
            wayback_df: Preprocessed wayback listings DataFrame
            sample_ratio: Ratio for stratified sampling (default 0.5)

        Returns:
            Sampled combined DataFrame
        """
        # Ensure both dataframes have the same columns
        common_columns = [
            "property_id",
            "rental_price",
            "bedrooms",
            "bathrooms",
            "car_spaces",
            "property_type",
            "suburb",
            "year",
            "quarter",
            "longitude",
            "latitude",
            "coordinates",
        ]

        live_df = live_df[common_columns]
        wayback_df = wayback_df[common_columns]

        # Combine dataframes
        df = pd.concat([live_df, wayback_df])

        # Sort by year, quarter descending and remove duplicates
        df = df.sort_values(by=["year", "quarter"], ascending=False)
        df = df.drop_duplicates(subset=["property_id"], keep="first")

        # Convert property_id to Int64
        df["property_id"] = df["property_id"].astype("Int64")

        # Perform stratified sampling
        import numpy as np

        np.random.seed(42)

        # Shuffle the dataframe randomly
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Create stratification groups based on property_type, suburb, and bedrooms
        df_shuffled["strata"] = (
            df_shuffled["property_type"].astype(str)
            + "_"
            + df_shuffled["suburb"].astype(str)
            + "_"
            + df_shuffled["bedrooms"].astype(str)
        )

        # Perform stratified sampling
        df_sampled = df_shuffled.groupby("strata", group_keys=False).apply(
            lambda x: x.sample(frac=sample_ratio, random_state=42) if len(x) > 1 else x
        )

        # Drop the temporary strata column
        df_sampled = df_sampled.drop(columns=["strata"])

        # Reset index
        df_sampled = df_sampled.reset_index(drop=True)

        return df_sampled

    def remove_outliers(
        self, df, column_name, lower_quantile=0.01, upper_quantile=0.99
    ):
        """
        Remove outliers from a DataFrame column based on quantile thresholds.

        Args:
            df: DataFrame to process
            column_name: Name of the column to remove outliers from
            lower_quantile: Lower quantile threshold (default: 0.01)
            upper_quantile: Upper quantile threshold (default: 0.99)

        Returns:
            DataFrame with outliers removed
        """
        # Calculate quantile thresholds
        lower_threshold = df[column_name].quantile(lower_quantile)
        upper_threshold = df[column_name].quantile(upper_quantile)

        print(f"Removing outliers from {column_name}:")
        print(
            f"  Lower threshold ({lower_quantile*100}% quantile): {lower_threshold:.2f}"
        )
        print(
            f"  Upper threshold ({upper_quantile*100}% quantile): {upper_threshold:.2f}"
        )

        # Count outliers before removal
        outliers_before = (
            (df[column_name] < lower_threshold) | (df[column_name] > upper_threshold)
        ).sum()
        print(
            f"  Outliers to remove: {outliers_before:,} rows ({outliers_before/len(df)*100:.2f}%)"
        )

        # Remove outliers
        df_clean = df[
            (df[column_name] >= lower_threshold) & (df[column_name] <= upper_threshold)
        ].copy()

        print(f"  Dataset shape before: {df.shape}")
        print(f"  Dataset shape after: {df_clean.shape}")
        print(f"  Rows removed: {df.shape[0] - df_clean.shape[0]:,}")

        return df_clean

    def process_moving_annual_rent_excel_file(self, file_path):
        """
        Process a single Excel file and extract median rent data from moving annual rent files.

        Args:
            file_path (str): Path to the Excel file

        Returns:
            pd.DataFrame: Processed data with columns: suburb, property_type, quarter, year, median_rent
        """
        # Read all sheets from the Excel file
        all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)

        # Property types we want to process (excluding 'All properties')
        property_types = [
            "1 bedroom flat",
            "2 bedroom flat",
            "3 bedroom flat",
            "2 bedroom house",
            "3 bedroom house",
            "4 bedroom house",
        ]

        all_data = []

        for sheet_name, df in all_sheets.items():
            if sheet_name not in property_types:
                continue

            print(f"Processing {sheet_name} from {os.path.basename(file_path)}")

            # Find the data start row (where suburbs begin)
            # Look for the first non-null value in the first column that's not a header
            data_start_row = None
            for i in range(len(df)):
                if pd.notna(df.iloc[i, 0]) and df.iloc[i, 0] not in [
                    "Moving annual median rent by suburb",
                    "1 bedroom flat",
                    "2 bedroom flat",
                    "3 bedroom flat",
                    "2 bedroom house",
                    "3 bedroom house",
                    "4 bedroom house",
                ]:
                    data_start_row = i
                    break

            if data_start_row is None:
                print(f"Warning: Could not find data start row for {sheet_name}")
                continue

            # Extract suburb names (second column, starting from data_start_row)
            # Filter out NaN values and Group Total rows
            suburb_series = df.iloc[data_start_row:, 1].dropna()
            suburbs = suburb_series[
                ~suburb_series.str.contains("Group Total", case=False, na=False)
            ].tolist()

            # Lowercase all suburbs
            suburbs = [suburb.lower() for suburb in suburbs]

            # Process each quarter/year combination
            # The pattern is: every 2 columns starting from column 2
            # Column 2: Mar 2000, Column 4: Jun 2000, Column 6: Sep 2000, Column 8: Dec 2000, etc.

            col_idx = 2  # Start from column 2
            while col_idx < df.shape[1]:
                # Check if this column has a quarter/year header
                quarter_year = df.iloc[1, col_idx]  # Row 1 contains quarter/year

                if (
                    pd.isna(quarter_year)
                    or "Count" in str(quarter_year)
                    or "Median" in str(quarter_year)
                ):
                    col_idx += 1
                    continue

                # The median data is in the next column (col_idx + 1)
                median_col = col_idx + 1

                if median_col >= df.shape[1]:
                    break

                # Parse quarter and year
                try:
                    quarter, year = str(quarter_year).split()
                    year = int(year)
                except:
                    col_idx += 2
                    continue

                # convert quarter from month name to quarter number
                quarter = {
                    "Jan": 1,
                    "Feb": 1,
                    "Mar": 1,
                    "Apr": 2,
                    "May": 2,
                    "Jun": 2,
                    "Jul": 3,
                    "Aug": 3,
                    "Sep": 3,
                    "Oct": 4,
                    "Nov": 4,
                    "Dec": 4,
                }[quarter]

                # Extract median values for this quarter/year
                # We need to get the values from column 1 (suburbs) and the corresponding median values
                suburb_data = df.iloc[data_start_row:, [1, median_col]].dropna(
                    subset=[1]
                )

                # Filter out Group Total rows and create mapping
                suburb_median_map = {}
                for idx, row in suburb_data.iterrows():
                    suburb_name = str(row.iloc[0]).lower()
                    median_value = row.iloc[1]

                    # Skip Group Total rows
                    if "group total" in suburb_name:
                        continue

                    # Store the mapping
                    suburb_median_map[suburb_name] = median_value

                # Create data for this quarter/year using the filtered suburbs
                for suburb in suburbs:
                    if suburb in suburb_median_map:
                        median_value = suburb_median_map[suburb]
                        if pd.notna(median_value) and median_value != "-":
                            try:
                                median_rent = float(median_value)
                                all_data.append(
                                    {
                                        "suburb": suburb,
                                        "property_type": sheet_name,
                                        "quarter": quarter,
                                        "year": year,
                                        "median_rent": median_rent,
                                    }
                                )
                            except (ValueError, TypeError):
                                # Skip invalid values
                                continue

                col_idx += 2  # Move to next quarter/year pair

        return pd.DataFrame(all_data)

    def process_moving_annual_rent_files(self, data_dir):
        """
        Process all moving annual rent Excel files in the specified directory.

        Args:
            data_dir (str): Directory containing moving annual rent Excel files

        Returns:
            pd.DataFrame: Combined data from all files
        """
        all_data = []

        # Get all Excel files in the directory
        excel_files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]
        excel_files.sort()  # Process in chronological order

        print(f"Found {len(excel_files)} Excel files to process:")
        for file in excel_files:
            print(f"  - {file}")

        for file in excel_files:
            file_path = os.path.join(data_dir, file)
            try:
                file_data = self.process_moving_annual_rent_excel_file(file_path)
                if not file_data.empty:
                    all_data.append(file_data)
                    print(f"Successfully processed {file}: {len(file_data)} records")
                else:
                    print(f"Warning: No data extracted from {file}")
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")

        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            return combined_data
        else:
            return pd.DataFrame()

    def process_school_data(self, schools_dir="../data/landing/schools"):
        """
        Process and standardize school data from multiple CSV files.

        Args:
            schools_dir (str): Directory containing school CSV files

        Returns:
            pd.DataFrame: Processed and standardized school data
        """
        import os
        from difflib import get_close_matches

        # List all CSV files in the directory
        csv_files = [f for f in os.listdir(schools_dir) if f.endswith(".csv")]

        # Define the standardized schema based on common columns across all years
        standard_columns = [
            "Address_Line_1",
            "Address_Line_2",
            "Address_Postcode",
            "Address_State",
            "Address_Town",
            "Education_Sector",
            "Entity_Type",
            "Full_Phone_No",
            "LGA_ID",
            "LGA_Name",
            "Postal_Address_Line_1",
            "Postal_Address_Line_2",
            "Postal_Postcode",
            "Postal_State",
            "Postal_Town",
            "School_Name",
            "School_No",
            "School_Type",
            "X",
            "Y",
            # Additional columns that exist in some years
            "Area",
            "LGA_TYPE",
            "Region",
            "School_Status",
        ]

        def standardize_school_dataframe(df, year):
            """Standardize a school dataframe to have consistent columns."""
            # Create a copy to avoid modifying the original
            df_std = df.copy()

            # Handle column name variations
            column_mapping = {
                "AREA_Name": "Area",  # 2024 has AREA_Name instead of Area
                "Region_Name": "Region",  # 2024 has Region_Name instead of Region
            }

            # Rename columns
            df_std = df_std.rename(columns=column_mapping)

            # Add missing columns with NaN values
            for col in standard_columns:
                if col not in df_std.columns:
                    df_std[col] = None

            # Reorder columns to match standard schema
            df_std = df_std[standard_columns]

            # Add year column to indicate when school was established
            df_std["establishment_year"] = year

            return df_std

        # Load and standardize all school datasets
        print("Loading and standardizing all school datasets...")
        standardized_dfs = []

        for file in csv_files:
            year = file.split("_")[-1].split(".")[0]  # Extract year from filename
            print(f"\nProcessing {file} (year: {year})")

            # Load the full dataset
            try:
                df = pd.read_csv(os.path.join(schools_dir, file), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(os.path.join(schools_dir, file), encoding="latin1")

            print(f"  Loaded {len(df)} schools")

            # Standardize the dataframe
            df_std = standardize_school_dataframe(df, year)
            standardized_dfs.append(df_std)

            print(f"  Standardized to {len(df_std.columns)} columns")

        # Combine all standardized dataframes
        print(f"\nCombining {len(standardized_dfs)} datasets...")
        combined_schools = pd.concat(standardized_dfs, ignore_index=True)

        print(f"Combined dataset shape: {combined_schools.shape}")
        print(f"Total schools: {len(combined_schools)}")
        print(f"\nEstablishment year distribution:")
        print(combined_schools["establishment_year"].value_counts().sort_index())

        # Select relevant columns
        combined_schools = combined_schools[
            [
                "School_Name",
                "Education_Sector",
                "School_Type",
                "School_Status",
                "establishment_year",
                "X",
                "Y",
            ]
        ]

        # Convert the X, Y columns to a Point object from shapely
        from shapely.geometry import Point

        combined_schools["coordinates"] = combined_schools.apply(
            lambda row: Point(row["X"], row["Y"]), axis=1
        )

        # Round the X, Y columns to 1 decimal place
        combined_schools["X"] = combined_schools["X"].round(1)
        combined_schools["Y"] = combined_schools["Y"].round(1)

        # Remove schools with the same fuzzy matched name and X and Y duplicates at 1 dp
        to_drop = set()
        name_to_indices = {}
        for idx, row in combined_schools.iterrows():
            name = row["School_Name"]
            x = row["X"]
            y = row["Y"]

            # Find close matches to the current school name
            close_matches = get_close_matches(
                name, name_to_indices.keys(), n=1, cutoff=0.99
            )

            if close_matches:
                matched_name = close_matches[0]
                for matched_idx in name_to_indices[matched_name]:
                    matched_row = combined_schools.loc[matched_idx]
                    if matched_row["X"] == x and matched_row["Y"] == y:
                        # If X and Y also match, mark the current index for dropping
                        to_drop.add(idx)
                        break

            # Add the current index to the mapping
            if name not in name_to_indices:
                name_to_indices[name] = []
            name_to_indices[name].append(idx)

        print(
            f"Dropping {len(to_drop)} duplicate schools based on fuzzy name and coordinates match."
        )
        combined_schools = combined_schools.drop(index=to_drop).reset_index(drop=True)
        print(f"Dataset shape after removing duplicates: {combined_schools.shape}")

        # Sort by school_name
        combined_schools = combined_schools.sort_values(by="School_Name")

        # Remove 'School_Type' where it is 'Language', 'Camp'
        combined_schools = combined_schools[
            ~combined_schools["School_Type"].isin(["Language", "Camp"])
        ]

        # Remove 'School_Status' where it is 'Closed'
        combined_schools = combined_schools[combined_schools["School_Status"] != "C"]

        # Drop School_Status column
        combined_schools = combined_schools.drop(columns=["School_Status"])

        # Convert column names to lower casing
        combined_schools.columns = combined_schools.columns.str.lower()

        # Check for duplicate school_name
        duplicate_schools = combined_schools[
            combined_schools.duplicated(subset=["school_name"])
        ]

        # Group duplicate_schools by school_name, education_sector, school_type, establishment_year and count the number of occurences
        duplicate_schools_grouped = (
            duplicate_schools.groupby(
                ["school_name", "education_sector", "school_type", "establishment_year"]
            )
            .size()
            .reset_index(name="count")
        )

        # Get the school_name from duplicate_schools_grouped where count is greater than 1
        duplicate_school_names = duplicate_schools_grouped[
            duplicate_schools_grouped["count"] > 1
        ]["school_name"]

        # Remove schools with duplicate names
        combined_schools_unique = combined_schools[
            ~combined_schools["school_name"].isin(duplicate_school_names)
        ]

        return combined_schools_unique

    def scrape_school_rankings(self):
        """
        Scrape school rankings from Better Education website.

        Returns:
            pd.DataFrame: School rankings data
        """
        import io
        import requests
        import re
        from difflib import get_close_matches

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "Referer": "https://bettereducation.com.au/Results/vce.aspx",
            "Cache-Control": "no-cache",
        }
        url = "https://bettereducation.com.au/Results/vce.aspx"
        resp = requests.get(url, headers=headers, timeout=30)

        resp.raise_for_status()

        tables = pd.read_html(io.StringIO(resp.text))  # no match -> gets all tables

        school_rank_df = tables[1].copy()
        # make the Better Education Rank columns go from 1 to 100 including every number in between
        school_rank_df["Better Education Rank"] = range(1, 101)

        return school_rank_df

    def add_school_rankings(self, schools_df, school_rank_df):
        """
        Add school rankings to the schools dataframe.

        Args:
            schools_df (pd.DataFrame): Schools dataframe
            school_rank_df (pd.DataFrame): School rankings dataframe

        Returns:
            pd.DataFrame: Schools dataframe with rankings added
        """
        import re
        from difflib import get_close_matches

        # Process school rankings
        school_rank_df.columns = [c.lower().strip() for c in school_rank_df.columns]
        school_rank_df = school_rank_df.rename(
            columns={
                "better education rank": "vic_secondary_rank",
                "school": "school_name",
            }
        )
        school_rank_df["school_name"] = school_rank_df["school_name"].str.strip()
        school_rank_df = school_rank_df[
            pd.to_numeric(school_rank_df["vic_secondary_rank"], errors="coerce").notna()
        ]
        school_rank_df["vic_secondary_rank"] = school_rank_df[
            "vic_secondary_rank"
        ].astype(int)

        def normalize(name: str) -> str:
            if not isinstance(name, str):
                return ""
            cleaned = name.lower().replace("'", "'").replace("–", "-").strip()
            # drop everything after the first comma (suburb/campus info)
            cleaned = cleaned.split(",", 1)[0]
            cleaned = re.sub(r"\s+", " ", cleaned)
            return cleaned

        # ranking table
        school_rank_df["name_norm"] = school_rank_df["school_name"].map(normalize)
        lookup_norm = dict(
            zip(school_rank_df["name_norm"], school_rank_df["vic_secondary_rank"])
        )

        # schools.csv
        schools_df["school_name_norm"] = schools_df["school_name"].map(normalize)

        def lookup_fuzzy(name, candidates, cutoff=0.8):
            matches = get_close_matches(name, candidates, n=1, cutoff=cutoff)
            return matches[0] if matches else None

        candidate_names = list(lookup_norm.keys())

        def assign_rank(row):
            rank = lookup_norm.get(row["school_name_norm"])
            if rank is None:
                # try fuzzy match against known names (casefolded) and goes both way for better matching
                match = lookup_fuzzy(
                    row["school_name_norm"], candidate_names, cutoff=0.85
                )
                if match:
                    rank = lookup_norm[match]
            school_type = row["school_type"].strip().lower()
            if rank:
                return rank
            if school_type not in {"secondary", "pri/sec"}:
                return None
            return 101

        schools_df["vic_secondary_rank"] = schools_df.apply(assign_rank, axis=1)
        schools_df = schools_df.drop(columns=["school_name_norm"])

        return schools_df

    def calculate_school_goodness(self, schools_df):
        """
        Calculate school goodness scores based on rankings.

        Args:
            schools_df (pd.DataFrame): Schools dataframe with rankings

        Returns:
            pd.DataFrame: Schools dataframe with goodness scores
        """
        import numpy as np

        eps = 0.0001

        # make a school goodness column based on the vic_secondary_rank
        def school_goodness(rank):
            if pd.isna(rank):
                return "N/A"
            else:
                goodness = 1 - (
                    np.log(rank) / (np.log(101)) + eps
                )  # Normalized log rank
                return round(goodness, 4)

        schools_df["school_goodness"] = schools_df["vic_secondary_rank"].map(
            school_goodness
        )

        return schools_df

    def find_best_schools_per_isochrone(self, listings_gdf, schools_gdf, iso_columns):
        """
        Find the best school for each isochrone based on spatial analysis.

        Args:
            listings_gdf (gpd.GeoDataFrame): Listings with isochrones
            schools_gdf (gpd.GeoDataFrame): Schools data
            iso_columns (list): List of isochrone column names

        Returns:
            gpd.GeoDataFrame: Listings with best school features added
        """
        import geopandas as gpd
        from pyproj import Geod
        from shapely import wkt, ops

        def safe_wkt(value):
            if pd.isna(value):
                return None
            value = str(value).strip()
            if not value:
                return None
            try:
                return wkt.loads(value)
            except Exception:
                return None

        def to_geom(val):
            if isinstance(val, str):
                cleaned = val.strip()
                if cleaned.lower() in {"", "nan", "none"}:
                    return None
                return wkt.loads(cleaned)
            if pd.isna(val):
                return None
            return val  # already a geometry

        def clean_geom_cell(val):
            if isinstance(val, str) and val.strip().lower() in {"", "nan", "none"}:
                return pd.NA
            if pd.isna(val):
                return pd.NA
            return val

        def swap_axes(geom):
            return ops.transform(lambda x, y, z=None: (y, x), geom)

        # Process isochrone columns
        for col in iso_columns:
            listings_gdf[col] = listings_gdf[col].map(safe_wkt)

        for col in iso_columns:
            listings_gdf[f"geom_{col}"] = listings_gdf[col].apply(to_geom)

        listings_gdf["year"] = listings_gdf["year"].astype("Int64")

        schools_gdf["establishment_year"] = (
            pd.to_numeric(schools_gdf["establishment_year"], errors="coerce")
            .round()
            .astype("Int64")  # null-friendly
        )
        schools_gdf["geometry"] = schools_gdf["coordinates"].apply(safe_wkt)
        schools_gdf["coordinates"] = schools_gdf["coordinates"].apply(safe_wkt)
        schools_gdf = gpd.GeoDataFrame(
            schools_gdf, geometry="geometry", crs="EPSG:4326"
        )

        geod = Geod(ellps="WGS84")
        beta = 0.2  # equivalent to lambda = 1/ beta

        def score_row(goodness, dist_km):
            return goodness / (1 + beta * dist_km)

        all_results = []
        iso_columns2 = [
            c for c in iso_columns if c.endswith("min") and "geom_" not in c
        ]

        for col in iso_columns2:
            poly_col = f"geom_{col}"
            # activate polygon geometry and drop rows without polygons
            iso_poly = listings_gdf.set_geometry(poly_col)
            iso_poly = iso_poly[iso_poly[poly_col].notna()]
            iso_poly = iso_poly.set_crs(
                "EPSG:4326", allow_override=True
            )  # define if missing

            # spatial join: schools inside polygon (keep listing_point column intact)
            joined = gpd.sjoin(
                iso_poly,
                schools_gdf,
                how="left",
                predicate="covers",
                rsuffix="school",
            )

            # only keep schools that existed by first_listed_year (or unknown year)
            mask = joined["establishment_year"].isna() | (
                joined["establishment_year"] <= joined["year"]
            )
            joined = joined[mask]

            if not joined.empty:
                # geodesic distance from listing point to school
                lon1 = joined["listing_point"].apply(lambda g: g.x).values
                lat1 = joined["listing_point"].apply(lambda g: g.y).values
                lon2 = gpd.GeoSeries(joined["coordinates_school"]).x
                lat2 = gpd.GeoSeries(joined["coordinates_school"]).y
                _, _, dists_m = geod.inv(lon1, lat1, lon2, lat2)
                joined["dist_km"] = dists_m / 1000.0

                joined["school_goodness"] = pd.to_numeric(
                    joined["school_goodness"], errors="coerce"
                )
                joined["dist_km"] = pd.to_numeric(joined["dist_km"], errors="coerce")

                valid = joined["school_goodness"].notna() & joined["dist_km"].notna()
                joined["score"] = pd.NA
                joined.loc[valid, "score"] = score_row(
                    joined.loc[valid, "school_goodness"], joined.loc[valid, "dist_km"]
                )

                # a count of how many schools within a given isochrone
                count = (
                    joined.groupby("property_id")["school_name"]
                    .count()  # counts rows in each group
                    .rename(f"n_schools_{col}")  # e.g., n_schools_driving_5min
                    .to_frame()
                )

                best_inside = (
                    joined.dropna(subset=["score"])
                    .sort_values("score", ascending=False)
                    .groupby("property_id")
                    .head(1)
                    .set_index("property_id")
                )

                # build out indexed by property_id
                out = (
                    iso_poly[["property_id"]].drop_duplicates().set_index("property_id")
                )
                for c in [
                    f"best_school_name_{col}",
                    f"best_school_coord_{col}",
                    f"best_score_{col}",
                    f"best_dist_km_{col}",
                ]:
                    out[c] = None

                if not best_inside.empty:
                    idx = best_inside.index
                    out.loc[idx, f"best_school_name_{col}"] = best_inside[
                        "school_name"
                    ].to_numpy()
                    out.loc[idx, f"best_school_coord_{col}"] = best_inside[
                        "coordinates_school"
                    ].to_numpy()
                    out.loc[idx, f"best_score_{col}"] = best_inside["score"].to_numpy()
                    out.loc[idx, f"best_dist_km_{col}"] = best_inside[
                        "dist_km"
                    ].to_numpy()

                # join back to listings_gdf by property_id
                all_results.append(out)
                all_results.append(count)

        final_out = pd.concat(
            all_results, axis=1
        )  # columns are already unique per {col}
        overlap = final_out.columns.intersection(listings_gdf.columns)
        listings_gdf = listings_gdf.drop(columns=overlap, errors="ignore").join(
            final_out, on="property_id"
        )

        return listings_gdf

    def impute_missing_school_features(self, listings_gdf):
        """
        Impute missing school features using nearest neighbour logic.

        Args:
            listings_gdf (gpd.GeoDataFrame): Listings with school features

        Returns:
            gpd.GeoDataFrame: Listings with imputed school features
        """
        fields = ["best_school_name", "best_school_coord", "best_score", "best_dist_km"]

        def all_fields_present(df, token):
            mode, dur = token.split("_", 1)
            cols = [
                f"{f}_{mode}_{dur}" for f in fields if f"{f}_{mode}_{dur}" in df.columns
            ]
            if not cols:
                return pd.Series(False, index=df.index)
            return df[cols].notna().all(axis=1)

        # availability for every token we might touch
        tokens = [
            "walking_5min",
            "walking_10min",
            "walking_15min",
            "driving_5min",
            "driving_10min",
            "driving_15min",
        ]
        avail = {tok: all_fields_present(listings_gdf, tok) for tok in tokens}

        # per-target fallback order
        fallback = {
            "walking_5min": [
                "walking_10min",
                "walking_15min",
                "driving_5min",
                "driving_10min",
                "driving_15min",
            ],
            "walking_10min": [
                "walking_15min",
                "driving_5min",
                "driving_10min",
                "driving_15min",
            ],
            "walking_15min": ["driving_5min", "driving_10min", "driving_15min"],
            "driving_5min": ["driving_10min", "driving_15min"],
            "driving_10min": ["driving_5min", "driving_15min"],
            "driving_15min": ["driving_10min", "driving_5min"],
        }

        for target in [
            "walking_5min",
            "walking_10min",
            "driving_5min",
            "driving_10min",
            "driving_15min",
        ]:
            mode_tgt, dur_tgt = target.split("_", 1)
            target_cols = [
                f"{f}_{mode_tgt}_{dur_tgt}"
                for f in fields
                if f"{f}_{mode_tgt}_{dur_tgt}" in listings_gdf.columns
            ]
            if not target_cols:
                continue

            missing = listings_gdf[target_cols].isna().all(axis=1)
            filled = pd.Series(False, index=listings_gdf.index)

            for candidate in fallback.get(target, []):
                rows = missing & avail[candidate] & ~filled
                if not rows.any():
                    continue

                mode_src, dur_src = candidate.split("_", 1)
                for f in fields:
                    src_col = f"{f}_{mode_src}_{dur_src}"
                    tgt_col = f"{f}_{mode_tgt}_{dur_tgt}"
                    if (
                        src_col in listings_gdf.columns
                        and tgt_col in listings_gdf.columns
                    ):
                        listings_gdf.loc[rows, tgt_col] = listings_gdf.loc[
                            rows, src_col
                        ].values

                tgt_cnt = f"n_schools_{mode_tgt}_{dur_tgt}"
                src_cnt = f"n_schools_{mode_src}_{dur_src}"
                if tgt_cnt in listings_gdf.columns and src_cnt in listings_gdf.columns:
                    need = rows & listings_gdf[tgt_cnt].fillna(0).eq(0)
                    listings_gdf.loc[need, tgt_cnt] = listings_gdf.loc[
                        need, src_cnt
                    ].values

                filled |= rows  # stop once we copy from the first available candidate

        return listings_gdf

    def finalize_school_features(self, listings_gdf):
        """
        Finalize school features by filling remaining missing values.

        Args:
            listings_gdf (gpd.GeoDataFrame): Listings with school features

        Returns:
            gpd.GeoDataFrame: Listings with finalized school features
        """
        score_cols = [c for c in listings_gdf.columns if c.startswith("best_score_")]
        listings_gdf[score_cols] = listings_gdf[score_cols].fillna(
            3e-8
        )  # Justification can be asked by venura(formula with reasonably max args)
        dist_cols = [c for c in listings_gdf.columns if c.startswith("best_dist_km_")]
        for col in dist_cols:
            max_val = listings_gdf[col].max(skipna=True)
            listings_gdf[col] = listings_gdf[col].fillna(
                max_val + 1 if pd.notna(max_val) else 1.0
            )

        count_cols = [c for c in listings_gdf.columns if c.startswith("n_schools_")]
        listings_gdf[count_cols] = listings_gdf[count_cols].fillna(0)

        return listings_gdf

    def process_school_features_workflow(
        self, listings_gdf, schools_dir="../data/landing/schools"
    ):
        """
        Complete workflow to process school features for listings.

        Args:
            listings_gdf (gpd.GeoDataFrame): Listings with isochrones
            schools_dir (str): Directory containing school CSV files

        Returns:
            gpd.GeoDataFrame: Listings with school features added
        """
        print("=== PROCESSING SCHOOL FEATURES ===")

        # Step 1: Process school data
        print("Step 1: Processing school data...")
        schools_df = self.process_school_data(schools_dir)

        # Step 2: Scrape and add rankings
        print("Step 2: Adding school rankings...")
        school_rank_df = self.scrape_school_rankings()
        schools_df = self.add_school_rankings(schools_df, school_rank_df)

        # Step 3: Calculate school goodness scores
        print("Step 3: Calculating school goodness scores...")
        schools_df = self.calculate_school_goodness(schools_df)

        # Step 4: Find best schools per isochrone
        print("Step 4: Finding best schools per isochrone...")
        iso_columns = [
            c
            for c in listings_gdf.columns
            if c.endswith("min_imputed") or c.endswith("min")
        ]
        listings_gdf = self.find_best_schools_per_isochrone(
            listings_gdf, schools_df, iso_columns
        )

        # Step 5: Impute missing school features
        print("Step 5: Imputing missing school features...")
        listings_gdf = self.impute_missing_school_features(listings_gdf)

        # Step 6: Finalize school features
        print("Step 6: Finalizing school features...")
        listings_gdf = self.finalize_school_features(listings_gdf)

        print("School features processing completed!")

        return listings_gdf
