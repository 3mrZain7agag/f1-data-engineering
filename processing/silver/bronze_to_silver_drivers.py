"""
Bronze → Silver: Drivers
--------------------------
Usage: python -m processing.silver.bronze_to_silver_drivers
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SCHEMA = StructType([
    StructField("driver_id",        StringType(), True),
    StructField("code",             StringType(), True),
    StructField("permanent_number", StringType(), True),
    StructField("given_name",       StringType(), True),
    StructField("family_name",      StringType(), True),
    StructField("full_name",        StringType(), True),
    StructField("date_of_birth",    StringType(), True),
    StructField("nationality",      StringType(), True),
])

BRONZE_PATH  = "s3a://f1-bronze/ergast/drivers/drivers.csv"
SILVER_TABLE = "f1_catalog.silver.drivers"


def bronze_to_silver_drivers():
    spark = get_spark("bronze_to_silver_drivers")
    log.info("Starting Bronze → Silver: drivers")

    df = spark.read.csv(BRONZE_PATH, schema=SCHEMA, header=True, nullValue="\\N")

    df_clean = (
        df
        .withColumn("date_of_birth", F.to_date("date_of_birth", "yyyy-MM-dd"))
        .withColumn("code",          F.when(F.col("code") == "", None).otherwise(F.col("code")))
        .withColumn("_source",       F.lit("ergast"))
        .withColumn("_ingested_at",  F.current_timestamp())
        .dropDuplicates(["driver_id"])
        .filter(F.col("driver_id").isNotNull())
        .orderBy("family_name")
    )

    spark.sql("CREATE NAMESPACE IF NOT EXISTS f1_catalog.silver")
    df_clean.writeTo(SILVER_TABLE).tableProperty("format-version", "2").createOrReplace()

    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {SILVER_TABLE}").collect()[0]["cnt"]
    print(f"\n── Silver Drivers: {count:,} rows ──────────────────")
    spark.sql(f"SELECT driver_id, full_name, nationality FROM {SILVER_TABLE} LIMIT 5").show(truncate=False)
    spark.stop()
    log.info("✅ Bronze → Silver: drivers complete")


if __name__ == "__main__":
    bronze_to_silver_drivers()