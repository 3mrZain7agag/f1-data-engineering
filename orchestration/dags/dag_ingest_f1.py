"""
DAG: dag_ingest_f1
------------------
Pulls F1 historical data from Jolpica API → saves to data/raw/ CSVs.
Schedule: Every Monday at 02:00 UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from ingestion.extract_all import main as run_ingestion

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          3,
    'retry_delay':      timedelta(minutes=5),
}

with DAG(
    dag_id='dag_ingest_f1',
    description='Ingest F1 data from Jolpica API to CSV files',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 2 * * 1',
    catchup=False,
    tags=['f1', 'ingestion', 'step-01'],
) as dag:

    ingest_current_season = PythonOperator(
        task_id='ingest_current_season',
        python_callable=run_ingestion,
        op_kwargs={'seasons': [2024]},
        execution_timeout=timedelta(hours=2),
    )

    ingest_historical = PythonOperator(
        task_id='ingest_historical_seasons',
        python_callable=run_ingestion,
        op_kwargs={'seasons': list(range(2015, 2024))},
        execution_timeout=timedelta(hours=3),
    )

    # Current season first, then backfill historical
    ingest_current_season >> ingest_historical
