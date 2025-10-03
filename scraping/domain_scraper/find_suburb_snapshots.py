#!/usr/bin/env python3
"""
Script to find available Wayback Machine snapshots for all Victorian suburbs
Uses the CDX API to find snapshots between 2022-2025, saving one per month if available

Usage:
    python find_suburb_snapshots.py
"""

import os
import sys
import csv
import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
import pandas as pd


def load_suburb_data():
    """Load suburb and postcode data from CSV file"""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "data",
        "geo",
        "vic_suburbs_postcodes.csv",
    )

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return []

    suburbs = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["suburb"] and row["postcode"]:  # Skip empty rows
                suburbs.append(
                    {
                        "suburb": row["suburb"].strip(),
                        "postcode": row["postcode"].strip(),
                    }
                )

    print(f"Loaded {len(suburbs)} suburbs from CSV")
    return suburbs


def get_wayback_snapshots(suburb, postcode, start_year=2022, end_year=2025):
    """
    Get available snapshots for a suburb using Wayback Machine CDX API
    Returns one snapshot per month if available
    """
    # Construct the search URL for Domain rental listings
    search_url = f"https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}"

    # Use Wayback Machine's CDX API to find available snapshots
    cdx_url = f"https://web.archive.org/cdx/search/cdx"

    params = {
        "url": search_url,
        "output": "json",
        "from": f"{start_year}0101000000",  # Start from Jan 1, start_year
        "to": f"{end_year}1231235959",  # End at Dec 31, end_year
        "collapse": "timestamp:8",  # Collapse by month (YYYYMM)
        "filter": "statuscode:200",  # Only successful captures
        "limit": 1000,  # Reasonable limit
    }

    try:
        print(f"Searching snapshots for {suburb} ({postcode})...")
        print(f"  Base URL: {search_url}")

        # Add retry logic for network issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(cdx_url, params=params, timeout=30)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  Attempt {attempt + 1} failed, retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    raise e

        data = response.json()

        if not data or len(data) <= 1:  # Empty or just headers
            print(f"  No snapshots found for {suburb} (URL: {search_url})")
            return []

        # Skip header row
        snapshots = data[1:]

        # Process snapshots to get one per month
        monthly_snapshots = {}
        for snapshot in snapshots:
            if len(snapshot) >= 3:
                timestamp = snapshot[1]
                original_url = snapshot[2]

                # Extract year-month from timestamp (YYYYMMDDHHMMSS)
                year_month = timestamp[:6]  # YYYYMM

                # Keep only the first snapshot for each month
                if year_month not in monthly_snapshots:
                    monthly_snapshots[year_month] = {
                        "timestamp": timestamp,
                        "url": original_url,
                        "wayback_url": f"https://web.archive.org/web/{timestamp}/{original_url}",
                    }

        # Convert to list and sort by timestamp
        result = list(monthly_snapshots.values())
        result.sort(key=lambda x: x["timestamp"])

        print(f"  Found {len(result)} monthly snapshots for {suburb}")
        return result

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching snapshots for {suburb}: {e}")
        return []
    except Exception as e:
        print(f"  Unexpected error for {suburb}: {e}")
        return []


def save_snapshots_to_csv(all_snapshots, output_file):
    """Save all snapshots to a CSV file"""
    if not all_snapshots:
        print("No snapshots to save")
        return

    # Flatten the data for CSV
    flattened_data = []
    for suburb_data in all_snapshots:
        suburb = suburb_data["suburb"]
        postcode = suburb_data["postcode"]

        for snapshot in suburb_data["snapshots"]:
            # Parse timestamp to get readable date
            timestamp = snapshot["timestamp"]
            year = timestamp[:4]
            month = timestamp[4:6]
            day = timestamp[6:8]
            hour = timestamp[8:10]
            minute = timestamp[10:12]
            second = timestamp[12:14]

            readable_date = f"{year}-{month}-{day} {hour}:{minute}:{second}"

            flattened_data.append(
                {
                    "suburb": suburb,
                    "postcode": postcode,
                    "timestamp": timestamp,
                    "readable_date": readable_date,
                    "original_url": snapshot["url"],
                    "wayback_url": snapshot["wayback_url"],
                }
            )

    # Save to CSV
    df = pd.DataFrame(flattened_data)
    df.to_csv(output_file, index=False)
    print(f"Saved {len(flattened_data)} snapshots to {output_file}")


def save_snapshots_to_json(all_snapshots, output_file):
    """Save all snapshots to a JSON file"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_snapshots, f, indent=2, ensure_ascii=False)
    print(f"Saved snapshots to {output_file}")


def main():
    """Main function to find snapshots for all suburbs"""
    print("Starting suburb snapshot discovery...")
    print("=" * 50)

    # Load suburb data
    suburbs = load_suburb_data()
    if not suburbs:
        print("No suburbs loaded. Exiting.")
        return

    # Limit for testing (remove this for full run)
    # suburbs = suburbs[:10]  # Test with first 10 suburbs

    all_snapshots = []
    no_snapshots_urls = []  # Track URLs with no snapshots
    total_suburbs = len(suburbs)

    for i, suburb_data in enumerate(suburbs, 1):
        suburb = suburb_data["suburb"]
        postcode = suburb_data["postcode"]

        print(f"\n[{i}/{total_suburbs}] Processing {suburb} ({postcode})")

        # Get snapshots for this suburb
        snapshots = get_wayback_snapshots(suburb, postcode)

        if snapshots:
            all_snapshots.append(
                {"suburb": suburb, "postcode": postcode, "snapshots": snapshots}
            )
        else:
            # Track URLs with no snapshots for validation
            search_url = f"https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}"
            no_snapshots_urls.append(
                {"suburb": suburb, "postcode": postcode, "url": search_url}
            )

        # Add a delay to be respectful to the API and avoid rate limiting
        time.sleep(2.0)

        # Progress update every 50 suburbs
        if i % 50 == 0:
            print(f"\nProgress: {i}/{total_suburbs} suburbs processed")
            print(f"Found snapshots for {len(all_snapshots)} suburbs so far")

    print("\n" + "=" * 50)
    print("Snapshot discovery completed!")
    print(f"Processed {total_suburbs} suburbs")
    print(f"Found snapshots for {len(all_snapshots)} suburbs")

    # Save results
    if all_snapshots:
        output_dir = Path(__file__).parent / "data" / "snapshots"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as CSV
        csv_file = output_dir / "suburb_snapshots_2022_2025.csv"
        save_snapshots_to_csv(all_snapshots, csv_file)

        # Save as JSON
        json_file = output_dir / "suburb_snapshots_2022_2025.json"
        save_snapshots_to_json(all_snapshots, json_file)

        # Print summary statistics
        total_snapshots = sum(len(sub["snapshots"]) for sub in all_snapshots)
        print(f"\nSummary:")
        print(f"  Total suburbs with snapshots: {len(all_snapshots)}")
        print(f"  Total snapshots found: {total_snapshots}")
        print(
            f"  Average snapshots per suburb: {total_snapshots/len(all_snapshots):.1f}"
        )

        # Show date range
        all_timestamps = []
        for sub in all_snapshots:
            for snap in sub["snapshots"]:
                all_timestamps.append(snap["timestamp"])

        if all_timestamps:
            all_timestamps.sort()
            earliest = all_timestamps[0]
            latest = all_timestamps[-1]
            print(f"  Date range: {earliest[:8]} to {latest[:8]}")

        # Show URLs with no snapshots for validation
        if no_snapshots_urls:
            print(f"\nURLs with no snapshots found ({len(no_snapshots_urls)}):")
            for item in no_snapshots_urls[:10]:  # Show first 10
                print(f"  {item['suburb']} ({item['postcode']}): {item['url']}")
            if len(no_snapshots_urls) > 10:
                print(f"  ... and {len(no_snapshots_urls) - 10} more")
    else:
        print("No snapshots found for any suburbs.")


if __name__ == "__main__":
    main()
