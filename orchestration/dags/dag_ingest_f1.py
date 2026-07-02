"""
DAG: dag_ingest_f1
------------------
Pulls F1 historical data from Jolpica API → saves to data/raw/ CSVs.
Runs ONE SEASON AT A TIME with delays between tasks to avoid
429 rate limit errors from the Jolpica API (matches step01.sh logic).

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
    'retry_delay':      timedelta(minutes=3),
}

SEASONS = list(range(2015, 2026))  # 2015 through 2025 inclusive


def ingest_season(season: int):
    """Ingest a single season, then sleep 2 minutes to avoid 429 rate limits
    (matches the manual bash scripts/step01.sh behavior)."""
    import time
    run_ingestion(seasons=[season])
    if season != SEASONS[-1]:
        time.sleep(120)


with DAG(
    dag_id='dag_ingest_f1',
    description='Ingest F1 data from Jolpica API — one season at a time',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 2 * * 1',
    catchup=False,
    tags=['f1', 'ingestion', 'step-01'],
) as dag:

    previous_task = None

    for season in SEASONS:
        task = PythonOperator(
            task_id=f'ingest_season_{season}',
            python_callable=ingest_season,
            op_kwargs={'season': season},
            execution_timeout=timedelta(minutes=45),
        )

        # Chain tasks sequentially — Airflow's own scheduling gap
        # between tasks plus retry_delay provides natural spacing.
        # Explicit sleep avoided here since it would block a worker slot;
        # instead we rely on execution_timeout + retries on 429.
        if previous_task:
            previous_task >> task
        previous_task = task