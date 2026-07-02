"""
DAG: dag_ingest_to_bronze
--------------------------
Uploads raw CSV files from data/raw/ to MinIO Bronze layer.
Runs after dag_ingest_f1 completes.
Schedule: Every Monday at 03:00 UTC (after ingestion)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from datalake.bronze.ingest_to_bronze import ingest_to_bronze

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          3,
    'retry_delay':      timedelta(minutes=5),
}

with DAG(
    dag_id='dag_ingest_to_bronze',
    description='Upload raw F1 CSVs to MinIO Bronze layer',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 3 * * 1',
    catchup=False,
    tags=['f1', 'bronze', 'datalake', 'step-04'],
) as dag:

    upload_to_bronze = PythonOperator(
        task_id='upload_to_bronze',
        python_callable=ingest_to_bronze,
        op_kwargs={'force': True},
        execution_timeout=timedelta(minutes=30),
    )

    upload_to_bronze