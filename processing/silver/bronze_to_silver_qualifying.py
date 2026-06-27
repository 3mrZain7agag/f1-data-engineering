"""
Bronze → Silver: Qualifying
----------------------------
Converts Q1/Q2/Q3 time strings to milliseconds.
Usage: python -m processing.silver.bronze_to_silver_qualifying
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SCHEMA = StructType([
    StructField("season",         IntegerType(), True),
    StructField("round",          IntegerType(), True),
    StructField("driver_id",      StringType(),  True),
    StructField("constructor_id", StringType(),  True),
    StructField("position",       IntegerType(), True),
    StructField("q1",             StringType(),  True),
    StructField("q2",             StringType(),  True),
    StructField("q3",             StringType(),  True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/qualifying/qualifying.csv"
SILVER_TABLE = "f1_catalog.silver.qualifying"


def time_str_to_ms(col_name):
    """Convert 'm:ss.mmm' string column to milliseconds integer."""
    return F.when(
        F.col(col_name).isNotNull() & (F.col(col_name) != ""),
        (
            F.split(F.col(col_name), ":")[0].cast("int") * 60000 +
            F.split(F.col(col_name), ":")[1].cast("double") * 1000
        ).cast("int")
    ).otherwise(None)


def bronze_to_silver_qualifying():
    spark = get_spark("bronze_to_silver_qualifying")
    log.info("Starting Bronze → Silver: qualifying")

    df = spark.read.csv(BRONZE_PATH, schema=SCHEMA, header=True, nullValue="\\N")

    df_clean = (
        df
        .withColumn("q1_ms", time_str_to_ms("q1"))
        .withColumn("q2_ms", time_str_to_ms("q2"))
        .withColumn("q3_ms", time_str_to_ms("q3"))
        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())
        .dropDuplicates(["season", "round", "driver_id"])
        .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("driver_id").isNotNull()
        )
        .orderBy("season", "round", "position")
    )

    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")
    df_clean.writeTo(SILVER_TABLE).tableProperty("format-version", "2").createOrReplace()

    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Qualifying: {count:,} rows ────────────────")
    spark.sql(f"""
        SELECT season, round, driver_id, position, q1, q1_ms, q3, q3_ms
        FROM {SILVER_TABLE}
        WHERE season = 2024 AND round = 1
        ORDER BY position LIMIT 5
    """).show(truncate=False)
    spark.stop()
    log.info("✅ Bronze → Silver: qualifying complete")


if __name__ == "__main__":
    bronze_to_silver_qualifying()