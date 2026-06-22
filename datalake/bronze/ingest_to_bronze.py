"""
Bronze Layer Ingestion — Step 04
----------------------------------
Uploads raw CSV files from data/raw/ to the Bronze layer in MinIO.
Follows the path structure:
    s3://f1-bronze/ergast/{entity}/year={YYYY}/data.csv

Usage:
    python -m datalake.bronze.ingest_to_bronze
"""

import os
from pathlib import Path
from datalake.storage_client import (
    get_storage_client,
    ensure_bucket_exists,
    upload_file,
    object_exists,
    BRONZE_BUCKET,
)
from utils.logger import get_logger

log     = get_logger(__name__)
RAW_DIR = Path("data/raw")

# Maps each CSV file to its Bronze S3 path
BRONZE_PATHS = {
    "races.csv":        "ergast/races/races.csv",
    "drivers.csv":      "ergast/drivers/drivers.csv",
    "constructors.csv": "ergast/constructors/constructors.csv",
    "circuits.csv":     "ergast/circuits/circuits.csv",
    "results.csv":      "ergast/results/results.csv",
    "qualifying.csv":   "ergast/qualifying/qualifying.csv",
    "pit_stops.csv":    "ergast/pit_stops/pit_stops.csv",
    "lap_times.csv":    "ergast/lap_times/lap_times.csv",
}


def ingest_to_bronze() -> None:
    """Upload all raw CSVs to MinIO Bronze layer."""

    # ── Connect to MinIO ───────────────────────────────────
    client = get_storage_client()
    ensure_bucket_exists(client, BRONZE_BUCKET)

    log.info(f"Starting Bronze ingestion → s3://{BRONZE_BUCKET}/")
    uploaded = 0
    skipped  = 0

    for filename, s3_key in BRONZE_PATHS.items():
        local_path = RAW_DIR / filename

        # Check local file exists
        if not local_path.exists():
            log.info(f"Skipping {filename} — not found in data/raw/")
            skipped += 1
            continue

        # Incremental — skip if already uploaded
        if object_exists(client, BRONZE_BUCKET, s3_key):
            log.info(f"Already exists — skipping: s3://{BRONZE_BUCKET}/{s3_key}")
            skipped += 1
            continue

        # Upload
        upload_file(client, str(local_path), BRONZE_BUCKET, s3_key)
        uploaded += 1

    log.info(f"Bronze ingestion complete — uploaded: {uploaded}, skipped: {skipped}")

    # ── Print summary ──────────────────────────────────────
    print("\n── Bronze Layer Summary ───────────────────────")
    print(f"  Bucket:   s3://{BRONZE_BUCKET}/")
    print(f"  Uploaded: {uploaded} files")
    print(f"  Skipped:  {skipped} files")
    print("\n  Objects in Bronze:")

    from datalake.storage_client import list_objects
    objects = list_objects(client, BRONZE_BUCKET)
    for obj in sorted(objects):
        print(f"    s3://{BRONZE_BUCKET}/{obj}")
    print("───────────────────────────────────────────────\n")


if __name__ == "__main__":
    ingest_to_bronze()