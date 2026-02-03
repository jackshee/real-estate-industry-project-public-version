# GitHub Actions Setup Guide

## Overview

This project uses GitHub Actions to automatically scrape Domain.com.au rental listings every quarter. The workflow runs on GitHub's servers, so you don't need to keep your computer running.

## Quick Start

### 1. Ensure Required Files Are Committed

The scraper needs the geo data file to know which suburbs to scrape:

```bash
# Check if geo data file exists
ls -la data/geo/vic_suburbs_postcodes.csv

# If it doesn't exist, you'll need to add it
# The file should contain suburb and postcode data for Victoria
```

**Important**: The `.gitignore` has been updated to allow this file to be committed. If you have issues, you may need to force-add it:

```bash
git add -f data/geo/vic_suburbs_postcodes.csv
git commit -m "Add geo data file for scraper"
git push
```

### 2. Verify Workflow File

The workflow file is located at:
```
.github/workflows/quarterly-domain-scraper.yml
```

### 3. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on **Settings** → **Actions** → **General**
3. Ensure "Allow all actions and reusable workflows" is selected
4. Save changes

### 4. Test the Workflow

**Option A: Manual Trigger (Recommended for first test)**

1. Go to **Actions** tab in GitHub
2. Select **Quarterly Domain Scraper** workflow
3. Click **Run workflow** button
4. Optionally specify a quarter (e.g., `2025-Q1`)
5. Click **Run workflow**

**Option B: Wait for Scheduled Run**

The workflow will automatically run on:
- January 15th at 00:00 UTC
- April 15th at 00:00 UTC  
- July 15th at 00:00 UTC
- October 15th at 00:00 UTC

## How It Works

### Workflow Steps

1. **Checkout**: Gets your repository code
2. **Setup Python**: Installs Python 3.10
3. **Install Dependencies**: Installs packages from `requirements.txt`
4. **Determine Quarter**: Calculates which quarter to scrape
5. **Run Scraper**: Executes `scripts/recurring/domain_live_scraper.py`
6. **Check Results**: Validates output file was created
7. **Commit Results**: Automatically commits scraped data
8. **Create Summary**: Shows results in GitHub Actions UI

### Output Structure

Scraped data is saved to:
```
data/landing/domain/live/{YYYY}/{Q{1-4}}/rental_listings_{YYYY}_{MM}.csv
```

For example:
- `data/landing/domain/live/2025/Q1/rental_listings_2025_03.csv`
- `data/landing/domain/live/2025/Q2/rental_listings_2025_06.csv`

### Automatic Commits

The workflow automatically commits scraped data with message:
```
Scrape Domain listings: 2025-Q1 [skip ci]
```

The `[skip ci]` tag prevents the commit from triggering another workflow run.

## Monitoring

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Click on **Quarterly Domain Scraper**
3. See all past runs with status (✅ success, ❌ failure, ⏳ in progress)

### View Logs

1. Click on a workflow run
2. Click on the **scrape** job
3. Expand steps to see detailed logs
4. Check for any errors or warnings

### Summary Information

Each run includes a summary with:
- Quarter scraped
- File size
- Number of listings
- Status

## Troubleshooting

### Issue: "Geo data file not found"

**Error:**
```
Error loading suburb data: FileNotFoundError: data/geo/vic_suburbs_postcodes.csv
```

**Solution:**
1. Ensure the file exists: `data/geo/vic_suburbs_postcodes.csv`
2. Force-add to git: `git add -f data/geo/vic_suburbs_postcodes.csv`
3. Commit and push: `git commit -m "Add geo data" && git push`

### Issue: Workflow times out

**Error:**
```
The job has timed out after 360 minutes
```

**Solution:**
- The scraper processes 3,186+ suburbs and can take several hours
- GitHub Actions has a 6-hour limit
- If it consistently times out, consider:
  - Splitting into multiple workflows by region
  - Reducing number of suburbs per run
  - Using a different scheduling service

### Issue: No data committed

**Check:**
1. Did the scraper complete successfully? (Check logs)
2. Was the output file created? (Check "Check scrape results" step)
3. Are there git permission issues? (Check "Commit results" step logs)

### Issue: Scraper fails with Selenium errors

**Error:**
```
selenium.common.exceptions.WebDriverException
```

**Solution:**
- The workflow installs Chrome/Chromium automatically
- If issues persist, check the "Install system dependencies" step
- Selenium is only needed for image extraction - scraper can work without it

## Manual Execution

You can also run the scraper locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scripts/recurring/domain_live_scraper.py --quarter 2025-Q1

# Or use current quarter
python scripts/recurring/domain_live_scraper.py
```

## Customization

### Change Schedule

Edit `.github/workflows/quarterly-domain-scraper.yml`:

```yaml
schedule:
  - cron: '0 0 15 1,4,7,10 *'  # Change this line
```

Cron format: `minute hour day month day-of-week`

### Change Output Directory

Edit the workflow file or pass `--output-dir` to the script.

### Add Notifications

Add a step to send notifications (email, Slack, etc.) on success/failure.

## Next Steps

1. ✅ Test workflow with manual trigger
2. ✅ Verify data is committed correctly
3. ✅ Monitor first scheduled run
4. ✅ Set up notifications (optional)

## Questions?

- Check workflow logs in GitHub Actions
- Review `.github/workflows/README.md` for workflow details
- Review `scripts/recurring/README.md` for script details
