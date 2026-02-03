# Recurring Data Ingestion Scripts

This directory contains scripts for scheduled data ingestion tasks.

## Domain Live Scraper

**Script:** `domain_live_scraper.py`

### Purpose

Scrapes current rental listings from Domain.com.au for a specific quarter.

### Usage

```bash
# Scrape current quarter
python scripts/recurring/domain_live_scraper.py

# Scrape specific quarter
python scripts/recurring/domain_live_scraper.py --quarter 2025-Q1

# Force re-scrape (even if already exists)
python scripts/recurring/domain_live_scraper.py --quarter 2025-Q1 --force

# Custom output directory
python scripts/recurring/domain_live_scraper.py --output-dir /path/to/data/
```

### Arguments

- `--quarter`: Quarter to scrape (format: `YYYY-Q{1-4}`, e.g., `2025-Q1`)
  - If not provided, uses current quarter
- `--output-dir`: Base directory for data storage (default: `data/`)
- `--force`: Force re-scrape even if output file already exists
- `--verbose`: Enable verbose logging (default: True)

### Output

Saves scraped data to:
```
{output-dir}/landing/domain/live/{YYYY}/{Q{1-4}}/rental_listings_{YYYY}_{MM}.csv
```

### Features

- **Idempotent**: Skips scraping if output file already exists (unless `--force`)
- **Quarter detection**: Automatically determines quarter from date
- **Error handling**: Graceful failures with detailed logging
- **File validation**: Checks if output file was created successfully

### Requirements

- Scrapy project in `scraping/domain_scraper/`
- Geo data file: `data/geo/vic_suburbs_postcodes.csv`
- All dependencies from `requirements.txt`

### Integration

This script is designed to be called by:
- **GitHub Actions**: `.github/workflows/quarterly-domain-scraper.yml`
- **Local execution**: For testing or manual runs
- **Future Airflow**: Can be adapted for Airflow DAGs if needed
