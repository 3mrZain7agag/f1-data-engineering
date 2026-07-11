"""
Export Gold Layer to CSV — Step 09
------------------------------------
Uses `dbt show` to pull each Gold model's full result set (as JSON)
and writes it out as a flat CSV file for Power BI (or any BI tool).

We shell out to dbt rather than opening our own Spark session, because
dbt-spark's session mode uses a Hive-enabled SparkSession backed by a
persistent local metastore (metastore_db/) that only dbt's own process
knows how to connect to correctly. Reproducing that config independently
is fragile; dbt already knows how to read its own tables.

Usage (run from the repo root):
    python3 -m export.export_gold_to_csv
"""

import os
import json
import subprocess
import pandas as pd
from utils.logger import get_logger

log = get_logger(__name__)

GOLD_MODELS = [
    "dim_drivers",
    "dim_circuits",
    "dim_races",
    "fact_race_results",
    "fact_lap_times",
    "fact_pit_stops",
    "agg_driver_season_stats",
    "agg_constructor_season_stats",
    "agg_circuit_stats",
]

DBT_PROJECT_DIR = "dbt/f1_gold"
OUTPUT_DIR = "exports/gold"


def export_gold_to_csv():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    exported = []
    failed = []

    for model in GOLD_MODELS:
        log.info(f"Exporting: {model}")
        try:
            result = subprocess.run(
                [
                    "dbt", "show",
                    "--select", model,
                    "--limit", "-1",
                    "--output", "json",
                    "--quiet",
                ],
                cwd=DBT_PROJECT_DIR,
                capture_output=True,
                text=True,
                check=True,
            )

            # dbt's --quiet still prints Spark/Ivy logs to stdout before the
            # JSON payload, so find the JSON object by locating the first '{'
            stdout = result.stdout
            json_start = stdout.index("{")
            payload = json.loads(stdout[json_start:])

            rows = payload["show"]
            df = pd.DataFrame(rows)

            out_path = os.path.join(OUTPUT_DIR, f"{model}.csv")
            df.to_csv(out_path, index=False)

            log.info(f"✅ Exported {model} ({len(df)} rows) → {out_path}")
            exported.append((model, len(df)))

        except subprocess.CalledProcessError as e:
            log.error(f"❌ Failed to export {model}: {e.stderr[-500:]}")
            failed.append(model)
        except (ValueError, KeyError) as e:
            log.error(f"❌ Failed to parse output for {model}: {e}")
            failed.append(model)

    print("\n── Gold Export Summary ──────────────────────")
    for model, rows in exported:
        print(f"  ✅ {model:<32} {rows:>6} rows")
    for model in failed:
        print(f"  ❌ {model:<32} FAILED")
    print(f"\n  Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("──────────────────────────────────────────────\n")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    export_gold_to_csv()