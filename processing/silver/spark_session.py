"""
Spark Session Factory — Step 05
---------------------------------
Creates a configured SparkSession with:
- MinIO (local) or AWS S3 (cloud) connectivity
- Apache Iceberg support for Silver/Gold layers
- Sensible defaults for local development

Usage:
    from processing.silver.spark_session import get_spark
    spark = get_spark("bronze_to_silver_races")
"""

import os
from pyspark.sql import SparkSession

# ── MinIO / S3 Config ──────────────────────────────────────
MINIO_ENDPOINT   = os.getenv("S3_ENDPOINT",          "http://localhost:9000")
AWS_ACCESS_KEY   = os.getenv("AWS_ACCESS_KEY_ID",    "f1minio")
AWS_SECRET_KEY   = os.getenv("AWS_SECRET_ACCESS_KEY", "f1minio123")

# ── Iceberg Warehouse ──────────────────────────────────────
SILVER_WAREHOUSE = os.getenv("SILVER_WAREHOUSE", "s3a://f1-silver/")
GOLD_WAREHOUSE   = os.getenv("GOLD_WAREHOUSE",   "s3a://f1-gold/")


def get_spark(app_name: str = "F1DataEngineering") -> SparkSession:
    """
    Returns a configured SparkSession.
    Works with MinIO locally and AWS S3 in production.
    """

    # Iceberg + Hadoop AWS JARs
    packages = ",".join([
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0",
        "org.apache.hadoop:hadoop-aws:3.3.4",
        "com.amazonaws:aws-java-sdk-bundle:1.12.262",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
    ])

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")   # use all local cores

        # ── Iceberg config ─────────────────────────────────
        .config("spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.f1_catalog",
                "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.f1_catalog.type", "hadoop")
        .config("spark.sql.catalog.f1_catalog.warehouse", SILVER_WAREHOUSE)

        # ── S3A / MinIO config ─────────────────────────────
        .config("spark.hadoop.fs.s3a.endpoint",                MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key",              AWS_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key",              AWS_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access",       "true")
        .config("spark.hadoop.fs.s3a.impl",
                "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider",
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled",  "false")

        # ── Performance ────────────────────────────────────
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "4")  # small data locally
        .config("spark.driver.memory", "2g")

        # ── Packages ───────────────────────────────────────
        .config("spark.jars.packages", packages)
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    return spark