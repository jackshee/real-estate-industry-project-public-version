# GitHub Actions Workflows

This directory contains automated workflows for data ingestion and processing.

## Quarterly Domain Scraper

**Workflow:** `.github/workflows/quarterly-domain-scraper.yml`

### Overview

Automatically scrapes Domain.com.au rental listings every quarter (15th of Jan, Apr, Jul, Oct).

### Schedule

- **Automatic**: Runs on the 15th of January, April, July, and October at 00:00 UTC
- **Manual**: Can be triggered manually from GitHub Actions UI with optional quarter parameter

### How It Works

1. **Determines Quarter**: 
   - Scheduled runs: Scrapes the previous quarter (e.g., Jan 15th → Q4 of previous year)
   - Manual runs: Uses specified quarter or current quarter

2. **Runs Scraper**: 
   - Executes `scripts/recurring/domain_live_scraper.py`
   - Saves to `data/landing/domain/live/{YYYY}/{Q{1-4}}/rental_listings_{YYYY}_{MM}.csv`

3. **Commits Results**: 
   - Automatically commits scraped data to repository
   - Commit message: `Scrape Domain listings: {QUARTER} [skip ci]`

### Requirements

1. **Geo Data File**: 
   - Must commit `data/geo/vic_suburbs_postcodes.csv` to repository
   - This file is required for the scraper to know which suburbs to scrape

2. **Dependencies**: 
   - All Python dependencies from `requirements.txt`
   - Selenium/Chrome for image extraction (handled automatically in workflow)

### Manual Trigger

To manually trigger a scrape:

1. Go to **Actions** tab in GitHub
2. Select **Quarterly Domain Scraper** workflow
3. Click **Run workflow**
4. Optionally specify quarter (format: `2025-Q1`)
5. Click **Run workflow**

### Output Structure

```
data/
└── landing/
    └── domain/
        └── live/
            └── {YYYY}/
                └── Q{1-4}/
                    └── rental_listings_{YYYY}_{MM}.csv
```

### Monitoring

- Check workflow runs in **Actions** tab
- View logs for each run
- Summary includes file size and listing count

### Troubleshooting

**Issue**: Scraper fails with "Geo data file not found"
- **Solution**: Ensure `data/geo/vic_suburbs_postcodes.csv` is committed to repository

**Issue**: Scraper times out
- **Solution**: GitHub Actions has 6-hour limit. For very large scrapes, consider splitting by region or increasing timeout

**Issue**: No data committed
- **Solution**: Check if output file was created. Workflow will fail if file doesn't exist after scraping.
