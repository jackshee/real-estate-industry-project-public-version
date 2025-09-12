#!/bin/bash

# Script to run the Domain rental spider and save results to CSV

echo "Starting Domain rental spider..."
echo "This will scrape all Victorian suburbs and save to rental_listings_2025_09.csv"
echo ""

# Change to the domain_scraper directory
cd "$(dirname "$0")"

# Activate virtual environment and run the spider with CSV output
source ../../venv/bin/activate
scrapy crawl domain_rental -o ../../data/raw/domain/rental_listings_2025_09.csv -L INFO

echo ""
echo "Spider completed!"
echo "Results saved to: ../../data/raw/domain/rental_listings_2025_09.csv"
