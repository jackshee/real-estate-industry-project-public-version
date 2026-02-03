# Airflow & Data Storage Guide

## Part 1: How Apache Airflow Works

### 🏗️ **Airflow Architecture**

Airflow is a **scheduler service** that needs to be running continuously. Here's how it works:

```
┌─────────────────┐
│  Airflow        │
│  Scheduler      │ ← Checks DAGs every few seconds
│  (Background)   │   Triggers tasks based on schedule
└────────┬────────┘
         │
         ├──→ Reads DAG files from `dags/` folder
         │
         ├──→ Checks schedule (cron expressions)
         │
         └──→ Executes tasks when schedule matches
```

### 🔄 **How Scheduling Works**

**Yes, Airflow needs to be running continuously**, but it's a background service (like a web server).

**Components:**
1. **Scheduler** - Checks DAG schedules every few seconds, triggers tasks
2. **Webserver** - UI for monitoring (http://localhost:8080)
3. **Executor** - Runs the actual tasks (can be local or distributed)
4. **Metadata Database** - Stores DAG state, task history, etc.

**Example:**
```python
# dags/domain_live_scraper_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'domain_live_scraper',
    default_args=default_args,
    description='Scrape Domain.com.au listings quarterly',
    schedule='0 0 15 1,4,7,10 *',  # ← This is a cron expression
    start_date=datetime(2025, 1, 1),
    catchup=False,  # Don't backfill past dates
) as dag:
    
    scrape_task = PythonOperator(
        task_id='scrape_listings',
        python_callable=scrape_live_listings,  # Your function
    )
```

**Cron Expression Breakdown:**
```
'0 0 15 1,4,7,10 *'
 │ │ │  └───────┘ └─ Day of week (any)
 │ │ └──────────── Day of month (15th)
 │ └────────────── Hour (0 = midnight)
 └──────────────── Minute (0)
 
 Translation: "At 00:00 on the 15th day of Jan, Apr, Jul, Oct"
```

### 🚀 **Running Airflow**

**Option 1: Local Development (Simplest)**
```bash
# Install Airflow
pip install apache-airflow

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start scheduler (in one terminal)
airflow scheduler

# Start webserver (in another terminal)
airflow webserver --port 8080
```

**Option 2: Docker (Recommended for Production)**
```bash
# Use official Airflow Docker image
docker-compose up -d
```

**Option 3: Cloud Services**
- **Google Cloud Composer** (managed Airflow)
- **AWS MWAA** (managed Airflow)
- **Astronomer** (managed Airflow platform)

### ⏰ **How It Triggers Tasks**

1. **Scheduler runs continuously** (checks every ~5 seconds by default)
2. **Reads DAG files** from `dags/` folder
3. **Evaluates schedule** - "Is it time to run this DAG?"
4. **Creates DAG Run** - If schedule matches, creates a new execution
5. **Executes tasks** - Runs your Python scripts
6. **Tracks state** - Success, failure, retries, etc.

**You don't need to manually trigger anything** - Airflow does it automatically based on the schedule!

### 📊 **Monitoring**

Access the Airflow UI at `http://localhost:8080`:
- See all DAGs
- View task history
- Monitor running tasks
- Check logs
- Manually trigger DAGs if needed
- View task dependencies

---

## Part 2: Database vs. File Storage

### 📁 **Current State: File-Based Storage**

Your project currently uses **CSV files**:
```
data/
├── landing/domain/live/rental_listings_2025_09.csv
├── landing/domain/wayback/rental_listings_2024_03.csv
└── curated/domain/listings_aggregated.csv
```

**Pros:**
- ✅ Simple - no database setup needed
- ✅ Human-readable (can open in Excel)
- ✅ Easy to version control (small files)
- ✅ No database maintenance
- ✅ Works well for data science workflows

**Cons:**
- ❌ Slower for large datasets
- ❌ No concurrent access control
- ❌ Harder to query (need to load entire file)
- ❌ No ACID transactions
- ❌ Limited scalability

---

### 🗄️ **When to Use a Database**

**Use a database when:**

1. **Large datasets** (>10GB, millions of rows)
   - Databases are optimized for large data
   - CSV files become slow to load/process

2. **Concurrent access** (multiple users/processes)
   - Databases handle concurrent reads/writes
   - CSV files can't be safely written by multiple processes

3. **Complex queries** (filtering, aggregations, joins)
   - SQL is powerful for data analysis
   - CSV requires loading everything into memory

4. **Real-time updates** (frequent writes)
   - Databases handle incremental updates efficiently
   - CSV requires rewriting entire file

5. **Data integrity** (ACID transactions)
   - Databases ensure data consistency
   - CSV files can be corrupted if write fails mid-way

6. **Production applications** (APIs, dashboards)
   - Databases are standard for production
   - CSV files are not suitable for production apps

**Don't use a database when:**

1. **Small datasets** (<1GB, <1M rows)
   - CSV is simpler and sufficient

2. **Data science workflows** (exploration, analysis)
   - Pandas works great with CSV
   - Easier to share data with colleagues

3. **One-time analysis** (not production)
   - CSV is fine for research/prototyping

4. **Version control** (tracking data changes)
   - CSV files can be versioned in Git (if small)
   - Databases require separate versioning strategy

---

### 🎯 **Recommendation for Your Project**

**Current Scale Analysis:**
- **Listings data**: ~14K properties per scrape
- **Historical data**: ~14K properties × 14 quarters = ~200K records
- **File sizes**: Likely <500MB total
- **Usage**: Data science analysis, not production app

**Recommendation: ✅ Stick with CSV files (for now)**

**Why:**
1. **Data size is manageable** - CSV files work fine for this scale
2. **Data science workflow** - Pandas + CSV is standard
3. **Simplicity** - No database setup/maintenance overhead
4. **Flexibility** - Easy to share, version, and analyze

**When to consider a database:**
- If dataset grows >10GB
- If you need real-time API access
- If multiple people need concurrent access
- If you're building a production application

---

### 🔄 **Hybrid Approach (Best of Both Worlds)**

You can use **both**:

```
┌─────────────────┐
│  Airflow        │
│  (Ingestion)    │
└────────┬────────┘
         │
         ├──→ CSV files (raw data, versioned)
         │    data/landing/domain/live/{YYYY}/Q{1-4}/
         │
         └──→ Database (optional, for analysis)
              - PostgreSQL for structured queries
              - Or keep CSV, load into pandas for analysis
```

**Workflow:**
1. **Airflow scrapes** → Saves to CSV (raw data)
2. **Analysis** → Load CSV into pandas (or database if needed)
3. **Curated layer** → CSV files (aggregated data)

**This gives you:**
- ✅ Simple file-based storage (CSV)
- ✅ Option to load into database later if needed
- ✅ Easy to share and version control
- ✅ No database maintenance overhead

---

## Part 3: Practical Setup

### 📋 **Airflow Setup Checklist**

1. **Install Airflow**
   ```bash
   pip install apache-airflow
   ```

2. **Set Airflow home** (where DAGs and config live)
   ```bash
   export AIRFLOW_HOME=/path/to/your/project/airflow
   ```

3. **Initialize database**
   ```bash
   airflow db init
   ```

4. **Create admin user**
   ```bash
   airflow users create --username admin --password admin \
       --firstname Admin --lastname User --role Admin \
       --email admin@example.com
   ```

5. **Start services**
   ```bash
   # Terminal 1: Scheduler
   airflow scheduler
   
   # Terminal 2: Webserver
   airflow webserver --port 8080
   ```

6. **Access UI**
   - Open `http://localhost:8080`
   - Login with admin/admin
   - See your DAGs!

### 🔧 **Keeping Airflow Running**

**Option 1: Manual (Development)**
- Run `airflow scheduler` and `airflow webserver` in terminals
- Keep terminals open

**Option 2: Background Process (Development)**
```bash
# Start scheduler in background
nohup airflow scheduler > scheduler.log 2>&1 &

# Start webserver in background
nohup airflow webserver > webserver.log 2>&1 &
```

**Option 3: System Service (Production)**
- Create systemd service files
- Airflow runs as a system service
- Auto-starts on boot

**Option 4: Docker (Recommended)**
```yaml
# docker-compose.yml
version: '3'
services:
  scheduler:
    image: apache/airflow:latest
    command: scheduler
    # ... config
  
  webserver:
    image: apache/airflow:latest
    command: webserver
    ports:
      - "8080:8080"
    # ... config
```

Then: `docker-compose up -d` (runs in background)

---

## Summary

### ✅ **Airflow**
- **Yes, it needs to run continuously** (like a web server)
- **Scheduler checks schedules automatically** - you don't need to trigger manually
- **Runs in background** - you can close your terminal (if set up properly)
- **UI for monitoring** - check status at http://localhost:8080

### ✅ **Storage**
- **Stick with CSV files** for your current scale
- **Consider database** if data grows >10GB or you need production features
- **Hybrid approach** - CSV for storage, load into pandas/database for analysis

### 🚀 **Next Steps**
1. Set up Airflow locally (development)
2. Create your first DAG (domain scraper)
3. Test with manual trigger
4. Enable scheduling
5. Monitor in UI

Want me to help you set up Airflow and create your first DAG?
