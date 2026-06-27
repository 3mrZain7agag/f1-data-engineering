"""
Bronze → Silver: Races
-----------------------
Reads raw races CSV from Bronze layer (MinIO),
applies cleaning and schema enforcement,
writes clean Parquet to Silver layer as Iceberg table.

Usage:
    python -m processing.silver.bronze_to_silver_races
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, StringType, DateType
)
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

# ── Schema Definition ──────────────────────────────────────
RACES_SCHEMA = StructType([
    StructField("season",       IntegerType(), True),
    StructField("round",        IntegerType(), True),
    StructField("race_name",    StringType(),  True),
    StructField("circuit_id",   StringType(),  True),
    StructField("circuit_name", StringType(),  True),
    StructField("country",      StringType(),  True),
    StructField("locality",     StringType(),  True),
    StructField("date",         StringType(),  True),
    StructField("time",         StringType(),  True),
])

# ── Paths ──────────────────────────────────────────────────
BRONZE_PATH = "s3a://f1-bronze/ergast/races/races.csv"
SILVER_TABLE = "f1_catalog.silver.races"


def bronze_to_silver_races():
    spark = get_spark("bronze_to_silver_races")
    log.info("Starting Bronze → Silver: races")

    # ── 1. Read from Bronze ────────────────────────────────
    log.info(f"Reading from: {BRONZE_PATH}")
    df = spark.read.csv(
        BRONZE_PATH,
        schema=RACES_SCHEMA,
        header=True,
        nullValue="\\N",
    )
    log.info(f"Bronze rows: {df.count()}")

    # ── 2. Transform ───────────────────────────────────────
    df_clean = (
        df
        # Cast date properly
        .withColumn("race_date", F.to_date("date", "yyyy-MM-dd"))

        # Clean nulls
        .withColumn("time",         F.when(F.col("time") == "", None).otherwise(F.col("time")))
        .withColumn("circuit_name", F.when(F.col("circuit_name") == "", None).otherwise(F.col("circuit_name")))

        # Add metadata columns
        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())

        # Drop original date string, keep race_date
        .drop("date")

        # Deduplicate on natural key
        .dropDuplicates(["season", "round"])

        # Filter out nulls on key fields
        .filter(F.col("season").isNotNull() & F.col("round").isNotNull())

        # Sort for readability
        .orderBy("season", "round")
    )

    log.info(f"Silver rows after cleaning: {df_clean.count()}")

    # ── 3. Write to Silver (Iceberg) ───────────────────────
    log.info(f"Writing to: {SILVER_TABLE}")

    # Create Silver bucket if needed
    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")

    df_clean.writeTo(SILVER_TABLE) \
        .tableProperty("format-version", "2") \
        .createOrReplace()

    log.info("✅ Bronze → Silver: races complete")

    # ── 4. Validate ────────────────────────────────────────
    result = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}")
    count = result.collect()[0]["cnt"]
    print(f"\n── Silver Races Summary ───────────────────────")
    print(f"  Table:  {SILVER_TABLE}")
    print(f"  Rows:   {count:,}")
    print(f"  Sample:")
    spark.sql(f"""
        SELECT season, round, race_name, country, race_date
        FROM {SILVER_TABLE}
        ORDER BY season DESC, round DESC
        LIMIT 5
    """).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    bronze_to_silver_races()