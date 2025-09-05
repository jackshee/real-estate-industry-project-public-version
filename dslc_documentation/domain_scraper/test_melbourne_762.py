#!/usr/bin/env python3
"""
Test script to verify Melbourne has 762 listings with ?ssubs=0 parameter
"""

import subprocess
import json
import os
import sys
from pathlib import Path


def test_melbourne_762():
    """Test that Melbourne has exactly 762 listings with ?ssubs=0"""
    print("=== MELBOURNE 762 LISTINGS TEST ===")
    print("Testing Melbourne (3000) with ?ssubs=0 parameter...")
    print("Expected: 762 listings (based on Domain website)")

    # Change to the scraper directory
    scraper_dir = Path(__file__).parent

    # Clean up old log file
    log_file = scraper_dir / "scrapy.log"
    if log_file.exists():
        log_file.unlink()
        print("Cleaned up old scrapy.log file")
    os.chdir(scraper_dir)

    # Output file for this test
    output_file = "melbourne_762_test.json"

    # Remove existing output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    try:
        # Run the scraper with specific settings for Melbourne
        print("Running scraper for Melbourne...")
        cmd = [
            "scrapy",
            "crawl",
            "domain_rental",
            "-o",
            output_file,
            "-s",
            "CLOSESPIDER_ITEMCOUNT=1000",  # Stop after 1000 items
            "-L",
            "INFO",  # Set log level to INFO
        ]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )  # 10 minute timeout

        if result.returncode != 0:
            print(f"❌ FAILURE: Scraper failed with return code {result.returncode}")
            print("STDOUT:", result.stdout[-500:])  # Show last 500 chars
            print("STDERR:", result.stderr[-500:])  # Show last 500 chars
            return False

        print("✅ Scraper completed successfully!")

        # Check if output file was created
        if not os.path.exists(output_file):
            print(f"❌ FAILURE: Output file {output_file} was not created!")
            return False

        # Count listings
        with open(output_file, "r", encoding="utf-8") as f:
            listings = json.load(f)

        total_count = len(listings)
        print(f"Total listings scraped: {total_count}")

        # Check if we got the expected count
        if total_count == 762:
            print("🎉 SUCCESS: Found exactly 762 Melbourne listings!")
            return True
        elif total_count > 762:
            print(
                f"⚠️  WARNING: Found {total_count} Melbourne listings (more than expected 762)"
            )
            return False
        else:
            print(
                f"❌ FAILURE: Found only {total_count} Melbourne listings (expected 762)"
            )
            return False

    except subprocess.TimeoutExpired:
        print("❌ FAILURE: Scraper timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ FAILURE: Error running scraper: {e}")
        return False


def analyze_results():
    """Analyze the scraped results"""
    output_file = "melbourne_762_test.json"

    if not os.path.exists(output_file):
        print("No output file found for analysis")
        return

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            listings = json.load(f)

        print(f"\n=== RESULTS ANALYSIS ===")
        print(f"Total listings: {len(listings)}")

        # Check image URLs
        listings_with_images = [l for l in listings if l.get("image_urls")]
        print(f"Listings with image URLs: {len(listings_with_images)}")

        if listings_with_images:
            sample_listing = listings_with_images[0]
            image_urls = sample_listing.get("image_urls", [])
            print(f"Sample listing has {len(image_urls)} images")
            if image_urls:
                print(f"Sample image URL: {image_urls[0]}")

        # Show sample listing
        if listings:
            sample = listings[0]
            print(f"\nSample listing:")
            print(f"  Title: {sample.get('listing_title', 'N/A')}")
            print(f"  Address: {sample.get('address_line_1', 'N/A')}")
            print(f"  Suburb: {sample.get('suburb', 'N/A')}")
            print(f"  Property Type: {sample.get('property_type', 'N/A')}")
            print(f"  Photos: {sample.get('number_of_photos', 'N/A')}")

    except Exception as e:
        print(f"Error analyzing results: {e}")


if __name__ == "__main__":
    success = test_melbourne_762()
    analyze_results()

    if success:
        print(f"\n🎉 Test PASSED!")
        sys.exit(0)
    else:
        print(f"\n💥 Test FAILED!")
        sys.exit(1)
