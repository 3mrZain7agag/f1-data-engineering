"""
Spark Structured Streaming Consumer — Step 08
------------------------------------------------
Reads lap events from the Kafka topic in real-time (micro-batches)
and writes them to the Bronze layer in MinIO as Parquet files.

Usage:
    python -m streaming.consumer.spark_streaming_consumer
    (runs continuously until interrupted with Ctrl+C)
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, StringType, DoubleType
)
from processing.silver.spark_session import get_spark
from streaming.producer.topic_config import KAFKA_BOOTSTRAP_SERVERS, TOPICS
from utils.logger import get_logger

log = get_logger(__name__)

# ── Schema of the JSON events published by the producer ────
LAP_EVENT_SCHEMA = StructType([
    StructField("season",          IntegerType(), True),
    StructField("round",           IntegerType(), True),
    StructField("driver_id",       StringType(),  True),
    StructField("lap_number",      IntegerType(), True),
    StructField("position",        IntegerType(), True),
    StructField("lap_time",        StringType(),  True),
    StructField("lap_time_ms",     IntegerType(), True),
    StructField("event_timestamp", DoubleType(),  True),
])

BRONZE_STREAM_PATH      = "s3a://f1-bronze/kafka/lap_events/"
CHECKPOINT_PATH         = "s3a://f1-bronze/_checkpoints/lap_events/"


def start_streaming_consumer():
    spark = get_spark("kafka_streaming_consumer")
    log.info(f"Starting Spark Structured Streaming consumer for topic: {TOPICS['lap_events']}")

    # ── 1. Read stream from Kafka ───────────────────────────
    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", TOPICS["lap_events"])
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # ── 2. Parse JSON value ─────────────────────────────────
    parsed_stream = (
        raw_stream
        .selectExpr("CAST(value AS STRING) as json_value", "timestamp as kafka_timestamp")
        .select(
            F.from_json(F.col("json_value"), LAP_EVENT_SCHEMA).alias("data"),
            F.col("kafka_timestamp")
        )
        .select("data.*", "kafka_timestamp")
        .withColumn("_received_at", F.current_timestamp())
    )

    # ── 3. Write micro-batches to Bronze (Parquet) ──────────
    query = (
        parsed_stream.writeStream
        .format("parquet")
        .option("path", BRONZE_STREAM_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .outputMode("append")
        .trigger(processingTime="10 seconds")
        .start()
    )

    log.info("Streaming consumer started. Writing micro-batches every 10 seconds.")
    log.info(f"Output path: {BRONZE_STREAM_PATH}")
    log.info("Press Ctrl+C to stop.")

    query.awaitTermination()


if __name__ == "__main__":
    start_streaming_consumer()