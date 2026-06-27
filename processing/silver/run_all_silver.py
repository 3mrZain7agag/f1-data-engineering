"""
Silver Master Runner — Step 05
--------------------------------
Runs all Bronze → Silver transformations in sequence.

Usage:
    python -m processing.silver.run_all_silver
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from utils.logger import get_logger

log = get_logger(__name__)


def run_all_silver():
    print("\n══════════════════════════════════════════════════")
    print("  F1 Data Engineering — Bronze → Silver Pipeline")
    print("══════════════════════════════════════════════════\n")

    steps = [
        ("Races",        "processing.silver.bronze_to_silver_races",      "bronze_to_silver_races"),
        ("Drivers",      "processing.silver.bronze_to_silver_drivers",    "bronze_to_silver_drivers"),
        ("Circuits",     "processing.silver.bronze_to_silver_circuits",   "bronze_to_silver_circuits"),
        ("Results",      "processing.silver.bronze_to_silver_results",    "bronze_to_silver_results"),
        ("Qualifying",   "processing.silver.bronze_to_silver_qualifying", "bronze_to_silver_qualifying"),
        ("Pit Stops",    "processing.silver.bronze_to_silver_pitstops",   "bronze_to_silver_pitstops"),
        ("Lap Times",    "processing.silver.bronze_to_silver_laps",       "bronze_to_silver_laps"),
    ]

    results = []

    for name, module_path, func_name in steps:
        print(f"── Processing: {name} {'─' * (30 - len(name))}")
        try:
            module = __import__(module_path, fromlist=[func_name])
            func   = getattr(module, func_name)
            func()
            results.append((name, "✅ Success"))
            log.info(f"{name}: complete")
        except Exception as e:
            results.append((name, f"❌ Failed: {e}"))
            log.info(f"{name}: FAILED — {e}")
        print()

    # ── Final Summary ──────────────────────────────────────
    print("\n══════════════════════════════════════════════════")
    print("  Silver Pipeline Summary")
    print("══════════════════════════════════════════════════")
    for name, status in results:
        print(f"  {name:<15} → {status}")
    print("══════════════════════════════════════════════════\n")


if __name__ == "__main__":
    run_all_silver()