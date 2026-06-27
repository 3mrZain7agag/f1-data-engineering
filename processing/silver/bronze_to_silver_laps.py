"""
Bronze → Silver: Lap Times
---------------------------
Converts lap time strings 'm:ss.mmm' to milliseconds.
Usage: python -m processing.silver.bronze_to_silver_laps
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SCHEMA = StructType([
    StructField("lap_number", IntegerType(), True),
    StructField("driver_id",  StringType(),  True),
    StructField("position",   IntegerType(), True),
    StructField("time",       StringType(),  True),
    StructField("season",     IntegerType(), True),
    StructField("round",      IntegerType(), True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/lap_times/lap_times.csv"
SILVER_TABLE = "f1_catalog.silver.lap_times"


def bronze_to_silver_laps():
    spark = get_spark("bronze_to_silver_laps")
    log.info("Starting Bronze → Silver: lap_times")

    df = spark.read.csv(BRONZE_PATH, schema=SCHEMA, header=True, nullValue="\\N")
    log.info(f"Bronze rows: {df.count()}")

    df_clean = (
        df
        .withColumnRenamed("time", "lap_time")

        # Convert 'm:ss.mmm' → milliseconds
        .withColumn("lap_time_ms",
            F.when(
                F.col("lap_time").isNotNull() & (F.col("lap_time") != ""),
                (
                    F.split(F.col("lap_time"), ":")[0].cast("int") * 60000 +
                    F.split(F.col("lap_time"), ":")[1].cast("double") * 1000
                ).cast("int")
            ).otherwise(None)
        )

        # Filter unrealistic lap times (< 50s or > 5min)
        .filter(
            F.col("lap_time_ms").isNull() |
            ((F.col("lap_time_ms") >= 50000) & (F.col("lap_time_ms") <= 300000))
        )

        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())
        .dropDuplicates(["season", "round", "driver_id", "lap_number"])
        .filter(
            F.col("season").isNotNull() &
            F.col("driver_id").isNotNull() &
            F.col("lap_number").isNotNull()
        )
        .orderBy("season", "round", "lap_number")
    )

    log.info(f"Silver rows after cleaning: {df_clean.count()}")

    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")
    df_clean.writeTo(SILVER_TABLE).tableProperty("format-version", "2").createOrReplace()

    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Lap Times: {count:,} rows ─────────────────")
    spark.sql(f"""
        SELECT season, round, driver_id, lap_number, lap_time, lap_time_ms
        FROM {SILVER_TABLE}
        WHERE season = 2024 AND round = 1
        ORDER BY lap_number, position LIMIT 5
    """).show(truncate=False)
    spark.stop()
    log.info("✅ Bronze → Silver: lap_times complete")


if __name__ == "__main__":
    bronze_to_silver_laps()