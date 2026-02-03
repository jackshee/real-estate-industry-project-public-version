# Data Ingestion Plan for Airflow Refactoring

## Overview
This document outlines the detailed plan for refactoring data ingestion from notebooks into Airflow DAGs, organized by data source update frequency and usage patterns.

---

## Data Source Classification

### 1. **MONTHLY RECURRING** - Listing Data (Scraper)

**Source:** Domain.com.au scraper  
**Frequency:** Monthly (1st of each month)  
**Type:** Listing-level property data  
**Update Pattern:** New data each month, append to historical dataset

**Strategy:**
- **DAG:** `dags/listings_monthly_dag.py`
- **Script:** `scripts/recurring/listings_scraper.py`
- **Schedule:** `0 0 1 * *` (1st of each month at midnight)
- **Data Structure:**
  ```
  data/
  ├── landing/
  │   └── domain/
  │       └── live/
  │           └── {YYYY_MM}/
  │               └── rental_listings_{YYYY_MM}.csv
  └── curated/
      └── domain/
          └── listings_aggregated.csv  # Appended monthly
  ```

**Key Features:**
- Date-partitioned by ingestion month
- Append to curated aggregated dataset
- Add `ingestion_date` and `ingestion_month` columns
- Deduplication logic based on `property_id` + `listing_date`
- Idempotent: Check if month already ingested before scraping

**Dependencies:** None (standalone scraper)

---

### 2. **QUARTERLY RECURRING** - Rent & Economic Data

**Sources:**
- DFFH Moving Annual Rent (quarterly median rent by suburb)
- Economic indicators (unemployment, interest rates, price data, economic activity, population, investment)

**Frequency:** Quarterly (released after each quarter end)  
**Update Pattern:** New quarter data released ~1 month after quarter end

**Strategy:**
- **DAG:** `dags/economic_data_quarterly_dag.py`
- **Scripts:**
  - `scripts/recurring/download_rent_data.py`
  - `scripts/recurring/download_economic_data.py` (handles all 6 economic indicators)
- **Schedule:** `0 0 15 1,4,7,10 *` (15th of Jan, Apr, Jul, Oct - allows time for data release)
- **Data Structure:**
  ```
  data/
  ├── landing/
  │   ├── moving_annual_rent/
  │   │   └── {YYYY}/
  │   │       └── Q{1-4}/
  │   │           └── moving_annual_median_weekly_rent_by_suburb.xlsx
  │   ├── unemployment_rate/
  │   │   └── {YYYY}/
  │   │       └── Q{1-4}/
  │   │           └── quarterly_unemployment_rate.csv
  │   ├── interest_rates/
  │   ├── price_data/
  │   ├── economic_activity/
  │   ├── population/
  │   └── investment/
  └── curated/
      ├── rent_data/
      │   └── quarterly_rent_aggregated.csv
      └── economic_data/
          └── quarterly_economic_aggregated.csv
  ```

**Key Features:**
- Quarter detection: Only run if new quarter data is available
- Check data freshness: Verify quarter hasn't been ingested already
- All economic indicators in one script (they're scraped from same source)
- Append to time-series curated datasets
- Add `quarter`, `year`, `ingestion_date` columns

**Dependencies:** None (independent downloads)

---

### 3. **ONE-TIME INITIALIZATION** - Census Data

**Source:** ABS Census 2021 (SAL codes 20001-22944)  
**Frequency:** Once per census cycle (Australian census every 5 years, next in 2026)  
**Update Pattern:** Static dataset, manual re-trigger if needed

**Strategy:**
- **DAG:** `dags/census_init_dag.py`
- **Script:** `scripts/one_time/download_census_data.py`
- **Schedule:** `None` (manual trigger only, paused after first success)
- **Data Structure:**
  ```
  data/
  ├── landing/
  │   └── population_by_suburb/
  │       └── census_2021/
  │           ├── SAL20001_population.xlsx
  │           ├── SAL20002_population.xlsx
  │           └── ... (2700+ files)
  └── processed/
      └── census/
          ├── population_breakdown.csv
          ├── median_stats.csv
          ├── household_income.csv
          └── personal_income.csv
  ```

**Key Features:**
- **Batching:** Split into task groups (e.g., 100 SAL codes per task) to avoid timeout
- **Idempotency:** Skip already-downloaded files
- **Error handling:** Track failed SAL codes, allow partial success
- **Post-processing:** Separate task to convert Excel to CSV (can be in same DAG)
- **DAG Configuration:** 
  - `is_paused_upon_creation=True` after first successful run
  - Add comment: "Re-run manually when new census data available (next: 2026)"

**Dependencies:** None (standalone)

**Implementation Notes:**
- Use Airflow's `Dynamic Task Mapping` or `TaskGroup` for batching
- Consider: 27 task groups of ~100 SAL codes each
- Store failed SAL codes in XCom for reporting

---

### 4. **ANNUAL OR ONE-TIME** - Schools Data

**Source:** Education Victoria (school locations)  
**Frequency:** Annual updates (2023, 2024, 2025 data available)  
**Update Pattern:** New year data released annually

**Strategy:**
- **DAG:** `dags/schools_annual_dag.py`
- **Script:** `scripts/recurring/download_schools_data.py` (or one_time if truly static)
- **Schedule:** `0 0 1 1 *` (1st of January annually) OR manual trigger
- **Data Structure:**
  ```
  data/
  ├── landing/
  │   └── schools/
  │       ├── school_locations_2023.csv
  │       ├── school_locations_2024.csv
  │       └── school_locations_2025.csv
  └── curated/
      └── schools/
          └── schools_combined.csv  # Latest year or all years merged
  ```

**Key Features:**
- Check if year already downloaded before fetching
- Option to download all available years on first run
- Append new year data to curated combined dataset
- Add `data_year` column

**Decision Needed:** 
- Is this truly annual (schedule yearly)?
- Or one-time initialization (manual trigger)?

**Dependencies:** None

---

### 5. **ONE-TIME OR INFREQUENT** - Public Transport Data

**Source:** Open Data Victoria (PTV stops and lines)  
**Frequency:** Infrequent updates (transport network changes rarely)  
**Usage:** Used in `scripts/api/fetch_ors_routes.py` to find nearest PTV stations

**Strategy:**
- **DAG:** `dags/transport_init_dag.py`
- **Script:** `scripts/one_time/download_transport_data.py`
- **Schedule:** `None` (manual trigger, or quarterly check for updates)
- **Data Structure:**
  ```
  data/
  └── landing/
      └── ptv/
          ├── public_transport_stops.geojson
          └── public_transport_lines.geojson
  ```

**Key Features:**
- Check file hash/version before re-downloading
- Since used downstream, keep but mark as infrequent
- Optional: Add quarterly check task that verifies if data has changed

**Dependencies:** None

---

## Repository Structure

```
project/
├── dags/
│   ├── __init__.py
│   ├── listings_monthly_dag.py          # Monthly: Domain scraper
│   ├── economic_data_quarterly_dag.py   # Quarterly: Rent + Economic
│   ├── census_init_dag.py              # One-time: Census (paused after success)
│   ├── schools_annual_dag.py           # Annual: Schools (or one-time)
│   └── transport_init_dag.py           # Infrequent: PTV data
│
├── scripts/
│   ├── __init__.py
│   ├── config.py                        # Centralized config (paths, URLs, schedules)
│   │
│   ├── recurring/                      # Scheduled tasks
│   │   ├── __init__.py
│   │   ├── listings_scraper.py
│   │   ├── download_rent_data.py
│   │   └── download_economic_data.py
│   │
│   ├── one_time/                       # Initialization tasks
│   │   ├── __init__.py
│   │   ├── download_census_data.py
│   │   ├── download_schools_data.py
│   │   └── download_transport_data.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── data_validation.py          # Data quality checks
│       ├── logging.py                  # Standardized logging
│       ├── partitioning.py             # Date-partitioning logic
│       └── storage.py                  # File operations (append, dedupe)
│
├── data/
│   ├── landing/                        # Raw data (date-partitioned)
│   │   ├── domain/
│   │   │   └── live/
│   │   │       └── {YYYY_MM}/
│   │   ├── moving_annual_rent/
│   │   │   └── {YYYY}/
│   │   │       └── Q{1-4}/
│   │   ├── economic_data/
│   │   │   └── {YYYY}/
│   │   │       └── Q{1-4}/
│   │   ├── population_by_suburb/
│   │   │   └── census_2021/
│   │   ├── schools/
│   │   └── ptv/
│   │
│   └── curated/                       # Aggregated/processed
│       ├── domain/
│       │   └── listings_aggregated.csv
│       ├── rent_data/
│       │   └── quarterly_rent_aggregated.csv
│       ├── economic_data/
│       │   └── quarterly_economic_aggregated.csv
│       └── schools/
│           └── schools_combined.csv
│
└── airflow/
    ├── config/
    │   └── default_args.py             # Shared DAG arguments
    └── utils/
        └── data_utils.py               # Airflow-specific utilities
```

---

## Implementation Priorities

### Phase 1: Recurring Data Sources (High Priority)
1. ✅ Listings scraper (monthly)
2. ✅ Rent data downloader (quarterly)
3. ✅ Economic data downloader (quarterly)

### Phase 2: One-Time Initialization (Medium Priority)
4. ✅ Census data downloader (with batching)
5. ✅ Schools data downloader
6. ✅ Transport data downloader

### Phase 3: Utilities & Configuration (High Priority)
7. ✅ Centralized config.py
8. ✅ Data validation utilities
9. ✅ Logging utilities
10. ✅ Partitioning utilities

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Separate DAGs by frequency** | Easier cron scheduling, independent failure handling |
| **Date-partitioned raw data** | Supports incremental processing, time-travel queries |
| **Curated layer for aggregation** | Raw stays immutable; transformations centralized |
| **One-time DAGs paused after success** | Prevents accidental re-runs; documents intent |
| **Batching for census data** | 2700+ files would timeout; task groups enable parallel processing |
| **Quarter detection logic** | Only run quarterly tasks when new data is available |
| **Idempotency checks** | All scripts check if data already exists before downloading |

---

## Data Quality & Validation

Each script should include:
- **Pre-flight checks:** Verify data source is accessible
- **Post-download validation:** 
  - File size checks
  - Schema validation (column names, types)
  - Row count validation
  - Date range validation (for time-series data)
- **Error handling:** Graceful failures with retry logic
- **Logging:** Structured logs for Airflow UI

---

## Next Steps

1. **Confirm schools data frequency:** Annual or one-time?
2. **Review transport data usage:** Confirm it's needed downstream
3. **Census batching strategy:** Decide on task group size (100 SAL codes per group?)
4. **Start implementation:** Begin with Phase 1 (recurring data sources)

---

## Questions for Clarification

1. **Schools data:** Annual schedule or one-time initialization?
2. **Census batching:** Preferred batch size? (Recommendation: 100 SAL codes per task group)
3. **Data retention:** How long to keep raw monthly snapshots? (Recommendation: 12-24 months)
4. **Backfills:** Support historical backfills for listings? (Recommendation: Yes, with date parameter)
5. **Transport data:** Keep as-is or add quarterly check for updates?
