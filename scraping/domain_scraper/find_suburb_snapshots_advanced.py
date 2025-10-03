#!/usr/bin/env python3
"""
Advanced script to find available Wayback Machine snapshots for all Victorian suburbs
Uses the CDX API to find snapshots between 2022-2025, with advanced filtering and options

Features:
- Finds one snapshot per month for each suburb
- Filters by specific months if desired
- Saves results in multiple formats (CSV, JSON)
- Includes progress tracking and error handling
- Can resume from where it left off
- Generates summary statistics

Usage:
    python find_suburb_snapshots_advanced.py [--months 3,6,9,12] [--resume] [--test]
"""

import os
import sys
import csv
import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
import pandas as pd
from typing import List, Dict, Optional


class SuburbSnapshotFinder:
    def __init__(self, start_year=2022, end_year=2025, target_months=None):
        self.start_year = start_year
        self.end_year = end_year
        self.target_months = target_months or list(
            range(1, 13)
        )  # All months by default
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    def load_suburb_data(self) -> List[Dict[str, str]]:
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

    def get_wayback_snapshots(self, suburb: str, postcode: str) -> List[Dict[str, str]]:
        """
        Get available snapshots for a suburb using Wayback Machine CDX API
        Returns one snapshot per target month if available
        """
        # Construct the search URL for Domain rental listings
        search_url = f"https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}"

        # Use Wayback Machine's CDX API to find available snapshots
        cdx_url = f"https://web.archive.org/cdx/search/cdx"

        params = {
            "url": search_url,
            "output": "json",
            "from": f"{self.start_year}0101000000",
            "to": f"{self.end_year}1231235959",
            "filter": "statuscode:200",  # Only successful captures
            "limit": 10000,  # Higher limit for more comprehensive results
        }

        try:
            print(f"  Base URL: {search_url}")
            response = self.session.get(cdx_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data or len(data) <= 1:  # Empty or just headers
                print(f"  No snapshots found for {suburb} (URL: {search_url})")
                return []

            # Skip header row
            snapshots = data[1:]

            # Process snapshots to get one per target month
            monthly_snapshots = {}
            for snapshot in snapshots:
                if len(snapshot) >= 3:
                    timestamp = snapshot[1]
                    original_url = snapshot[2]

                    # Extract year-month from timestamp (YYYYMMDDHHMMSS)
                    year = int(timestamp[:4])
                    month = int(timestamp[4:6])

                    # Only include if month is in target months
                    if month in self.target_months:
                        year_month = timestamp[:6]  # YYYYMM

                        # Keep only the first snapshot for each month
                        if year_month not in monthly_snapshots:
                            monthly_snapshots[year_month] = {
                                "timestamp": timestamp,
                                "url": original_url,
                                "wayback_url": f"https://web.archive.org/web/{timestamp}/{original_url}",
                                "year": year,
                                "month": month,
                            }

            # Convert to list and sort by timestamp
            result = list(monthly_snapshots.values())
            result.sort(key=lambda x: x["timestamp"])

            return result

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching snapshots for {suburb}: {e}")
            return []
        except Exception as e:
            print(f"  Unexpected error for {suburb}: {e}")
            return []

    def save_progress(self, processed_suburbs: List[str], output_file: str):
        """Save progress to resume later"""
        with open(output_file, "w") as f:
            json.dump(processed_suburbs, f)

    def load_progress(self, progress_file: str) -> List[str]:
        """Load previously processed suburbs"""
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                return json.load(f)
        return []

    def save_snapshots_to_csv(self, all_snapshots: List[Dict], output_file: str):
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
                        "year": snapshot["year"],
                        "month": snapshot["month"],
                        "original_url": snapshot["url"],
                        "wayback_url": snapshot["wayback_url"],
                    }
                )

        # Save to CSV
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_file, index=False)
        print(f"Saved {len(flattened_data)} snapshots to {output_file}")

    def save_snapshots_to_json(self, all_snapshots: List[Dict], output_file: str):
        """Save all snapshots to a JSON file"""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_snapshots, f, indent=2, ensure_ascii=False)
        print(f"Saved snapshots to {output_file}")

    def generate_summary(self, all_snapshots: List[Dict]):
        """Generate and print summary statistics"""
        if not all_snapshots:
            print("No snapshots found.")
            return

        total_snapshots = sum(len(sub["snapshots"]) for sub in all_snapshots)

        print(f"\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)
        print(f"Total suburbs with snapshots: {len(all_snapshots)}")
        print(f"Total snapshots found: {total_snapshots}")
        print(f"Average snapshots per suburb: {total_snapshots/len(all_snapshots):.1f}")

        # Show date range
        all_timestamps = []
        for sub in all_snapshots:
            for snap in sub["snapshots"]:
                all_timestamps.append(snap["timestamp"])

        if all_timestamps:
            all_timestamps.sort()
            earliest = all_timestamps[0]
            latest = all_timestamps[-1]
            print(f"Date range: {earliest[:8]} to {latest[:8]}")

        # Show distribution by year
        year_counts = {}
        month_counts = {}
        for sub in all_snapshots:
            for snap in sub["snapshots"]:
                year = snap["year"]
                month = snap["month"]
                year_counts[year] = year_counts.get(year, 0) + 1
                month_counts[month] = month_counts.get(month, 0) + 1

        print(f"\nSnapshots by year:")
        for year in sorted(year_counts.keys()):
            print(f"  {year}: {year_counts[year]} snapshots")

        print(f"\nSnapshots by month:")
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        for month in sorted(month_counts.keys()):
            print(
                f"  {month_names[month-1]} ({month:02d}): {month_counts[month]} snapshots"
            )

        # Show top suburbs by snapshot count
        suburb_counts = [
            (sub["suburb"], len(sub["snapshots"])) for sub in all_snapshots
        ]
        suburb_counts.sort(key=lambda x: x[1], reverse=True)

        print(f"\nTop 10 suburbs by snapshot count:")
        for i, (suburb, count) in enumerate(suburb_counts[:10], 1):
            print(f"  {i:2d}. {suburb}: {count} snapshots")

        # Show URLs with no snapshots for validation
        if hasattr(self, "no_snapshots_urls") and self.no_snapshots_urls:
            print(f"\nURLs with no snapshots found ({len(self.no_snapshots_urls)}):")
            for item in self.no_snapshots_urls[:10]:  # Show first 10
                print(f"  {item['suburb']} ({item['postcode']}): {item['url']}")
            if len(self.no_snapshots_urls) > 10:
                print(f"  ... and {len(self.no_snapshots_urls) - 10} more")

    def run(self, test_mode=False, resume=False):
        """Main function to find snapshots for all suburbs"""
        print("Starting advanced suburb snapshot discovery...")
        print("=" * 60)
        print(f"Target years: {self.start_year}-{self.end_year}")
        print(f"Target months: {self.target_months}")
        print("=" * 60)

        # Load suburb data
        suburbs = self.load_suburb_data()
        if not suburbs:
            print("No suburbs loaded. Exiting.")
            return

        # Test mode - limit suburbs
        if test_mode:
            suburbs = suburbs[:20]  # Test with first 20 suburbs
            print(f"TEST MODE: Processing only {len(suburbs)} suburbs")

        # Setup output directory
        output_dir = Path(__file__).parent / "data" / "snapshots"
        output_dir.mkdir(parents=True, exist_ok=True)

        progress_file = output_dir / "progress.json"
        processed_suburbs = []

        # Resume from previous run if requested
        if resume:
            processed_suburbs = self.load_progress(progress_file)
            print(
                f"Resuming from previous run. Skipping {len(processed_suburbs)} already processed suburbs."
            )

        all_snapshots = []
        no_snapshots_urls = []  # Track URLs with no snapshots
        total_suburbs = len(suburbs)
        start_index = len(processed_suburbs)

        for i, suburb_data in enumerate(suburbs[start_index:], start_index + 1):
            suburb = suburb_data["suburb"]
            postcode = suburb_data["postcode"]

            print(f"\n[{i}/{total_suburbs}] Processing {suburb} ({postcode})")

            # Get snapshots for this suburb
            snapshots = self.get_wayback_snapshots(suburb, postcode)

            if snapshots:
                all_snapshots.append(
                    {"suburb": suburb, "postcode": postcode, "snapshots": snapshots}
                )
                print(f"  Found {len(snapshots)} snapshots")
            else:
                print(f"  No snapshots found")
                # Track URLs with no snapshots for validation
                search_url = f"https://www.domain.com.au/rent/{suburb.lower().replace(' ', '-')}-vic-{postcode}"
                no_snapshots_urls.append(
                    {"suburb": suburb, "postcode": postcode, "url": search_url}
                )

            # Track progress
            processed_suburbs.append(suburb)

            # Save progress every 50 suburbs
            if i % 50 == 0:
                self.save_progress(processed_suburbs, progress_file)
                print(f"\nProgress saved: {i}/{total_suburbs} suburbs processed")
                print(f"Found snapshots for {len(all_snapshots)} suburbs so far")

            # Add a delay to be respectful to the API and avoid rate limiting
            time.sleep(2.0)

        # Clean up progress file
        if os.path.exists(progress_file):
            os.remove(progress_file)

        print("\n" + "=" * 60)
        print("Snapshot discovery completed!")
        print(f"Processed {total_suburbs} suburbs")
        print(f"Found snapshots for {len(all_snapshots)} suburbs")

        # Save results
        if all_snapshots:
            # Save as CSV
            csv_file = (
                output_dir / f"suburb_snapshots_{self.start_year}_{self.end_year}.csv"
            )
            self.save_snapshots_to_csv(all_snapshots, csv_file)

            # Save as JSON
            json_file = (
                output_dir / f"suburb_snapshots_{self.start_year}_{self.end_year}.json"
            )
            self.save_snapshots_to_json(all_snapshots, json_file)

            # Generate summary
            self.no_snapshots_urls = no_snapshots_urls  # Store for summary
            self.generate_summary(all_snapshots)
        else:
            print("No snapshots found for any suburbs.")


def main():
    parser = argparse.ArgumentParser(
        description="Find Wayback Machine snapshots for Victorian suburbs"
    )
    parser.add_argument(
        "--months", type=str, help="Comma-separated list of months to target (1-12)"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from previous run"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode (process only first 20 suburbs)"
    )
    parser.add_argument(
        "--start-year", type=int, default=2022, help="Start year (default: 2022)"
    )
    parser.add_argument(
        "--end-year", type=int, default=2025, help="End year (default: 2025)"
    )

    args = parser.parse_args()

    # Parse target months
    target_months = None
    if args.months:
        try:
            target_months = [int(m.strip()) for m in args.months.split(",")]
            if not all(1 <= m <= 12 for m in target_months):
                print("Error: Months must be between 1 and 12")
                return
        except ValueError:
            print(
                "Error: Invalid months format. Use comma-separated numbers (e.g., 3,6,9,12)"
            )
            return

    # Create finder and run
    finder = SuburbSnapshotFinder(
        start_year=args.start_year, end_year=args.end_year, target_months=target_months
    )

    finder.run(test_mode=args.test, resume=args.resume)


if __name__ == "__main__":
    main()
