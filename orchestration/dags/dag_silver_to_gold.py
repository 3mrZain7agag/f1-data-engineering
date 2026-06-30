"""
DAG: dag_silver_to_gold
------------------------
Runs dbt Gold layer transformations.
Schedule: Every Monday at 05:00 UTC (after Silver layer)
"""

import os
import subprocess
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
os.environ["PATH"] = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{os.environ['PATH']}"

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}


def run_dbt_gold():
    """Run dbt models and tests for Gold layer."""
    import shutil
    dbt_dir = '/workspaces/f1-data-engineering/dbt/f1_gold'

    # Clean spark-warehouse to avoid LOCATION_ALREADY_EXISTS errors
    warehouse_path = f'{dbt_dir}/spark-warehouse'
    if os.path.exists(warehouse_path):
        shutil.rmtree(warehouse_path)
        print(f'Cleaned {warehouse_path}')

    target_path = f'{dbt_dir}/target'
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
        print(f'Cleaned {target_path}')

    env = os.environ.copy()
    env['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
    env['PATH']      = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{env['PATH']}"

    print("Running dbt run --full-refresh...")
    result = subprocess.run(
        ['dbt', 'run', '--full-refresh'],
        cwd=dbt_dir,
        env=env,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt run failed:\n{result.stderr}")


def run_dbt_tests():
    """Run dbt tests to validate Gold layer."""
    dbt_dir = '/workspaces/f1-data-engineering/dbt/f1_gold'

    env = os.environ.copy()
    env['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
    env['PATH']      = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{env['PATH']}"

    print("Running dbt test...")
    result = subprocess.run(
        ['dbt', 'test'],
        cwd=dbt_dir,
        env=env,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt tests failed:\n{result.stderr}")
    print("✅ All dbt tests passed!")


with DAG(
    dag_id='dag_silver_to_gold',
    description='dbt Gold layer transformations and tests',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 5 * * 1',
    catchup=False,
    tags=['f1', 'gold', 'dbt', 'step-06'],
) as dag:

    t_dbt_run = PythonOperator(
        task_id='dbt_run',
        python_callable=run_dbt_gold,
        execution_timeout=timedelta(hours=1),
    )

    t_dbt_test = PythonOperator(
        task_id='dbt_test',
        python_callable=run_dbt_tests,
        execution_timeout=timedelta(minutes=30),
    )

    t_dbt_run >> t_dbt_test
