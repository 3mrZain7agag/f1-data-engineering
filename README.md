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

The project is built incrementally — each step adds one new concept on top of the previous one.
Every step produces a working, demonstrable system.

| Step | Title | Status | Key Tools |
|------|-------|--------|-----------|
| 01 | Simple Python ETL | ✅ Complete | Python, Pandas, SQLite |
| 02 | Local Data Warehouse | ✅ Complete | PostgreSQL, Star Schema, Docker |
| 03 | Airflow Orchestration | ✅ Complete | Apache Airflow, DAGs, psycopg2 |
| 04 | Bronze Data Lake | 🔲 Upcoming | MinIO, S3, Parquet |
| 05 | PySpark Silver Layer | 🔲 Upcoming | Apache Spark, Iceberg |
| 06 | dbt Gold Layer | 🔲 Upcoming | dbt-core, dbt-spark |
| 07 | Data Quality | 🔲 Upcoming | Great Expectations |
| 08 | Kafka Streaming | 🔲 Upcoming | Apache Kafka, Spark Streaming |
| 09 | FastF1 Telemetry | 🔲 Upcoming | FastF1, multi-source ingestion |
| 10 | Cloud Migration (AWS) | 🔲 Upcoming | Terraform, S3, MSK, Glue, Redshift |
| 11 | Power BI Dashboard | 🔲 Upcoming | Power BI, Redshift |
| 12 | Machine Learning | 🔲 Upcoming | scikit-learn, MLflow, XGBoost |

---

## ✅ Step 01 — Simple Python ETL

### What it does
Pulls 10 seasons of F1 historical data (2015–2024) from the
[Jolpica API](https://api.jolpi.ca) (free Ergast replacement) and saves it locally
as CSV files and an SQLite database.

### Data extracted
| Entity | Rows |
|--------|------|
| Races | 209 |
| Drivers | 54 |
| Constructors | 18 |
| Circuits | 32 |
| Race Results | 4,219 |
| Qualifying | 7,931 |
| Pit Stops | 14,261 |
| Lap Times | 59,447 |

### How to run
```bash
pip install -r requirements.txt

# Single season (test)
python -m ingestion.extract_all --seasons 2024

# Full run — all 10 seasons
python -m ingestion.extract_all
```

### Key features
- ✅ Retry logic on API failures (tenacity)
- ✅ Pagination support (handles large datasets)
- ✅ Incremental loading (skips already downloaded data)
- ✅ Structured JSON logging throughout

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
| dim_drivers | Dimension | 54 |
| dim_constructors | Dimension | 18 |
| dim_circuits | Dimension | 32 |
| dim_races | Dimension | 209 |
| dim_dates | Dimension | 209 |
| fact_race_results | Fact | 4,219 |
| fact_lap_times | Fact | 59,447 |
| fact_pit_stops | Fact | 14,261 |
| fact_qualifying | Fact | 7,931 |

### How to run
```bash
# Start PostgreSQL
docker-compose -f docker/docker-compose.yml up -d

# Create schema
docker exec -i f1_postgres psql -U f1user -d f1_warehouse < warehouse/schema.sql

# Load data
python -m warehouse.load_warehouse
```

### Example queries
```sql
-- Top 10 drivers by total points 2015–2024
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

---

## ✅ Step 03 — Apache Airflow Orchestration

### What it does
Wraps the manual pipeline scripts into Apache Airflow DAGs that run
automatically on a schedule, with retries, logging, and a Web UI for monitoring.

### DAG Design
```
dag_ingest_f1 (Every Monday 02:00 UTC)
├── ingest_current_season (2024)
└── ingest_historical_seasons (2015–2023)

dag_load_warehouse (Every Monday 05:00 UTC)
├── load_warehouse
└── validate_row_counts
```

### How to run
```bash
# Set Airflow home
export AIRFLOW_HOME=/workspaces/f1-data-engineering/airflow

# Initialize (first time only)
airflow db migrate
airflow users create --username admin --firstname Amr --lastname Hagag \
    --role Admin --email amr.hagag.prof@gmail.com --password admin123

# Terminal 1 — Web UI
airflow webserver --port 8080

# Terminal 2 — Scheduler
airflow scheduler
```

Then open port **8080** in Codespaces to access the Airflow Web UI.

### Key features
- ✅ Two DAGs — ingestion and warehouse loading
- ✅ Task dependency management (`>>` operator)
- ✅ Automatic retries on failure (3 retries, 5 min delay)
- ✅ Full run history and task logs in Web UI
- ✅ Configurable schedules (cron expressions)
- ✅ psycopg2 direct connection (bypasses SQLAlchemy version conflict)

### Lessons learned
- `ExternalTaskSensor` matches runs by exact timestamp — avoid for manually triggered DAGs
- Airflow 2.9.3 requires SQLAlchemy 1.4 which conflicts with pandas 2.2 `to_sql` — solved by using psycopg2 directly
- Always enable `enable_proxy_fix = True` when running Airflow behind a proxy (Codespaces)

---

## 🗂️ Project Structure

```
f1-data-engineering/
├── ingestion/
│   ├── ergast_client.py         ← Jolpica API client (retry, pagination)
│   └── extract_all.py           ← Main ETL runner (8 extractors)
├── warehouse/
│   ├── schema.sql               ← Star Schema DDL (9 tables)
│   └── load_warehouse.py        ← CSV → PostgreSQL loader (psycopg2)
├── orchestration/
│   └── dags/
│       ├── dag_ingest_f1.py     ← Ingestion DAG
│       └── dag_load_warehouse.py← Warehouse load DAG
├── utils/
│   └── logger.py                ← Structured JSON logging
├── docker/
│   └── docker-compose.yml       ← PostgreSQL container
├── data/
│   └── raw/                     ← gitignored — lives locally only
├── airflow/                     ← gitignored — Airflow metadata
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
| psycopg2 | Latest | PostgreSQL connector |
| PostgreSQL | 15 | Data Warehouse |
| Apache Airflow | 2.9.3 | Pipeline orchestration |
| Docker Compose | 2.40 | Local service management |
| SQLite | Built-in | Quick local storage (Step 01) |

---

## 🚀 Development Environment

This project runs entirely on **GitHub Codespaces** — no local installation needed.

1. Click **Code** → **Codespaces** → Open existing Codespace
2. All dependencies install via `pip install -r requirements.txt`
3. Docker and Docker Compose are available out of the box

---

## 📝 Commit Convention

| Prefix | Usage |
|--------|-------|
| `feat:` | New feature or step |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Code improvement |
| `test:` | Adding tests |
| `chore:` | Setup or config |