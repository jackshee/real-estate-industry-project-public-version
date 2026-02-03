# Domain Scraper Airflow Refactoring Plan

## Current State Analysis

### Live Scraper (`run_spider.py`)
- **Spider**: `domain_rental` (Scrapy)
- **Source**: Live Domain.com.au website
- **Output**: `data/landing/domain/live/rental_listings_YYYY_MM.csv`
- **Current behavior**: Hardcoded filename with date, runs manually
- **Scope**: Scrapes all Victorian suburbs (3,186+ suburbs)

### Wayback Scraper (`run_wayback_spider.py`)
- **Spider**: `wayback_domain_rental` (Scrapy)
- **Source**: Wayback Machine archived snapshots
- **Input**: `data/snapshots/suburb_snapshots_2022_2025_quarterly_snapshots.csv`
- **Output**: `data/landing/domain/wayback/rental_listings_YYYY_MM.csv`
- **Current behavior**: Processes quarters in reverse chronological order
- **Scope**: Historical data from 2022 Q3 to 2025 Q2

---

## Proposed Approach & Feedback

### ✅ **Your Approach is Sound**

**Live Scraper (Quarterly via Airflow):**
- ✅ **Correct**: Live data changes constantly, needs scheduled updates
- ✅ **Quarterly makes sense**: Aligns with rent/economic data releases
- ✅ **Airflow benefits**: Monitoring, error handling, retries, logging

**Wayback Scraper (Monthly, NOT via Airflow):**
- ✅ **Correct reasoning**: Historical snapshots are static - they don't change
- ✅ **No scheduling needed**: Can run on-demand or as one-time initialization
- ⚠️ **But consider**: Even if not scheduled, having it as a **manual Airflow task** provides:
  - Standardized logging and error handling
  - Data validation
  - Easy re-runs for specific quarters if needed
  - Integration with your data pipeline

---

## Recommended Structure

### Option A: Your Approach (Simpler)
```
scripts/
├── recurring/
│   └── domain_live_scraper.py      # Quarterly Airflow task
└── one_time/
    └── domain_wayback_scraper.py   # Manual script (no Airflow)
```

**Pros:**
- Simpler - wayback doesn't need scheduling
- Clear separation: scheduled vs. on-demand

**Cons:**
- Wayback scraper won't have Airflow monitoring/logging
- Manual runs require remembering command-line syntax

### Option B: Hybrid Approach (Recommended)
```
scripts/
├── recurring/
│   └── domain_live_scraper.py      # Quarterly Airflow task (scheduled)
└── one_time/
    └── domain_wayback_scraper.py   # Manual Airflow task (on-demand)
```

**Pros:**
- Wayback still gets Airflow benefits (logging, monitoring, validation)
- Can trigger manually from Airflow UI when needed
- Consistent error handling and data validation
- Easy to re-run specific quarters if scraping fails

**Cons:**
- Slightly more setup (but minimal)

**Recommendation: Use Option B** - Even if wayback is manual, having it as an Airflow task provides consistency and better observability.

---

## Detailed Implementation Plan

### 1. Live Scraper (Quarterly Airflow Task)

**DAG:** `dags/domain_live_scraper_dag.py`

**Schedule:** `0 0 15 1,4,7,10 *` (15th of Jan, Apr, Jul, Oct - allows time for quarter-end data)

**Script:** `scripts/recurring/domain_live_scraper.py`

**Key Features:**
- **Quarter detection**: Automatically determine current quarter from execution date
- **Idempotency**: Check if quarter already scraped before running
- **Date-partitioned output**: `data/landing/domain/live/{YYYY}/Q{1-4}/rental_listings_{YYYY}_{MM}.csv`
- **Append to curated**: After scraping, append to aggregated dataset with `ingestion_date`
- **Error handling**: Retry logic, graceful failures
- **Data validation**: Row counts, schema validation, date range checks

**Data Flow:**
```
Airflow Task → domain_live_scraper.py → Scrapy Spider → 
  → Raw: data/landing/domain/live/{YYYY}/Q{1-4}/rental_listings_{YYYY}_{MM}.csv
  → Curated: data/curated/domain/listings_aggregated.csv (append)
```

**Implementation Details:**
```python
# scripts/recurring/domain_live_scraper.py
def scrape_live_listings(
    execution_date: str,  # From Airflow context
    base_data_dir: str = "../data/",
    verbose: bool = True
) -> bool:
    """
    Scrape live Domain.com.au listings for a specific quarter.
    
    Args:
        execution_date: Airflow execution date (YYYY-MM-DD)
        base_data_dir: Base directory for data storage
        verbose: Enable verbose logging
    
    Returns:
        bool: True if successful, False otherwise
    """
    # 1. Parse execution_date to determine quarter
    # 2. Check if quarter already scraped (idempotency)
    # 3. Run Scrapy spider with appropriate output path
    # 4. Validate output data
    # 5. Append to curated aggregated dataset
    # 6. Return success status
```

---

### 2. Wayback Scraper (Manual Airflow Task or Standalone Script)

**Option 2A: Manual Airflow Task (Recommended)**
- **DAG:** `dags/domain_wayback_scraper_dag.py`
- **Schedule:** `None` (manual trigger only)
- **Script:** `scripts/one_time/domain_wayback_scraper.py`

**Option 2B: Standalone Script (Your Preference)**
- **Script:** `scripts/one_time/domain_wayback_scraper.py`
- **No Airflow DAG** - run directly via command line

**Key Features:**
- **Quarter selection**: Allow specifying which quarters to scrape
- **Resume capability**: Skip already-scraped quarters
- **Batch processing**: Process quarters sequentially with progress tracking
- **Output structure**: Same as current (`data/landing/domain/wayback/rental_listings_YYYY_MM.csv`)

**Implementation Details:**
```python
# scripts/one_time/domain_wayback_scraper.py
def scrape_wayback_listings(
    quarters: List[str] = None,  # e.g., ["2024_Q1", "2024_Q2"]
    start_quarter: str = None,    # Start from this quarter
    end_quarter: str = None,       # End at this quarter
    base_data_dir: str = "../data/",
    skip_existing: bool = True,    # Skip already-scraped quarters
    verbose: bool = True
) -> Dict[str, bool]:
    """
    Scrape historical Domain.com.au listings from Wayback Machine.
    
    Args:
        quarters: Specific quarters to scrape (None = all available)
        start_quarter: Start quarter (format: "YYYY_Q{1-4}")
        end_quarter: End quarter (format: "YYYY_Q{1-4}")
        base_data_dir: Base directory for data storage
        skip_existing: Skip quarters that already have output files
        verbose: Enable verbose logging
    
    Returns:
        Dict mapping quarter to success status
    """
    # 1. Load suburb snapshots CSV
    # 2. Determine quarters to process
    # 3. For each quarter:
    #    - Check if already scraped (if skip_existing)
    #    - Run wayback spider for that quarter
    #    - Validate output
    # 4. Return results summary
```

---

## Repository Structure

```
project/
├── dags/
│   ├── __init__.py
│   ├── domain_live_scraper_dag.py      # Quarterly scheduled
│   └── domain_wayback_scraper_dag.py   # Manual trigger (optional)
│
├── scripts/
│   ├── __init__.py
│   ├── config.py                       # Centralized config
│   │
│   ├── recurring/
│   │   ├── __init__.py
│   │   └── domain_live_scraper.py     # Quarterly Airflow task
│   │
│   └── one_time/
│       ├── __init__.py
│       └── domain_wayback_scraper.py   # Manual/on-demand
│
├── scraping/
│   └── domain_scraper/                 # Existing Scrapy project
│       ├── domain_scraper/
│       │   └── spiders/
│       │       ├── domain_spider.py
│       │       └── wayback_domain_spider.py
│       ├── run_spider.py               # Keep for manual runs
│       └── run_wayback_spider.py       # Keep for manual runs
│
└── data/
    ├── landing/
    │   └── domain/
    │       ├── live/
    │       │   └── {YYYY}/
    │       │       └── Q{1-4}/
    │       │           └── rental_listings_{YYYY}_{MM}.csv
    │       └── wayback/
    │           └── rental_listings_{YYYY}_{MM}.csv
    └── curated/
        └── domain/
            └── listings_aggregated.csv
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Live scraper quarterly** | Aligns with economic data releases, reduces scraping load |
| **Date-partitioned raw data** | Easy to track, supports incremental processing |
| **Curated aggregated layer** | Single source of truth for analysis |
| **Wayback scraper manual** | Historical data is static, no need for scheduling |
| **Idempotency checks** | Prevent duplicate scraping, safe to re-run |
| **Quarter detection from execution_date** | Automatic quarter determination from Airflow context |

---

## Implementation Steps

### Phase 1: Refactor Live Scraper
1. ✅ Create `scripts/recurring/domain_live_scraper.py`
   - Extract logic from `run_spider.py`
   - Add quarter detection from execution_date
   - Add idempotency checks
   - Add data validation
   - Add curated layer append logic

2. ✅ Create `dags/domain_live_scraper_dag.py`
   - Quarterly schedule (15th of Jan, Apr, Jul, Oct)
   - PythonOperator calling domain_live_scraper.py
   - Error handling and retries
   - Logging configuration

3. ✅ Update data paths to date-partitioned structure

### Phase 2: Refactor Wayback Scraper (Optional)
4. ✅ Create `scripts/one_time/domain_wayback_scraper.py`
   - Extract logic from `run_wayback_spider.py`
   - Add quarter selection parameters
   - Add resume/skip-existing logic
   - Improve error handling

5. ✅ (Optional) Create `dags/domain_wayback_scraper_dag.py`
   - Manual trigger only
   - Parameterized for quarter selection

### Phase 3: Testing & Validation
6. ✅ Test live scraper with Airflow
7. ✅ Test wayback scraper (manual)
8. ✅ Validate data quality and schema
9. ✅ Test idempotency (re-running same quarter)

---

## Questions for Clarification

1. **Live scraper frequency**: Confirm quarterly (15th of Jan/Apr/Jul/Oct)?
2. **Wayback scraper**: Standalone script or manual Airflow task?
3. **Data retention**: How long to keep raw quarterly snapshots?
4. **Backfills**: Support historical backfills for live scraper? (e.g., if we missed Q1, can we scrape it later?)
5. **Error handling**: If scraping fails mid-way (e.g., after 1000 suburbs), should we:
   - Retry the entire quarter?
   - Resume from where it failed?
   - Save partial results?

---

## Next Steps

Once you confirm the approach, I'll:
1. Refactor `run_spider.py` → `scripts/recurring/domain_live_scraper.py`
2. Create `dags/domain_live_scraper_dag.py`
3. Update data paths to date-partitioned structure
4. Add idempotency and validation logic
5. (Optional) Refactor wayback scraper

Ready to proceed?
