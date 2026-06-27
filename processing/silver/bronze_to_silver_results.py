"""
Bronze → Silver: Race Results
------------------------------
Reads raw results CSV from Bronze layer,
applies cleaning, type enforcement, and deduplication,
writes to Silver layer as Iceberg table.

Usage:
    python -m processing.silver.bronze_to_silver_results
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, StringType, FloatType
)
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

RESULTS_SCHEMA = StructType([
    StructField("season",           IntegerType(), True),
    StructField("round",            IntegerType(), True),
    StructField("race_name",        StringType(),  True),
    StructField("driver_id",        StringType(),  True),
    StructField("constructor_id",   StringType(),  True),
    StructField("grid",             IntegerType(), True),
    StructField("position",         IntegerType(), True),
    StructField("position_text",    StringType(),  True),
    StructField("points",           FloatType(),   True),
    StructField("laps",             IntegerType(), True),
    StructField("status",           StringType(),  True),
    StructField("fastest_lap_rank", IntegerType(), True),
    StructField("fastest_lap_time", StringType(),  True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/results/results.csv"
SILVER_TABLE = "f1_catalog.silver.race_results"


def bronze_to_silver_results():
    spark = get_spark("bronze_to_silver_results")
    log.info("Starting Bronze → Silver: race_results")

    # ── 1. Read from Bronze ────────────────────────────────
    df = spark.read.csv(
        BRONZE_PATH,
        schema=RESULTS_SCHEMA,
        header=True,
        nullValue="\\N",
    )
    log.info(f"Bronze rows: {df.count()}")

    # ── 2. Transform ───────────────────────────────────────
    df_clean = (
        df
        # Standardize nulls
        .withColumn("position",
            F.when(F.col("position_text").isin(["R","D","E","W","F","N"]), None)
             .otherwise(F.col("position")))

        # Clean empty strings
        .withColumn("fastest_lap_time",
            F.when(F.col("fastest_lap_time") == "", None)
             .otherwise(F.col("fastest_lap_time")))

        # Add finish flag
        .withColumn("is_classified",
            F.col("position_text").rlike("^[0-9]+$"))

        # Add metadata
        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())

        # Deduplicate
        .dropDuplicates(["season", "round", "driver_id"])

        # Filter nulls on key fields
        .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("driver_id").isNotNull()
        )

        .orderBy("season", "round", "position")
    )

    log.info(f"Silver rows after cleaning: {df_clean.count()}")

    # ── 3. Write to Silver ─────────────────────────────────
    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")

    df_clean.writeTo(SILVER_TABLE) \
        .tableProperty("format-version", "2") \
        .createOrReplace()

    log.info("✅ Bronze → Silver: race_results complete")

    # ── 4. Validate ────────────────────────────────────────
    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Race Results Summary ─────────────────")
    print(f"  Table:  {SILVER_TABLE}")
    print(f"  Rows:   {count:,}")
    print(f"  Sample (2024 winners):")
    spark.sql(f"""
        SELECT season, round, driver_id, constructor_id, position, points, status
        FROM {SILVER_TABLE}
        WHERE season = 2024 AND position = 1
        ORDER BY round
        LIMIT 5
    """).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    bronze_to_silver_results()