"""
Data Quality — Silver: lap_times
-----------------------------------
Validates the Silver lap_times table before it flows to Gold.

Usage:
    python -m quality.checkpoints.validate_lap_times
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

import great_expectations as gx
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SILVER_TABLE = "f1_catalog.silver.lap_times"


def validate_lap_times() -> bool:
    spark = get_spark("validate_lap_times")
    log.info(f"Validating: {SILVER_TABLE}")

    df = spark.sql(f"SELECT * FROM {SILVER_TABLE}")
    pdf = df.toPandas()

    context = gx.get_context(mode="ephemeral")
    validator = context.sources.pandas_default.read_dataframe(pdf)

    results = []

    # 1. driver_id not null
    r = validator.expect_column_values_to_not_be_null("driver_id")
    results.append(("driver_id not null", r.success))

    # 2. lap_number must be positive
    r = validator.expect_column_values_to_be_between(
        "lap_number", min_value=1, max_value=100
    )
    results.append(("lap_number in range [1-100]", r.success))

    # 3. lap_time_ms must be realistic (50s - 5min), allow nulls
    non_null_laps = pdf[pdf["lap_time_ms"].notna()]
    if len(non_null_laps) > 0:
        in_range = non_null_laps["lap_time_ms"].between(50000, 300000)
        pct_valid = in_range.sum() / len(non_null_laps)
        results.append(("lap_time_ms in range [50s-5min]", pct_valid >= 0.99))
    else:
        results.append(("lap_time_ms in range [50s-5min]", True))

    # 4. no duplicate (season, round, driver_id, lap_number)
    pdf["_dedup_key"] = (
        pdf["season"].astype(str) + "_" +
        pdf["round"].astype(str) + "_" +
        pdf["driver_id"].astype(str) + "_" +
        pdf["lap_number"].astype(str)
    )
    dup_count = pdf["_dedup_key"].duplicated().sum()
    results.append(("no duplicate season+round+driver+lap", dup_count == 0))

    # ── Report ──────────────────────────────────────────────
    print("\n── Data Quality Report: silver.lap_times ────────")
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {check_name}")
        if not passed:
            all_passed = False
    print(f"\n  Total rows validated: {len(pdf):,}")
    print("──────────────────────────────────────────────────\n")

    spark.stop()

    if all_passed:
        log.info("✅ All expectations passed for lap_times")
    else:
        log.info("❌ Some expectations FAILED for lap_times")

    return all_passed


if __name__ == "__main__":
    success = validate_lap_times()
    sys.exit(0 if success else 1)