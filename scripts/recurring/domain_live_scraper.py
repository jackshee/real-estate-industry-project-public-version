#!/usr/bin/env python3
"""
Domain.com.au Live Listings Scraper for GitHub Actions

This script scrapes current rental listings from Domain.com.au and saves them
in a date-partitioned structure. Designed to run quarterly via GitHub Actions.

Usage:
    python scripts/recurring/domain_live_scraper.py [--quarter YYYY-Q{1-4}] [--output-dir data/]
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_quarter_from_date(date: Optional[datetime] = None) -> tuple[str, str]:
    """
    Determine quarter and year from a date.
    
    Args:
        date: Datetime object (defaults to current date)
    
    Returns:
        Tuple of (year, quarter) e.g., ("2025", "Q1")
    """
    if date is None:
        date = datetime.now()
    
    year = date.year
    quarter = (date.month - 1) // 3 + 1
    
    return str(year), f"Q{quarter}"


def get_quarter_month(quarter: str) -> str:
    """
    Get the month string for a quarter (for filename).
    
    Args:
        quarter: Quarter string like "Q1", "Q2", etc.
    
    Returns:
        Month string like "03", "06", "09", "12"
    """
    quarter_to_month = {
        "Q1": "03",
        "Q2": "06", 
        "Q3": "09",
        "Q4": "12"
    }
    return quarter_to_month.get(quarter, "03")


def check_if_already_scraped(output_file: Path) -> bool:
    """
    Check if this quarter has already been scraped.
    
    Args:
        output_file: Path to expected output file
    
    Returns:
        True if file exists and has content, False otherwise
    """
    if not output_file.exists():
        return False
    
    # Check if file has content (more than just header)
    try:
        file_size = output_file.stat().st_size
        if file_size < 100:  # Less than 100 bytes probably just header
            logger.warning(f"Output file exists but appears empty: {output_file}")
            return False
        logger.info(f"Quarter already scraped: {output_file} ({file_size:,} bytes)")
        return True
    except Exception as e:
        logger.error(f"Error checking file: {e}")
        return False


def scrape_live_listings(
    year: str,
    quarter: str,
    base_data_dir: str = "data/",
    skip_if_exists: bool = True,
    verbose: bool = True
) -> bool:
    """
    Scrape live Domain.com.au listings for a specific quarter.
    
    Args:
        year: Year as string (e.g., "2025")
        quarter: Quarter as string (e.g., "Q1")
        base_data_dir: Base directory for data storage
        skip_if_exists: Skip scraping if output file already exists
        verbose: Enable verbose logging
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting live listings scrape for {year} {quarter}")
    
    # Determine output path
    month = get_quarter_month(quarter)
    output_dir = Path(base_data_dir) / "landing" / "domain" / "live" / year / quarter
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"rental_listings_{year}_{month}.csv"
    
    # Check if already scraped
    if skip_if_exists and check_if_already_scraped(output_file):
        logger.info(f"Skipping scrape - {year} {quarter} already exists")
        return True
    
    # Get scraper directory
    scraper_dir = project_root / "scraping" / "domain_scraper"
    
    if not scraper_dir.exists():
        logger.error(f"Scraper directory not found: {scraper_dir}")
        return False
    
    # Check if geo data exists
    geo_file = project_root / "data" / "geo" / "vic_suburbs_postcodes.csv"
    if not geo_file.exists():
        logger.error(f"Geo data file not found: {geo_file}")
        logger.error("This file is required for scraping. Please ensure it's committed to the repo.")
        return False
    
    # Build scrapy command
    cmd = [
        sys.executable,  # Use current Python interpreter
        "-m",
        "scrapy",
        "crawl",
        "domain_rental",
        "-o",
        str(output_file.absolute()),
        "-L",
        "INFO",
    ]
    
    logger.info(f"Running scraper from: {scraper_dir}")
    logger.info(f"Output will be saved to: {output_file}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info("=" * 60)
    
    try:
        # Change to scraper directory (Scrapy needs to run from project root)
        original_cwd = os.getcwd()
        os.chdir(scraper_dir)
        
        # Run the scraper
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        
        # Return to original directory
        os.chdir(original_cwd)
        
        # Verify output file was created
        if not output_file.exists():
            logger.error(f"Scraper completed but output file not found: {output_file}")
            return False
        
        file_size = output_file.stat().st_size
        logger.info("=" * 60)
        logger.info(f"✅ Scraper completed successfully!")
        logger.info(f"📁 Output file: {output_file}")
        logger.info(f"📊 File size: {file_size:,} bytes")
        
        # Count lines (approximate)
        try:
            with open(output_file, 'r') as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
            logger.info(f"📈 Listings scraped: {line_count:,}")
        except Exception as e:
            logger.warning(f"Could not count lines: {e}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Scraper failed with return code: {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"❌ Error running scraper: {e}")
        return False
    finally:
        # Ensure we return to original directory
        if 'original_cwd' in locals():
            os.chdir(original_cwd)


def main():
    """Main entry point for the scraper script."""
    parser = argparse.ArgumentParser(
        description="Scrape Domain.com.au live rental listings"
    )
    parser.add_argument(
        "--quarter",
        type=str,
        help="Quarter to scrape (format: YYYY-Q{1-4}, e.g., 2025-Q1). If not provided, uses current quarter.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/",
        help="Base directory for data storage (default: data/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scrape even if output file already exists",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Determine quarter
    if args.quarter:
        # Parse quarter string like "2025-Q1"
        try:
            year, quarter = args.quarter.split("-")
            if not quarter.startswith("Q"):
                quarter = f"Q{quarter}"
        except ValueError:
            logger.error(f"Invalid quarter format: {args.quarter}. Expected: YYYY-Q{1-4}")
            sys.exit(1)
    else:
        # Use current quarter
        year, quarter = get_quarter_from_date()
        logger.info(f"No quarter specified, using current: {year} {quarter}")
    
    # Run scraper
    success = scrape_live_listings(
        year=year,
        quarter=quarter,
        base_data_dir=args.output_dir,
        skip_if_exists=not args.force,
        verbose=args.verbose
    )
    
    if success:
        logger.info("✅ Scraping completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Scraping failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
