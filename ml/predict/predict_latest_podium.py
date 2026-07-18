"""
Step 10 — Predict Podium for the Latest Race
Convenience wrapper around predict_race.py that always targets:
  - the most recent race by date in dim_races
  - the podium_finish model (top 3)
  - the XGBoost model (best-performing on podium_finish: ROC-AUC 0.93)

If that race's actual results already exist, predictions are compared
against the real outcome. If not, only the predicted podium is shown.

Run:
    python -m ml.predict.predict_latest_podium
"""

from ml.features.build_features import load_gold_tables, engineer_all
from ml.predict.predict_race import get_latest_race_with_qualifying, predict_for_race


def main():
    tables = load_gold_tables()
    all_features = engineer_all(tables)

    target_race = get_latest_race_with_qualifying(
        tables["dim_races"], tables["fact_race_results"]
    )
    predict_for_race(
        target_race,
        all_features,
        target="podium_finish",
        model_name="xgboost",
        top_n=3,
    )


if __name__ == "__main__":
    main()