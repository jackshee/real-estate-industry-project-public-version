#!/usr/bin/env python3
"""
Test script to verify the Domain rental spider works with a small subset
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

    # Define the output file path for testing
    output_file = "../../data/raw/domain/test_rental_listings.csv"

    # Ensure the output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the scrapy command with a small subset for testing using virtual environment
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
        "-s",
        "CLOSESPIDER_PAGECOUNT=5",  # Limit to 5 pages for testing
    ]

    print(f"Running spider test with command: {' '.join(cmd)}")
    print(f"Output will be saved to: {output_file}")
    print("This will process only the first 5 pages for testing")
    print("=" * 60)

    try:
        # Run the spider
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("=" * 60)
        print("Spider test completed successfully!")
        print(f"Test results saved to: {output_file}")

        # Check if file was created and has content
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"Output file size: {file_size} bytes")
            if file_size > 100:  # More than just headers
                print("✅ Test successful - file contains data")
            else:
                print("⚠️  Test completed but file may be empty or contain only headers")
        else:
            print("❌ Test failed - no output file created")

    except subprocess.CalledProcessError as e:
        print(f"Error running spider: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSpider test interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
