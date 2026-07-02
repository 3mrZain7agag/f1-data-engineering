"""
Data Quality — Silver: race_results
--------------------------------------
Validates the Silver race_results table before it's allowed
to flow into the Gold layer (dbt).

Expectations are derived from:
- F1 domain knowledge (position range, points range)
- Schema requirements from Step 05 (non-null join keys)
- Uniqueness constraints (no duplicate driver+race entries)

Usage:
    python -m quality.checkpoints.validate_race_results
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

import great_expectations as gx
from processing.silver.spark_session import get_spark
from utils.logger import get_logger

log = get_logger(__name__)

SILVER_TABLE = "f1_catalog.silver.race_results"


def validate_race_results() -> bool:
    """
    Runs data quality checks on Silver race_results.
    Returns True if all critical checks pass, False otherwise.
    """
    spark = get_spark("validate_race_results")
    log.info(f"Validating: {SILVER_TABLE}")

    df = spark.sql(f"SELECT * FROM {SILVER_TABLE}")
    pdf = df.toPandas()  # GE works on pandas for simplicity here

    context = gx.get_context(mode="ephemeral")
    validator = context.sources.pandas_default.read_dataframe(pdf)

    results = []

    # ── Critical Expectations ──────────────────────────────

    # 1. season must never be null
    r = validator.expect_column_values_to_not_be_null("season")
    results.append(("season not null", r.success))

    # 2. driver_id must never be null (join key)
    r = validator.expect_column_values_to_not_be_null("driver_id")
    results.append(("driver_id not null", r.success))

    # 3. position must be between 1 and 24 (max grid + margin)
    r = validator.expect_column_values_to_be_between(
        "position", min_value=1, max_value=24, mostly=0.95
    )
    results.append(("position in range [1-24]", r.success))

    # 4. points must be between 0 and 26 (sprint + race max)
    r = validator.expect_column_values_to_be_between(
        "points", min_value=0, max_value=26
    )
    results.append(("points in range [0-26]", r.success))

    # 5. no duplicate (season, round, driver_id) combinations
    pdf["_dedup_key"] = (
        pdf["season"].astype(str) + "_" +
        pdf["round"].astype(str) + "_" +
        pdf["driver_id"].astype(str)
    )
    dup_count = pdf["_dedup_key"].duplicated().sum()
    results.append(("no duplicate season+round+driver_id", dup_count == 0))

    # 6. status must not be null
    r = validator.expect_column_values_to_not_be_null("status")
    results.append(("status not null", r.success))

    # ── Report ──────────────────────────────────────────────
    print("\n── Data Quality Report: silver.race_results ────")
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
        log.info("✅ All expectations passed for race_results")
    else:
        log.info("❌ Some expectations FAILED for race_results")

    return all_passed


if __name__ == "__main__":
    success = validate_race_results()
    sys.exit(0 if success else 1)