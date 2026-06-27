"""
Bronze → Silver: Circuits
--------------------------
Usage: python -m processing.silver.bronze_to_silver_circuits
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SCHEMA = StructType([
    StructField("circuit_id",   StringType(), True),
    StructField("circuit_name", StringType(), True),
    StructField("locality",     StringType(), True),
    StructField("country",      StringType(), True),
    StructField("lat",          DoubleType(), True),
    StructField("long",         DoubleType(), True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/circuits/circuits.csv"
SILVER_TABLE = "f1_catalog.silver.circuits"


def bronze_to_silver_circuits():
    spark = get_spark("bronze_to_silver_circuits")
    log.info("Starting Bronze → Silver: circuits")

    df = spark.read.csv(BRONZE_PATH, schema=SCHEMA, header=True, nullValue="\\N")

    df_clean = (
        df
        .withColumn("_source",      F.lit("ergast"))
        .withColumn("_ingested_at", F.current_timestamp())
        .dropDuplicates(["circuit_id"])
        .filter(F.col("circuit_id").isNotNull())
        .orderBy("country")
    )

    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")
    df_clean.writeTo(SILVER_TABLE).tableProperty("format-version", "2").createOrReplace()

    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Circuits: {count:,} rows ──────────────────")
    spark.sql(f"SELECT circuit_id, circuit_name, country, lat, long FROM {SILVER_TABLE} LIMIT 5").show(truncate=False)
    spark.stop()
    log.info("✅ Bronze → Silver: circuits complete")


if __name__ == "__main__":
    bronze_to_silver_circuits()