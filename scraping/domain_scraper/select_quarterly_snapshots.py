#!/usr/bin/env python3
"""
Script to select nearest quarterly snapshots from suburb_snapshots_2022_2025.csv

This script reads the suburb snapshots CSV and selects the nearest snapshot
per quarter (March, June, September, December) from 2022 to 2025 for each suburb.
Output is a CSV with suburbs as rows and quarters as columns.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys
import os


def parse_timestamp(timestamp_str):
    """Parse timestamp string in format YYYYMMDDHHMMSS to datetime"""
    try:
        return datetime.strptime(str(timestamp_str), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def get_quarter_target_dates():
    """Get target dates for each quarter from 2022 to 2025"""
    target_dates = {}

    for year in range(2022, 2026):  # 2022 to 2025 inclusive
        for month in [3, 6, 9, 12]:  # Mar, Jun, Sep, Dec
            # Use the 15th of each month as the target date
            target_date = datetime(year, month, 15)
            quarter_name = f"{year}_Q{((month-1)//3)+1}"
            target_dates[quarter_name] = target_date

    return target_dates


def find_nearest_snapshot(snapshots_df, target_date, max_days_diff=45):
    """
    Find the nearest snapshot to the target date within max_days_diff days

    Args:
        snapshots_df: DataFrame with timestamp column
        target_date: datetime target date
        max_days_diff: maximum days difference to consider (default 45 days)

    Returns:
        timestamp string if found, None otherwise
    """
    if snapshots_df.empty:
        return None

    # Calculate days difference for each snapshot
    snapshots_df = snapshots_df.copy()
    snapshots_df["days_diff"] = (snapshots_df["datetime"] - target_date).dt.days.abs()

    # Filter to snapshots within acceptable range
    valid_snapshots = snapshots_df[snapshots_df["days_diff"] <= max_days_diff]

    if valid_snapshots.empty:
        return None

    # Return the timestamp of the closest snapshot
    closest_idx = valid_snapshots["days_diff"].idxmin()
    return snapshots_df.loc[closest_idx, "timestamp"]


def process_quarterly_snapshots(input_file, output_file=None):
    """
    Process the suburb snapshots CSV to select nearest quarterly snapshots

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional)
    """

    print(f"Reading data from {input_file}...")

    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

    print(f"Loaded {len(df)} records")

    # Parse timestamps to datetime
    df["datetime"] = df["timestamp"].apply(parse_timestamp)

    # Remove rows with invalid timestamps
    invalid_timestamps = df["datetime"].isna().sum()
    if invalid_timestamps > 0:
        print(f"Warning: Found {invalid_timestamps} records with invalid timestamps")
        df = df.dropna(subset=["datetime"])

    print(f"Processing {len(df)} valid records")

    # Get target dates for each quarter
    target_dates = get_quarter_target_dates()
    print(f"Looking for snapshots near {len(target_dates)} quarterly targets")

    # Group by suburb and postcode
    grouped = df.groupby(["suburb", "postcode"])

    results = []

    print("Processing suburbs...")
    for (suburb, postcode), group_df in grouped:
        result_row = {"suburb": suburb, "postcode": postcode}

        # Find nearest snapshot for each quarter
        for quarter_name, target_date in target_dates.items():
            nearest_timestamp = find_nearest_snapshot(group_df, target_date)
            result_row[quarter_name] = nearest_timestamp

        results.append(result_row)

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Sort by suburb and postcode
    results_df = results_df.sort_values(["suburb", "postcode"])

    print(f"Found quarterly snapshots for {len(results_df)} suburbs")

    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}_quarterly_snapshots.csv"

    # Save to CSV
    try:
        results_df.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")

        # Print summary statistics
        print("\nSummary:")
        print(f"Total suburbs: {len(results_df)}")

        for quarter in target_dates.keys():
            non_null_count = results_df[quarter].notna().sum()
            print(f"{quarter}: {non_null_count} suburbs with snapshots")

        return True

    except Exception as e:
        print(f"Error saving results: {e}")
        return False


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Select nearest quarterly snapshots from suburb snapshots CSV"
    )
    parser.add_argument(
        "input_file", help="Path to input CSV file (suburb_snapshots_2022_2025.csv)"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output CSV file (default: input_filename_quarterly_snapshots.csv)",
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)

    # Process the data
    success = process_quarterly_snapshots(args.input_file, args.output)

    if success:
        print("Processing completed successfully!")
        sys.exit(0)
    else:
        print("Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
