#!/bin/bash
# =================================================================
# steps.sh — Reference dictionary for all pipeline steps
# Shows: prerequisites, what it does, how to run it
# Usage: bash scripts/steps.sh
# =================================================================

cat << 'EOF'

===================================================================
  F1 Data Engineering — Steps Dictionary
===================================================================

┌─────────────────────────────────────────────────────────────────┐
│ STEP 01 — Simple Python ETL                                     │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Pulls F1 historical data from Jolpica API        │
│                and saves it as CSV files + SQLite DB            │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: None (first step)                                │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step01.sh                           │
│                bash scripts/step01.sh 2024   (single season)    │
├─────────────────────────────────────────────────────────────────┤
│ Output:        data/raw/*.csv, data/raw/f1.db                   │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~3-4 hours (all seasons, one at a time)          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 02 — Local Data Warehouse (Star Schema)                    │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Loads raw CSVs into PostgreSQL Star Schema       │
│                (5 dimension + 4 fact tables)                    │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 01 complete, PostgreSQL running             │
│                (bash scripts/start_postgres.sh)                 │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step02.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        PostgreSQL tables in f1_warehouse DB             │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~10 seconds                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 03 — Apache Airflow Orchestration                          │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Triggers Airflow DAGs to automate Steps          │
│                01, 02, 04, 05, 06 end-to-end                    │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Airflow running (bash scripts/start_airflow.sh)  │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step03.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        Triggers dag_ingest_f1 (others run after)        │
├─────────────────────────────────────────────────────────────────┤
│ Monitor at:    Port 8080 → admin / admin123                     │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      Background — check Airflow UI for progress       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 04 — Bronze Data Lake (MinIO)                              │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Uploads raw CSVs to MinIO Bronze layer           │
│                (S3-compatible object storage)                   │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 01 complete, MinIO running                  │
│                (bash scripts/start_minio.sh)                    │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step04.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        s3://f1-bronze/ergast/*.csv                      │
├─────────────────────────────────────────────────────────────────┤
│ Monitor at:    Port 9001 → f1minio / f1minio123                 │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~10 seconds                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 05 — PySpark Silver Layer (Apache Iceberg)                 │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Cleans, types, and deduplicates Bronze data      │
│                using PySpark, writes as Iceberg tables          │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 04 complete, Spark running                  │
│                (bash scripts/start_spark.sh), Java 17 active    │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step05.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        s3://f1-silver/ (7 Iceberg tables)               │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~5-10 minutes                                    │
├─────────────────────────────────────────────────────────────────┤
│ Note:          Always verify: java -version shows 17            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 06 — dbt Gold Layer                                        │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Transforms Silver data into analytics-ready      │
│                Star Schema using dbt (joins, aggregations)      │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 05 complete, Java 17 active                 │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step06.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        dbt/f1_gold/spark-warehouse/gold_gold.db/        │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~2-3 minutes                                     │
├─────────────────────────────────────────────────────────────────┤
│ Known issue:   Gold tables stored locally, not in MinIO         │
│                (fixed in Step 10 with AWS Redshift)             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 07 — Data Quality (Great Expectations)                     │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Validates Silver layer data quality with         │
│                automated checkpoints before Gold build          │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 05 complete, Java 17 active                 │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step07.sh                           │
├─────────────────────────────────────────────────────────────────┤
│ Output:        Pass/Fail report for race_results, lap_times     │
├─────────────────────────────────────────────────────────────────┤
│ Duration:      ~30 seconds                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 08 — Kafka Streaming                            [UPCOMING] │
├─────────────────────────────────────────────────────────────────┤
│ What it does:  Simulates real-time race data via Kafka +        │
│                Spark Structured Streaming                       │
├─────────────────────────────────────────────────────────────────┤
│ Prerequisites: Step 06 complete                                 │
├─────────────────────────────────────────────────────────────────┤
│ Run with:      bash scripts/step08.sh  (not yet built)          │
└─────────────────────────────────────────────────────────────────┘

===================================================================
  Quick Reference
===================================================================

  Full pipeline (recommended order):
    bash scripts/setup.sh        (once)
    bash scripts/start.sh        (every session)
    bash scripts/step01.sh
    bash scripts/step02.sh
    bash scripts/step04.sh
    bash scripts/step05.sh
    bash scripts/step06.sh

  Or let Airflow handle 01, 02, 04 automatically:
    bash scripts/step03.sh
    (then manually run step05.sh and step06.sh after)

  Check status anytime:
    bash scripts/status.sh

===================================================================

EOF