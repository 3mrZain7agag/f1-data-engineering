"""
Data Quality Master Runner — Step 07
---------------------------------------
Runs all Silver layer data quality checkpoints.
If any critical checkpoint fails, the pipeline should NOT proceed to Gold.

Usage:
    python -m quality.checkpoints.run_all_checks
"""

import sys
sys.path.insert(0, '/workspaces/f1-data-engineering')

from utils.logger import get_logger

log = get_logger(__name__)


def run_all_checks() -> bool:
    print("\n══════════════════════════════════════════════════")
    print("  F1 Data Engineering — Data Quality Checkpoints")
    print("══════════════════════════════════════════════════\n")

    from quality.checkpoints.validate_race_results import validate_race_results
    from quality.checkpoints.validate_lap_times import validate_lap_times

    checks = [
        ("race_results", validate_race_results),
        ("lap_times",    validate_lap_times),
    ]

    all_passed = True
    summary = []

    for name, check_fn in checks:
        try:
            passed = check_fn()
            summary.append((name, "PASS" if passed else "FAIL"))
            if not passed:
                all_passed = False
        except Exception as e:
            summary.append((name, f"ERROR: {e}"))
            all_passed = False

    print("\n══════════════════════════════════════════════════")
    print("  Data Quality Summary")
    print("══════════════════════════════════════════════════")
    for name, status in summary:
        print(f"  {name:<20} -> {status}")
    print("══════════════════════════════════════════════════")

    if all_passed:
        print("\nALL CHECKPOINTS PASSED - safe to proceed to Gold layer\n")
    else:
        print("\nCHECKPOINT FAILURES DETECTED - pipeline should halt\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)