#!/usr/bin/env python3
"""
Run domain spider for all quarters in reverse chronological order
From 2025_Q2 down to 2022_Q3
"""

import pandas as pd
import os
import subprocess
import sys
import time
from datetime import datetime


def get_quarter_columns():
    """Get all quarter columns in reverse chronological order (2025_Q2 to 2022_Q3), excluding 2025_Q3"""
    quarters = []

    # Generate quarters from 2025_Q2 down to 2022_Q3, excluding 2025_Q3
    for year in range(2025, 2021, -1):  # 2025, 2024, 2023, 2022
        for q in range(4, 0, -1):  # Q4, Q3, Q2, Q1
            quarter_col = f"{year}_Q{q}"
            # Skip 2025_Q3 as requested
            if quarter_col == "2025_Q3":
                continue
            quarters.append(quarter_col)

    return quarters


def get_quarter_filename(quarter_col):
    """Convert quarter column to filename format"""
    year = quarter_col.split("_")[0]
    quarter = quarter_col.split("_")[1]

    # Map quarter to month
    month_map = {"Q1": "03", "Q2": "06", "Q3": "09", "Q4": "12"}
    month = month_map[quarter]

    return f"rental_listings_{year}_{month}.csv"


def consolidate_csv_files(input_files, output_file):
    """Consolidate multiple CSV files into one clean file"""
    import csv

    if not input_files:
        return

    # Read all files and combine data
    all_data = []
    header_written = False

    for file_path in input_files:
        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Use the first file's header
                if not header_written:
                    fieldnames = reader.fieldnames
                    header_written = True

                # Add all rows from this file
                for row in reader:
                    all_data.append(row)

        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")

    # Write consolidated data
    if all_data and header_written:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"✅ Consolidated {len(all_data)} listings into {output_file}")
    else:
        print("❌ No data to consolidate")


def run_spider_for_quarter(quarter_col, df):
    """Run the spider for a specific quarter"""
    print(f"\n{'='*80}")
    print(f"🕐 Processing {quarter_col}")
    print(f"{'='*80}")

    # Filter suburbs with timestamps for this quarter
    quarter_data = df[df[quarter_col].notna() & (df[quarter_col] != "")].copy()

    if quarter_data.empty:
        print(f"⏭️  No data available for {quarter_col}")
        return False

    print(f"📊 Found {len(quarter_data)} suburbs with timestamps for {quarter_col}")

    # Create output filename
    filename = get_quarter_filename(quarter_col)
    output_path = f"../../data/raw/domain/{filename}"

    print(f"📁 Output file: {output_path}")

    # Create a temporary directory for individual suburb files
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()

    # Run spider for each suburb with its specific timestamp
    successful_runs = 0
    failed_runs = 0
    total_listings_this_quarter = 0
    all_listings = []

    for i, (idx, row) in enumerate(quarter_data.iterrows(), 1):
        suburb = row["suburb"]
        postcode = row["postcode"]
        timestamp = row[quarter_col]
        timestamp_str = str(int(float(timestamp)))

        print(
            f"\n--- Suburb {i}/{len(quarter_data)}: {suburb} ({postcode}) - {timestamp_str} ---"
        )

        # Create individual output file for this suburb
        temp_output = os.path.join(temp_dir, f"{suburb}_{postcode}_{timestamp_str}.csv")

        # Run the spider with specific suburb and timestamp
        cmd = [
            "scrapy",
            "crawl",
            "wayback_domain_rental",
            "-a",
            f"wayback_timestamp={timestamp_str}",
            "-a",
            f"target_suburb={suburb}",
            "-a",
            f"target_postcode={postcode}",
            "-a",
            f"output_file={temp_output}",
            "--loglevel=INFO",
        ]

        print(f"Running command: {' '.join(cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            end_time = time.time()
            duration = end_time - start_time

            if result.returncode == 0:
                print(f"✅ Spider completed successfully in {duration:.1f} seconds")
                successful_runs += 1

                # Check output file and count listings
                if os.path.exists(temp_output):
                    file_size = os.path.getsize(temp_output)
                    print(f"📁 Output file size: {file_size:,} bytes")

                    # Count listings in the CSV file (subtract 1 for header)
                    try:
                        with open(temp_output, "r") as f:
                            lines = f.readlines()
                            line_count = len(lines) - 1  # Subtract header
                        print(f"📊 Listings scraped for {suburb}: {line_count}")
                        total_listings_this_quarter += line_count

                        # Store the data for later consolidation
                        if line_count > 0:
                            all_listings.append(temp_output)
                    except Exception as e:
                        print(f"⚠️ Could not count listings: {e}")
                else:
                    print("❌ Output file was not created")
            else:
                print(f"❌ Spider failed with return code {result.returncode}")
                print(f"Error output: {result.stderr}")
                failed_runs += 1

        except Exception as e:
            print(f"❌ Error running spider: {e}")
            failed_runs += 1

        # Add delay between runs (except for the last one)
        if i < len(quarter_data):
            print("⏳ Waiting 1 seconds before next suburb...")
            time.sleep(1)

    # Consolidate all individual files into one clean CSV
    if all_listings:
        print(f"\n🔄 Consolidating {len(all_listings)} suburb files into {output_path}")
        consolidate_csv_files(all_listings, output_path)

        # Clean up temporary files
        shutil.rmtree(temp_dir)

        # Final count
        try:
            with open(output_path, "r") as f:
                final_count = sum(1 for line in f) - 1  # Subtract header
            print(f"📊 Final consolidated file: {final_count} listings")
        except Exception as e:
            print(f"⚠️ Could not count final listings: {e}")
    else:
        print("❌ No data files to consolidate")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    # Summary for this quarter
    print(f"\n📊 {quarter_col} Summary:")
    print(f"   Suburbs with data: {len(quarter_data)}")
    print(f"   Successful runs: {successful_runs}")
    print(f"   Failed runs: {failed_runs}")
    print(f"   Total listings scraped: {total_listings_this_quarter}")
    print(f"   Output file: {output_path}")

    return successful_runs > 0


def main():
    """Main function to process all quarters"""
    print("🚀 Starting quarterly domain scraping in reverse chronological order...")
    print("📅 Processing quarters from 2025_Q2 down to 2022_Q3 (excluding 2025_Q3)")

    # Load the suburb snapshots data
    csv_path = "data/snapshots/suburb_snapshots_2022_2025_quarterly_snapshots.csv"

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    print(f"📂 Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(df)} suburb records")

    # Get all quarters in reverse chronological order
    quarters = get_quarter_columns()
    print(f"📅 Processing {len(quarters)} quarters: {', '.join(quarters)}")

    # Process each quarter
    results = []
    start_time = time.time()

    for i, quarter_col in enumerate(quarters, 1):
        print(f"\n🔄 Progress: {i}/{len(quarters)} quarters")

        success = run_spider_for_quarter(quarter_col, df)
        results.append({"quarter": quarter_col, "success": success})

        # Add delay between quarters (except for the last one)
        if i < len(quarters):
            print("⏳ Waiting 1 seconds before next quarter...")
            time.sleep(1)

    # Final summary
    end_time = time.time()
    total_duration = end_time - start_time
    total_duration_hours = total_duration / 3600

    print(f"\n{'='*80}")
    print("🎯 FINAL SUMMARY")
    print(f"{'='*80}")

    successful_quarters = [r for r in results if r["success"]]
    failed_quarters = [r for r in results if not r["success"]]

    print(f"📊 Total quarters processed: {len(results)}")
    print(f"✅ Successful quarters: {len(successful_quarters)}")
    print(f"❌ Failed quarters: {len(failed_quarters)}")
    print(f"⏱️  Total duration: {total_duration_hours:.2f} hours")

    if successful_quarters:
        print(f"\n✅ Successfully processed quarters:")
        for result in successful_quarters:
            print(f"  - {result['quarter']}")

    if failed_quarters:
        print(f"\n❌ Failed quarters:")
        for result in failed_quarters:
            print(f"  - {result['quarter']}")

    print(f"\n📁 Output files saved to: ../../data/raw/domain/")
    print("✅ Quarterly scraping completed!")


if __name__ == "__main__":
    main()
