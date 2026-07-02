"""
DAG: dag_data_quality
------------------------
Runs Great Expectations checkpoints on Silver layer.
Runs after dag_bronze_to_silver, before dag_silver_to_gold.
Schedule: Every Monday at 04:30 UTC
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
os.environ["PATH"] = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{os.environ['PATH']}"

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          1,
    'retry_delay':      timedelta(minutes=5),
}


def run_quality_checks():
    import sys
    sys.path.insert(0, '/workspaces/f1-data-engineering')
    from quality.checkpoints.run_all_checks import run_all_checks
    passed = run_all_checks()
    if not passed:
        raise Exception("Data quality checks failed — halting pipeline before Gold build")


with DAG(
    dag_id='dag_data_quality',
    description='Great Expectations checkpoints on Silver layer',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='30 4 * * 1',
    catchup=False,
    tags=['f1', 'quality', 'great_expectations', 'step-07'],
) as dag:

    t_quality_check = PythonOperator(
        task_id='run_quality_checks',
        python_callable=run_quality_checks,
        execution_timeout=timedelta(minutes=15),
    )

    t_quality_check
