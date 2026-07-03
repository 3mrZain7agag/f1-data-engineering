"""
DAG: dag_kafka_replay
------------------------
Starts the Spark Structured Streaming consumer in the background,
then runs the race replay producer to simulate a live F1 race.

Note: The streaming consumer is a long-running process — this DAG
starts it detached (nohup) rather than as a blocking Airflow task,
since Airflow tasks are expected to complete, not run forever.

Schedule: Manual trigger only (not on a fixed schedule)

Configure the race to replay via Airflow Variables:
    f1_replay_season (default: 2024)
    f1_replay_round  (default: 1)
"""

import os
import subprocess
import time
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
os.environ["PATH"] = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{os.environ['PATH']}"

PROJECT_DIR = "/workspaces/f1-data-engineering"

default_args = {
    'owner':            'amr_hagag',
    'depends_on_past':  False,
    'email_on_failure': False,
    'retries':          1,
    'retry_delay':      timedelta(minutes=2),
}


def start_streaming_consumer():
    """Starts the Spark Streaming consumer as a detached background process."""
    env = os.environ.copy()
    env['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
    env['PATH']      = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{env['PATH']}"

    log_file = open('/tmp/f1_consumer_dag.log', 'w')
    process = subprocess.Popen(
        ['python', '-m', 'streaming.consumer.spark_streaming_consumer'],
        cwd=PROJECT_DIR,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    with open('/tmp/f1_consumer_dag.pid', 'w') as f:
        f.write(str(process.pid))

    print(f"Streaming consumer started with PID {process.pid}")
    print("Waiting 25 seconds for consumer to initialize...")
    time.sleep(25)


def run_race_replay():
    """Runs the producer to replay a race — season/round via Airflow Variables."""
    season = Variable.get("f1_replay_season", default_var="2024")
    round_num = Variable.get("f1_replay_round", default_var="1")

    env = os.environ.copy()
    env['JAVA_HOME'] = '/usr/lib/jvm/java-17-openjdk-amd64'
    env['PATH']      = f"/usr/lib/jvm/java-17-openjdk-amd64/bin:{env['PATH']}"

    result = subprocess.run(
        ['python', '-m', 'streaming.producer.race_replay_producer',
         '--season', str(season), '--round', str(round_num), '--speed', '50'],
        cwd=PROJECT_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Race replay producer failed:\n{result.stderr}")


def wait_for_final_batch():
    """Gives the streaming consumer time to process the last micro-batch."""
    print("Waiting 15 seconds for final micro-batch to process...")
    time.sleep(15)
    print("Streaming consumer continues running in the background.")
    print("To stop it manually: kill $(cat /tmp/f1_consumer_dag.pid)")


with DAG(
    dag_id='dag_kafka_replay',
    description='Kafka race replay producer + Spark Streaming consumer (manual trigger)',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['f1', 'streaming', 'kafka', 'step-08'],
) as dag:

    t_start_consumer = PythonOperator(
        task_id='start_streaming_consumer',
        python_callable=start_streaming_consumer,
        execution_timeout=timedelta(minutes=2),
    )

    t_run_replay = PythonOperator(
        task_id='run_race_replay',
        python_callable=run_race_replay,
        execution_timeout=timedelta(minutes=10),
    )

    t_wait = PythonOperator(
        task_id='wait_for_final_batch',
        python_callable=wait_for_final_batch,
        execution_timeout=timedelta(minutes=1),
    )

    t_start_consumer >> t_run_replay >> t_wait