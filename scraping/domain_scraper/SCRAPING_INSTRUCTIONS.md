# Domain Rental Scraper - Instructions

This directory contains a Scrapy spider for scraping rental property listings from Domain.com.au.

## Quick Start

### Option 1: Using the provided scripts (Recommended)

1. **Test the spider first** (recommended):
   ```bash
   cd scraping/domain_scraper
   python test_spider.py
   ```

2. **Run live listings scraping**:
   ```bash
   cd scraping/domain_scraper
   python run_spider.py
   ```
   Or using the shell script:
   ```bash
   cd scraping/domain_scraper
   ./run_spider.sh
   ```

3. **Run wayback historical scraping** (2022-2025):
   ```bash
   cd scraping/domain_scraper
   python run_wayback_spider.py
   ```

### Option 2: Using Scrapy directly

1. **Test with limited pages**:
   ```bash
   cd scraping/domain_scraper
   source ../../venv/bin/activate
   scrapy crawl domain_rental -o ../../data/landing/domain/live/test_rental_listings.csv -s CLOSESPIDER_PAGECOUNT=5
   ```

2. **Run full scraping**:
   ```bash
   cd scraping/domain_scraper
   source ../../venv/bin/activate
   scrapy crawl domain_rental -o ../../data/landing/domain/live/rental_listings_2025_09.csv
   ```

**Note**: The scripts automatically use the virtual environment, but if running Scrapy directly, you need to activate the virtual environment first with `source ../../venv/bin/activate`.

## Output

The spider will save results to:
- **Live listings**: `data/landing/domain/live/rental_listings_2025_09.csv`
- **Wayback listings**: `data/landing/domain/wayback/rental_listings_YYYY_MM.csv`
- **Test**: `data/landing/domain/live/test_rental_listings.csv`

## Configuration

The spider is configured to:
- Process all Victorian suburbs (3,186+ suburbs)
- Use conservative settings to avoid being blocked
- Extract detailed property information including:
  - Basic property details (address, price, bedrooms, etc.)
  - Property features and amenities
  - School catchment information
  - Market insights and demographics
  - Property images (using Selenium)

## Performance

- **Expected duration**: Several hours for full scraping
- **Concurrent requests**: 4 (conservative to avoid blocking)
- **Delay between requests**: 1 second (with randomization)
- **Auto-throttling**: Enabled to adapt to server response

## Monitoring

The spider provides detailed logging including:
- Progress per suburb
- Timing statistics
- Error handling
- Final summary with performance metrics

## Troubleshooting

1. **If the spider gets blocked**: The settings are conservative, but if you encounter issues, you can increase delays in `domain_spider.py` custom_settings.

2. **If Selenium fails**: The spider will continue without image extraction if Selenium fails.

3. **Memory issues**: The spider processes suburbs sequentially to manage memory usage.

## Files

- `domain_spider.py` - Main spider implementation
- `items.py` - Data structure definitions
- `pipelines.py` - Data processing pipelines
- `settings.py` - Scrapy configuration
- `run_spider.py` - Python script to run full scraping
- `run_spider.sh` - Shell script to run full scraping
- `test_spider.py` - Test script with limited pages
