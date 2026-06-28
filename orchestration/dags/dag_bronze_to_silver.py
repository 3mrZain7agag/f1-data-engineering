"""
DAG: dag_bronze_to_silver
--------------------------
Runs all Bronze → Silver PySpark transformations using Apache Iceberg.
Triggered after dag_ingest_to_bronze completes.
Schedule: Every Monday at 04:00 UTC

Requirements:
- MinIO running with f1-bronze and f1-silver buckets
- Java 17 installed (JAVA_HOME set correctly)
- PySpark 3.5.0 installed
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

# ── Ensure Java 17 is used for Spark ──────────────────────
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
os.environ["PATH"]      = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{os.environ['PATH']}"

from datalake.storage_client import get_storage_client, ensure_bucket_exists

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}


def ensure_silver_bucket():
    """Make sure f1-silver bucket exists before running Spark jobs."""
    client = get_storage_client()
    ensure_bucket_exists(client, 'f1-silver')
    ensure_bucket_exists(client, 'f1-gold')
    print("✅ MinIO buckets ready: f1-silver, f1-gold")


def run_silver_races():
    from processing.silver.bronze_to_silver_races import bronze_to_silver_races
    bronze_to_silver_races()


def run_silver_drivers():
    from processing.silver.bronze_to_silver_drivers import bronze_to_silver_drivers
    bronze_to_silver_drivers()


def run_silver_circuits():
    from processing.silver.bronze_to_silver_circuits import bronze_to_silver_circuits
    bronze_to_silver_circuits()


def run_silver_results():
    from processing.silver.bronze_to_silver_results import bronze_to_silver_results
    bronze_to_silver_results()


def run_silver_qualifying():
    from processing.silver.bronze_to_silver_qualifying import bronze_to_silver_qualifying
    bronze_to_silver_qualifying()


def run_silver_pitstops():
    from processing.silver.bronze_to_silver_pitstops import bronze_to_silver_pitstops
    bronze_to_silver_pitstops()


def run_silver_laps():
    from processing.silver.bronze_to_silver_laps import bronze_to_silver_laps
    bronze_to_silver_laps()


with DAG(
    dag_id='dag_bronze_to_silver',
    description='Bronze → Silver PySpark transformations with Apache Iceberg',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 4 * * 1',
    catchup=False,
    tags=['f1', 'silver', 'spark', 'iceberg', 'step-05'],
) as dag:

    t_buckets = PythonOperator(
        task_id='ensure_buckets',
        python_callable=ensure_silver_bucket,
        execution_timeout=timedelta(minutes=5),
    )

    t_races = PythonOperator(
        task_id='silver_races',
        python_callable=run_silver_races,
        execution_timeout=timedelta(minutes=15),
    )

    t_drivers = PythonOperator(
        task_id='silver_drivers',
        python_callable=run_silver_drivers,
        execution_timeout=timedelta(minutes=15),
    )

    t_circuits = PythonOperator(
        task_id='silver_circuits',
        python_callable=run_silver_circuits,
        execution_timeout=timedelta(minutes=15),
    )

    t_results = PythonOperator(
        task_id='silver_results',
        python_callable=run_silver_results,
        execution_timeout=timedelta(minutes=30),
    )

    t_qualifying = PythonOperator(
        task_id='silver_qualifying',
        python_callable=run_silver_qualifying,
        execution_timeout=timedelta(minutes=30),
    )

    t_pitstops = PythonOperator(
        task_id='silver_pitstops',
        python_callable=run_silver_pitstops,
        execution_timeout=timedelta(minutes=30),
    )

    t_laps = PythonOperator(
        task_id='silver_laps',
        python_callable=run_silver_laps,
        execution_timeout=timedelta(minutes=30),
    )

    # ── Task Dependencies ──────────────────────────────────
    # Buckets first, then reference tables, then fact tables
    t_buckets >> [t_races, t_drivers, t_circuits]
    t_races   >> t_results
    t_drivers >> t_results
    t_results >> [t_qualifying, t_pitstops, t_laps]