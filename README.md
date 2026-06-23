# 🏎️ F1 Data Engineering Platform

> **End-to-end Data Engineering project built around Formula 1 racing data.**
> From a simple Python ETL script to a full cloud-native streaming platform — built incrementally, one step at a time.

---

## 👤 Author
**Amr Hagag** — Data Engineering Student & DEPI Trainee
- 📧 amr.hagag.prof@gmail.com
- 💼 [linkedin.com/in/amrhagag-dataeng](https://linkedin.com/in/amrhagag-dataeng)
- 🐙 [github.com/3mrZain7agag](https://github.com/3mrZain7agag)

---

## 🎯 Project Goal

A portfolio-grade, end-to-end Data Engineering platform that demonstrates mastery of the full modern DE stack:
- Data ingestion from REST APIs
- Data Warehouse design (Star Schema)
- Workflow orchestration (Apache Airflow)
- Data Lake architecture (Bronze / Silver / Gold)
- Distributed processing (Apache Spark)
- Streaming architecture (Apache Kafka)
- Cloud deployment (AWS S3, MSK, Glue, Redshift)
- Data quality (Great Expectations)
- Transformations (dbt)
- Machine Learning (scikit-learn + MLflow)
- Dashboarding (Power BI)

---

## 🗺️ Progressive Build Roadmap

| Step | Title | Status | Key Tools |
|------|-------|--------|-----------|
| 01 | Simple Python ETL | ✅ Complete | Python, Pandas, SQLite |
| 02 | Local Data Warehouse | ✅ Complete | PostgreSQL, Star Schema, Docker |
| 03 | Airflow Orchestration | ✅ Complete | Apache Airflow, DAGs, psycopg2 |
| 04 | Bronze Data Lake | ✅ Complete | MinIO, boto3, S3-compatible storage |
| 05 | PySpark Silver Layer | 🔲 Upcoming | Apache Spark, Iceberg |
| 06 | dbt Gold Layer | 🔲 Upcoming | dbt-core, dbt-spark |
| 07 | Data Quality | 🔲 Upcoming | Great Expectations |
| 08 | Kafka Streaming | 🔲 Upcoming | Apache Kafka, Spark Streaming |
| 09 | FastF1 Telemetry | 🔲 Upcoming | FastF1, multi-source ingestion |
| 10 | Cloud Migration (AWS) | 🔲 Upcoming | Terraform, S3, MSK, Glue, Redshift |
| 11 | Power BI Dashboard | 🔲 Upcoming | Power BI, Redshift |
| 12 | Machine Learning | 🔲 Upcoming | scikit-learn, MLflow, XGBoost |

---

## 🚀 Quick Start

> **Everything runs on GitHub Codespaces — no local installation needed.**

### First Time Only
```bash
bash scripts/setup.sh
```

### Every Time You Reopen Codespace
```bash
bash scripts/start.sh
```

### Run the Full Pipeline
```bash
bash scripts/step03.sh   # Airflow handles Step 01 + Step 02 automatically
bash scripts/step04.sh   # Upload to Bronze layer
```

### Manual Run (debugging only)
```bash
bash scripts/step01.sh   # pull data manually
bash scripts/step02.sh   # load warehouse manually
bash scripts/step04.sh   # upload to Bronze
```

### Save Your Work to GitHub
```bash
bash scripts/git_save.sh "your message here"
```

---

## 📋 Scripts Reference

| Script | Usage | Purpose |
|--------|-------|---------|
| `setup.sh` | `bash scripts/setup.sh` | Run **once** after cloning — installs everything |
| `start.sh` | `bash scripts/start.sh` | Run **every session** — starts all services |
| `stop.sh` | `bash scripts/stop.sh` | Stop all services cleanly |
| `step01.sh` | `bash scripts/step01.sh` | Pull F1 data from Jolpica API |
| `step01.sh` | `bash scripts/step01.sh 2024` | Pull a single season only |
| `step02.sh` | `bash scripts/step02.sh` | Load raw CSVs into PostgreSQL DWH |
| `step03.sh` | `bash scripts/step03.sh` | Trigger Airflow DAGs |
| `step04.sh` | `bash scripts/step04.sh` | Upload raw CSVs to Bronze layer (MinIO) |
| `git_save.sh` | `bash scripts/git_save.sh "message"` | Commit and push to GitHub |

### Daily Workflow
```
Morning:
  bash scripts/start.sh          ← starts everything + pulls latest code

Work on the project...

Save progress:
  bash scripts/git_save.sh "feat: what I did today"

End of day:
  bash scripts/stop.sh           ← stop everything cleanly
```

---

## ✅ Step 01 — Simple Python ETL

### What it does
Pulls F1 historical data (2015–2025) from the [Jolpica API](https://api.jolpi.ca)
(free Ergast replacement) and saves it locally as CSV files and an SQLite database.

### Data extracted
| Entity | Rows |
|--------|------|
| Races | 233 |
| Drivers | 71 |
| Constructors | 18 |
| Circuits | 32 |
| Race Results | 4,698 |
| Qualifying | 4,684 |
| Pit Stops | 8,364 |
| Lap Times | 35,446 |

### Run it
```bash
bash scripts/step01.sh             # all seasons
bash scripts/step01.sh 2024        # single season (faster, for testing)
```

### Key features
- ✅ Retry logic on API failures (tenacity)
- ✅ Pagination support (handles large datasets)
- ✅ Incremental loading (skips already downloaded data)
- ✅ Structured JSON logging throughout
- ✅ Rate limit handling — 429 errors trigger 60s wait + retry

### Known limitation
Jolpica API returns incomplete lap time data (~35K rows vs expected ~800K).
This will be resolved in Step 09 with FastF1 telemetry integration.

---

## ✅ Step 02 — Local Data Warehouse (Star Schema)

### What it does
Reads the raw CSVs from Step 01 and loads them into a PostgreSQL
Data Warehouse modeled as a **Star Schema**.

### Star Schema Design
```
                    dim_drivers
                         │
dim_circuits ── fact_race_results ── dim_constructors
                         │
                    dim_races
                         │
                    dim_dates
```

### Warehouse tables
| Table | Type | Rows |
|-------|------|------|
| dim_drivers | Dimension | 71 |
| dim_constructors | Dimension | 18 |
| dim_circuits | Dimension | 32 |
| dim_races | Dimension | 233 |
| dim_dates | Dimension | 233 |
| fact_race_results | Fact | 4,698 |
| fact_lap_times | Fact | 35,446 |
| fact_pit_stops | Fact | 8,364 |
| fact_qualifying | Fact | 4,684 |

### Run it
```bash
bash scripts/step02.sh
```

### Example queries
```sql
-- Top 10 drivers by total points 2015–2025
SELECT d.full_name, SUM(f.points) AS total_points
FROM fact_race_results f
JOIN dim_drivers d ON f.driver_key = d.driver_key
GROUP BY d.full_name
ORDER BY total_points DESC
LIMIT 10;

-- Most wins per season
SELECT r.season, d.full_name, COUNT(*) AS wins
FROM fact_race_results f
JOIN dim_drivers d ON f.driver_key = d.driver_key
JOIN dim_races r ON f.race_key = r.race_key
WHERE f.finish_position = 1
GROUP BY r.season, d.full_name
ORDER BY wins DESC
LIMIT 10;
```

### Key features
- ✅ PostgreSQL running in Docker (reproducible)
- ✅ Star Schema with surrogate keys
- ✅ Foreign key relationships enforced
- ✅ Deduplication before loading
- ✅ Idempotent loader (safe to re-run)
- ✅ Graceful handling of missing files (lap_times.csv)

---

## ✅ Step 03 — Apache Airflow Orchestration

### What it does
Wraps the manual pipeline scripts into Apache Airflow DAGs that run
automatically on a schedule, with retries, logging, and a Web UI for monitoring.

### DAG Design
```
dag_ingest_f1 (Every Monday 02:00 UTC)
├── ingest_current_season   (latest season)
└── ingest_historical_seasons (all previous seasons)

dag_load_warehouse (Every Monday 05:00 UTC)
├── load_warehouse
└── validate_row_counts

dag_ingest_to_bronze (Every Monday 03:00 UTC)
└── upload_to_bronze
```

### Run it
```bash
bash scripts/start.sh      # starts Airflow automatically
bash scripts/step03.sh     # triggers the DAGs + unpauses them
```

Then open **port 8080** in the Codespaces Ports tab → login with `admin / admin123`

### Key features
- ✅ Three DAGs — ingestion, warehouse loading, Bronze upload
- ✅ Auto-unpause DAGs on trigger
- ✅ Task dependency management (`>>` operator)
- ✅ Automatic retries on failure
- ✅ Full run history and task logs in Web UI
- ✅ REST API enabled for VS Code Airflow extension

### Lessons learned
- `ExternalTaskSensor` matches runs by exact timestamp — removed in favor of manual trigger order
- Airflow 2.9.3 requires SQLAlchemy 1.4 — solved by using psycopg2 directly
- Always enable `enable_proxy_fix = True` when running behind a proxy (Codespaces)
- DAGs start paused by default — always unpause before triggering

---

## ✅ Step 04 — Bronze Data Lake (MinIO)

### What it does
Introduces a proper **Data Lake** by adding MinIO (S3-compatible object storage)
to the stack. Raw CSV files are uploaded to a structured Bronze layer in MinIO,
mirroring exactly what will run on AWS S3 in Step 10.

### What is MinIO?
MinIO is an open-source object storage system with a 100% compatible AWS S3 API.
It runs locally in Docker and stores data on the Codespace disk.
When we migrate to AWS in Step 10, only the endpoint URL changes — zero code changes.

```
Development:   MinIO (Docker)  →  localhost:9000
Production:    AWS S3          →  s3://f1-datalake-prod/
```

### Bronze Layer Structure
```
s3://f1-bronze/
└── ergast/
    ├── races/races.csv
    ├── drivers/drivers.csv
    ├── constructors/constructors.csv
    ├── circuits/circuits.csv
    ├── results/results.csv
    ├── qualifying/qualifying.csv
    ├── pit_stops/pit_stops.csv
    └── lap_times/lap_times.csv
```

### Run it
```bash
bash scripts/step04.sh          # incremental — skips existing files
```

### Force re-upload (when data changes)
```bash
python3 -c "
from datalake.bronze.ingest_to_bronze import ingest_to_bronze
ingest_to_bronze(force=True)
"
```

### MinIO UI
Open **port 9001** in Codespaces Ports tab
- **Username:** `f1minio`
- **Password:** `f1minio123`

### Key features
- ✅ MinIO running in Docker alongside PostgreSQL
- ✅ Identical boto3 API to AWS S3 — zero code changes needed for cloud migration
- ✅ Structured folder hierarchy (source/entity/file)
- ✅ Incremental uploads (skips already uploaded files)
- ✅ Force re-upload flag for data updates
- ✅ `storage_client.py` abstraction — switches between MinIO and S3 via env var
- ✅ dag_ingest_to_bronze DAG in Airflow

### Lessons learned
- MinIO is S3 under the hood — same boto3 client, same API calls, same bucket structure
- Incremental checks need a force flag when source data is updated
- Bronze = raw unmodified data — no transformations, full audit trail

---

## 🗂️ Project Structure

```
f1-data-engineering/
├── ingestion/
│   ├── ergast_client.py          ← Jolpica API client (retry, pagination, 429 handling)
│   └── extract_all.py            ← Main ETL runner (8 extractors)
├── warehouse/
│   ├── schema.sql                ← Star Schema DDL (9 tables)
│   └── load_warehouse.py         ← CSV → PostgreSQL loader (psycopg2)
├── datalake/
│   ├── storage_client.py         ← Unified S3/MinIO client (env-based switching)
│   └── bronze/
│       └── ingest_to_bronze.py   ← Upload CSVs to Bronze layer
├── orchestration/
│   └── dags/
│       ├── dag_ingest_f1.py      ← Ingestion DAG
│       ├── dag_load_warehouse.py ← Warehouse load DAG
│       └── dag_ingest_to_bronze.py ← Bronze upload DAG
├── scripts/
│   ├── setup.sh                  ← First-time setup (installs everything)
│   ├── start.sh                  ← Start all services + git pull
│   ├── stop.sh                   ← Stop all services
│   ├── step01.sh                 ← Pull F1 data from API
│   ├── step02.sh                 ← Load data into PostgreSQL DWH
│   ├── step03.sh                 ← Trigger Airflow DAGs
│   ├── step04.sh                 ← Upload to Bronze layer (MinIO)
│   └── git_save.sh               ← Commit and push to GitHub
├── utils/
│   └── logger.py                 ← Structured JSON logging
├── docker/
│   └── docker-compose.yml        ← PostgreSQL + MinIO containers
├── data/
│   └── raw/                      ← gitignored — lives locally only
├── airflow/                      ← gitignored — Airflow metadata
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack (Current)

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Pipeline code |
| Pandas | 2.2.2 | Data manipulation |
| Requests + Tenacity | Latest | API calls with retry |
| psycopg2 | 2.9.9 | PostgreSQL connector |
| boto3 | 1.34.144 | S3/MinIO client |
| PostgreSQL | 15 | Data Warehouse |
| MinIO | Latest | Local S3-compatible object storage |
| Apache Airflow | 2.9.3 | Pipeline orchestration |
| Docker Compose | 2.40 | Local service management |
| SQLite | Built-in | Quick local storage (Step 01) |

---

## 📝 Commit Convention

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature or step |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Code improvement |
| `test:` | Adding tests |
| `chore:` | Setup, scripts, config |