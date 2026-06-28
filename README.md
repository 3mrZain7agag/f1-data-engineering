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
| 05 | PySpark Silver Layer | ✅ Complete | Apache Spark 3.5, Iceberg, Java 17 |
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

### Check What's Running
```bash
bash scripts/status.sh
```

### Run the Full Pipeline
```bash
bash scripts/step03.sh   # Airflow: pull data + load warehouse
bash scripts/step04.sh   # Upload raw CSVs to Bronze (MinIO)
bash scripts/step05.sh   # Transform Bronze → Silver (PySpark + Iceberg)
```

### Save Your Work to GitHub
```bash
bash scripts/git_save.sh "your message here"
```

---

## 📋 Scripts Reference

### 🔧 Setup & Lifecycle

| Script | Usage | Purpose |
|--------|-------|---------|
| `setup.sh` | `bash scripts/setup.sh` | Run **once** — installs everything (Java 17, Airflow, creates buckets) |
| `start.sh` | `bash scripts/start.sh` | Start **all** services + git pull |
| `stop.sh` | `bash scripts/stop.sh` | Stop **all** services |
| `status.sh` | `bash scripts/status.sh` | Check all services + data summary |
| `git_save.sh` | `bash scripts/git_save.sh "msg"` | Commit and push to GitHub |

### 🐳 Individual Service Control

| Script | Usage | Purpose |
|--------|-------|---------|
| `start_postgres.sh` | `bash scripts/start_postgres.sh` | Start PostgreSQL only |
| `start_minio.sh` | `bash scripts/start_minio.sh` | Start MinIO only |
| `start_airflow.sh` | `bash scripts/start_airflow.sh` | Start Airflow webserver + scheduler |
| `start_spark.sh` | `bash scripts/start_spark.sh` | Start Spark master + worker |
| `stop_postgres.sh` | `bash scripts/stop_postgres.sh` | Stop PostgreSQL only |
| `stop_minio.sh` | `bash scripts/stop_minio.sh` | Stop MinIO only |
| `stop_airflow.sh` | `bash scripts/stop_airflow.sh` | Stop Airflow only |
| `stop_spark.sh` | `bash scripts/stop_spark.sh` | Stop Spark only |

### 📊 Pipeline Steps

| Script | Usage | Purpose |
|--------|-------|---------|
| `step01.sh` | `bash scripts/step01.sh` | Pull all F1 seasons from API (one by one) |
| `step01.sh` | `bash scripts/step01.sh 2024` | Pull a single season |
| `step02.sh` | `bash scripts/step02.sh` | Load CSVs into PostgreSQL DWH |
| `step03.sh` | `bash scripts/step03.sh` | Trigger + unpause Airflow DAGs |
| `step04.sh` | `bash scripts/step04.sh` | Upload raw CSVs to Bronze (MinIO) |
| `step05.sh` | `bash scripts/step05.sh` | Transform Bronze → Silver (PySpark) |

### 📅 Daily Workflow
```
Morning:
  bash scripts/start.sh          ← starts everything + pulls latest code
  bash scripts/status.sh         ← verify everything is running

Work on the project...

Save progress:
  bash scripts/git_save.sh "feat: what I did today"

End of day:
  bash scripts/stop.sh           ← stop everything cleanly
```

### 🔧 Troubleshooting
```bash
# Java version reset? Re-export Java 17
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Spark not starting?
bash scripts/stop_spark.sh
bash scripts/start_spark.sh

# Silver bucket missing after restart?
bash scripts/step05.sh  # recreates bucket automatically

# Rate limit on API? Run seasons one by one
bash scripts/step01.sh 2024
sleep 120
bash scripts/step01.sh 2025

# Force re-upload Bronze data
python3 -c "from datalake.bronze.ingest_to_bronze import ingest_to_bronze; ingest_to_bronze(force=True)"
```

---

## ✅ Step 01 — Simple Python ETL

### What it does
Pulls F1 historical data (2015–2025) from the [Jolpica API](https://api.jolpi.ca) and saves locally as CSV + SQLite.

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
| Lap Times | 32,747 |

### Run it
```bash
bash scripts/step01.sh             # all seasons (2min sleep between each)
bash scripts/step01.sh 2024        # single season
```

### Key features
- ✅ Retry logic + 429 rate limit handling (60s wait)
- ✅ One season at a time with 2min sleep
- ✅ Incremental loading (skips already downloaded data)
- ✅ Structured JSON logging

---

## ✅ Step 02 — Local Data Warehouse (Star Schema)

### What it does
Loads raw CSVs into PostgreSQL modeled as a **Star Schema**.

### Star Schema
```
                    dim_drivers
                         │
dim_circuits ── fact_race_results ── dim_constructors
                         │
                    dim_races
                         │
                    dim_dates
```

### Run it
```bash
bash scripts/step02.sh
```

### Example queries
```sql
SELECT d.full_name, SUM(f.points) AS total_points
FROM fact_race_results f
JOIN dim_drivers d ON f.driver_key = d.driver_key
GROUP BY d.full_name
ORDER BY total_points DESC
LIMIT 10;
```

---

## ✅ Step 03 — Apache Airflow Orchestration

### DAGs
```
dag_ingest_f1          → Step 01: pulls data from API        (Mon 02:00 UTC)
dag_ingest_to_bronze   → Step 04: uploads to MinIO Bronze    (Mon 03:00 UTC)
dag_bronze_to_silver   → Step 05: PySpark Silver layer       (Mon 04:00 UTC)
dag_load_warehouse     → Step 02: loads PostgreSQL DWH       (Mon 05:00 UTC)
```

### Run it
```bash
bash scripts/start.sh
bash scripts/step03.sh   # triggers + unpauses all 4 DAGs
# Open port 8080 → admin / admin123
```

---

## ✅ Step 04 — Bronze Data Lake (MinIO)

### Bronze Layer Structure
```
s3://f1-bronze/
└── ergast/
    ├── races/races.csv
    ├── results/results.csv
    ├── drivers/drivers.csv
    ├── circuits/circuits.csv
    ├── qualifying/qualifying.csv
    ├── pit_stops/pit_stops.csv
    └── lap_times/lap_times.csv
```

### Run it
```bash
bash scripts/step04.sh
# MinIO UI → Open port 9001 → f1minio / f1minio123
```

---

## ✅ Step 05 — PySpark Silver Layer (Apache Iceberg)

### What it does
Reads raw CSV files from Bronze, applies cleaning and type enforcement, and writes clean **Parquet files** as **Apache Iceberg tables** to the Silver layer in MinIO.

### What is Apache Iceberg?
Iceberg is a table format that sits on top of Parquet files in S3/MinIO. It adds ACID transactions, schema evolution, time travel, and upserts — making the Data Lake behave like a database.

### Transformations Applied
| Transformation | Applied To |
|---------------|-----------|
| Schema enforcement (correct types) | All tables |
| Null standardization (`\N`, `""` → NULL) | All tables |
| Deduplication on natural keys | All tables |
| Lap time strings → milliseconds | lap_times, qualifying |
| Pit stop duration → milliseconds | pit_stops |
| Date strings → DateType | races, drivers |
| DNF/DNS position → NULL | race_results |
| Unrealistic lap times filtered | lap_times (< 50s or > 5min) |

### Silver Tables
| Table | Rows | Key Additions |
|-------|------|--------------|
| silver.races | 233 | race_date (DateType) |
| silver.race_results | 4,698 | is_classified flag |
| silver.drivers | 71 | date_of_birth (DateType) |
| silver.circuits | 32 | lat/long (DoubleType) |
| silver.qualifying | 4,684 | q1_ms, q2_ms, q3_ms (milliseconds) |
| silver.pit_stops | 8,364 | duration_ms (milliseconds) |
| silver.lap_times | 32,747 | lap_time_ms (milliseconds) |

### Run it
```bash
bash scripts/step05.sh   # runs all 7 transformations + creates f1-silver bucket
```

### Architecture
```
MinIO Bronze (raw CSV)
       │
       ▼  PySpark 3.5 + Apache Iceberg 1.5
MinIO Silver (clean Parquet/Iceberg)
       │
  f1_catalog.silver.races
  f1_catalog.silver.race_results
  f1_catalog.silver.drivers
  ...
```

### Key features
- ✅ Apache Spark 3.5.0 running in Docker
- ✅ Java 17 (required — Java 25 is incompatible with Spark)
- ✅ Apache Iceberg 1.5 with ACID transactions
- ✅ Hadoop AWS + S3A connector for MinIO/S3 access
- ✅ `spark_session.py` — reusable factory, switches MinIO ↔ AWS S3 via env var
- ✅ `run_all_silver.py` — master runner for all 7 transformations
- ✅ f1-silver bucket auto-created by step05.sh

### Lessons learned
- Java 25 is incompatible with Spark 3.5 — must use Java 17
- `JAVA_HOME` resets on Codespace restart — added to `start.sh` and `~/.bashrc`
- CSV schema must match column order exactly when using StructType
- Iceberg warehouse bucket must exist before Spark can write — auto-created in setup.sh

---

## 🗂️ Project Structure

```
f1-data-engineering/
├── ingestion/
│   ├── ergast_client.py          ← API client (retry, pagination, 429)
│   └── extract_all.py            ← ETL runner (8 extractors)
├── warehouse/
│   ├── schema.sql                ← Star Schema DDL
│   └── load_warehouse.py         ← CSV → PostgreSQL (psycopg2)
├── datalake/
│   ├── storage_client.py         ← S3/MinIO unified client
│   └── bronze/
│       └── ingest_to_bronze.py   ← Upload to Bronze layer
├── processing/
│   └── silver/
│       ├── spark_session.py      ← Spark + Iceberg factory
│       ├── bronze_to_silver_races.py
│       ├── bronze_to_silver_results.py
│       ├── bronze_to_silver_drivers.py
│       ├── bronze_to_silver_circuits.py
│       ├── bronze_to_silver_qualifying.py
│       ├── bronze_to_silver_pitstops.py
│       ├── bronze_to_silver_laps.py
│       └── run_all_silver.py     ← Master runner
├── orchestration/dags/
│   ├── dag_ingest_f1.py
│   ├── dag_load_warehouse.py
│   ├── dag_ingest_to_bronze.py
│   └── dag_bronze_to_silver.py   ← Step 05: PySpark Silver DAG
├── scripts/
│   ├── setup.sh                  ← First-time setup (8 steps)
│   ├── start.sh                  ← Start all services
│   ├── stop.sh                   ← Stop all services
│   ├── status.sh                 ← Service + data status dashboard
│   ├── start_postgres.sh         ← PostgreSQL only
│   ├── start_minio.sh            ← MinIO only
│   ├── start_airflow.sh          ← Airflow only
│   ├── start_spark.sh            ← Spark only
│   ├── stop_postgres.sh          ← Stop PostgreSQL
│   ├── stop_minio.sh             ← Stop MinIO
│   ├── stop_airflow.sh           ← Stop Airflow
│   ├── stop_spark.sh             ← Stop Spark
│   ├── step01.sh                 ← Pull F1 data
│   ├── step02.sh                 ← Load warehouse
│   ├── step03.sh                 ← Trigger Airflow
│   ├── step04.sh                 ← Upload to Bronze
│   ├── step05.sh                 ← Bronze → Silver
│   └── git_save.sh               ← Save to GitHub
├── utils/
│   └── logger.py                 ← JSON logging
├── docker/
│   └── docker-compose.yml        ← PostgreSQL + MinIO + Spark
├── data/raw/                     ← gitignored
├── airflow/                      ← gitignored
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
| PySpark | 3.5.0 | Distributed data processing |
| Apache Iceberg | 1.5.0 | ACID table format on S3/MinIO |
| Java | 17 | Required for Spark |
| PostgreSQL | 15 | Data Warehouse |
| MinIO | Latest | Local S3-compatible storage |
| Apache Airflow | 2.9.3 | Pipeline orchestration |
| Docker Compose | 2.40 | Local service management |

---

## 🖥️ Service Ports

| Service | Port | Credentials |
|---------|------|-------------|
| PostgreSQL | 5432 | f1user / f1password |
| MinIO API | 9000 | f1minio / f1minio123 |
| MinIO UI | 9001 | f1minio / f1minio123 |
| Airflow UI | 8080 | admin / admin123 |
| Spark Master UI | 8082 | — |
| Spark Connect | 7077 | — |

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