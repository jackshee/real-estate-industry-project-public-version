#!/usr/bin/env python3
"""
Script to run the Domain rental spider and save results to CSV
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Change to the domain_scraper directory
    os.chdir(script_dir)

    # Define the output file path (relative to project root)
    output_file = "../../data/landing/domain/live/rental_listings_2025_09.csv"

    # Ensure the output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the scrapy command using the virtual environment
    venv_python = "../../venv/bin/python"
    cmd = [
        venv_python,
        "-m",
        "scrapy",
        "crawl",
        "domain_rental",
        "-o",
        output_file,
        "-L",
        "INFO",  # Set log level to INFO for cleaner output
    ]

    print(f"Running spider with command: {' '.join(cmd)}")
    print(f"Output will be saved to: {output_file}")
    print("=" * 60)

    try:
        # Run the spider
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("=" * 60)
        print("Spider completed successfully!")
        print(f"Results saved to: {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error running spider: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSpider interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
