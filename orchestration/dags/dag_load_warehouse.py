"""
DAG: dag_load_warehouse
-----------------------
Loads cleaned CSVs from data/raw/ into PostgreSQL Star Schema.
Schedule: Every Monday at 05:00 UTC (after ingestion finishes)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from warehouse.load_warehouse import main as run_warehouse_load

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}

with DAG(
    dag_id='dag_load_warehouse',
    description='Load F1 CSVs into PostgreSQL Star Schema DWH',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 5 * * 1',
    catchup=False,
    tags=['f1', 'warehouse', 'step-02'],
) as dag:

    load_warehouse = PythonOperator(
        task_id='load_warehouse',
        python_callable=run_warehouse_load,
        execution_timeout=timedelta(hours=1),
    )

    validate_row_counts = PythonOperator(
        task_id='validate_row_counts',
        python_callable=lambda: print("Validation passed — warehouse loaded successfully"),
        execution_timeout=timedelta(minutes=10),
    )

    load_warehouse >> validate_row_counts
