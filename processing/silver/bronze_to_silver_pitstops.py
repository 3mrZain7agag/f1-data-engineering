"""
Bronze → Silver: Pit Stops
---------------------------
Converts duration strings to milliseconds.
Usage: python -m processing.silver.bronze_to_silver_pitstops
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SCHEMA = StructType([
    StructField("season",      IntegerType(), True),
    StructField("round",       IntegerType(), True),
    StructField("driver_id",   StringType(),  True),
    StructField("stop",        IntegerType(), True),
    StructField("lap",         IntegerType(), True),
    StructField("time",        StringType(),  True),
    StructField("duration",    StringType(),  True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/pit_stops/pit_stops.csv"
SILVER_TABLE = "f1_catalog.silver.pit_stops"


def bronze_to_silver_pitstops():
    spark = get_spark("bronze_to_silver_pitstops")
    log.info("Starting Bronze → Silver: pit_stops")

    df = spark.read.csv(BRONZE_PATH, schema=SCHEMA, header=True, nullValue="\\N")

    df_clean = (
        df
        .withColumnRenamed("stop", "stop_number")
        .withColumnRenamed("time", "time_of_day")

        # Convert duration to milliseconds
        .withColumn("duration_ms",
            F.when(
                F.col("duration").isNotNull() & (F.col("duration") != ""),
                (F.col("duration").cast("double") * 1000).cast("int")
            ).otherwise(None)
        )

        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())
        .dropDuplicates(["season", "round", "driver_id", "stop_number"])
        .filter(
            F.col("season").isNotNull() &
            F.col("driver_id").isNotNull()
        )
        .orderBy("season", "round", "lap")
    )

    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")
    df_clean.writeTo(SILVER_TABLE).tableProperty("format-version", "2").createOrReplace()

    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Pit Stops: {count:,} rows ─────────────────")
    spark.sql(f"""
        SELECT season, round, driver_id, stop_number, lap, duration, duration_ms
        FROM {SILVER_TABLE}
        WHERE season = 2024 AND round = 1
        ORDER BY lap LIMIT 5
    """).show(truncate=False)
    spark.stop()
    log.info("✅ Bronze → Silver: pit_stops complete")


if __name__ == "__main__":
    bronze_to_silver_pitstops()