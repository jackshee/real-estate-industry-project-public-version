#!/usr/bin/env python3
"""
Test script to verify Abbotsford has 32 listings with ?ssubs=0 parameter
"""

import subprocess
import json
import os
import sys
from pathlib import Path


def test_abbotsford_32():
    """Test that Abbotsford has exactly 32 listings with ?ssubs=0"""
    print("=== ABBOTSFORD 32 LISTINGS TEST ===")
    print("Testing Abbotsford (3067) with ?ssubs=0 parameter...")
    print("Expected: 32 listings (based on Domain website)")

    # Change to the scraper directory
    scraper_dir = Path(__file__).parent

    # Clean up old log file
    log_file = scraper_dir / "scrapy.log"
    if log_file.exists():
        log_file.unlink()
        print("Cleaned up old scrapy.log file")
    os.chdir(scraper_dir)

    # Output file for this test
    output_file = "abbotsford_32_test.json"

    # Remove existing output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    try:
        # Run the scraper with specific settings for Abbotsford
        print("Running scraper for Abbotsford...")
        cmd = [
            "scrapy",
            "crawl",
            "domain_rental",
            "-o",
            output_file,
            "-s",
            "CLOSESPIDER_ITEMCOUNT=100",  # Stop after 100 items (more than expected 32)
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
        if total_count == 32:
            print("🎉 SUCCESS: Found exactly 32 Abbotsford listings!")
            return True
        elif total_count > 32:
            print(
                f"⚠️  WARNING: Found {total_count} Abbotsford listings (more than expected 32)"
            )
            return False
        else:
            print(
                f"❌ FAILURE: Found only {total_count} Abbotsford listings (expected 32)"
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
    output_file = "abbotsford_32_test.json"

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
            print(f"  Address: {sample.get('full_address', 'N/A')}")
            print(f"  Suburb: {sample.get('suburb', 'N/A')}")
            print(f"  Property Type: {sample.get('property_type', 'N/A')}")
            print(f"  Photos: {sample.get('number_of_photos', 'N/A')}")
            print(f"  Price: {sample.get('rental_price', 'N/A')}")

    except Exception as e:
        print(f"Error analyzing results: {e}")


if __name__ == "__main__":
    success = test_abbotsford_32()
    analyze_results()

    if success:
        print(f"\n🎉 Test PASSED!")
        sys.exit(0)
    else:
        print(f"\n💥 Test FAILED!")
        sys.exit(1)
