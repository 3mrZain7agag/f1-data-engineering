"""
Step 10 — Predict a Real Race
Finds the race with the most recent date in dim_races, builds its features
(using the same leakage-safe pipeline as training), and predicts top10_finish
/ podium_finish probabilities for every driver entered in that race.

If that race's actual results already exist (finish_position is filled in),
predictions are compared against the real outcome. If not (e.g. qualifying
has just happened but the race hasn't run yet), only predictions are shown.

IMPORTANT: this predicts per-driver "will this driver finish top10/podium"
probabilities using grid_position + qualifying_position + season-to-date
form. It does NOT predict the full finishing order of the race, and it
requires qualifying_position/grid_position to already exist in
fact_race_results for the target race (i.e. run this after qualifying).

Run:
    python -m ml.predict.predict_race
    python -m ml.predict.predict_race --race-id 1234   # target a specific race
    python -m ml.predict.predict_race --model xgboost   # or logreg (default: xgboost)
"""

import argparse
import os
import joblib
import pandas as pd

from ml.features.build_features import load_gold_tables, engineer_all, FEATURE_COLS

MODELS_DIR = "ml/models"


def get_latest_race_with_qualifying(races_df: pd.DataFrame, results_df: pd.DataFrame):
    """
    Returns the most recent race (by date) that has at least one entry with
    qualifying_position recorded in fact_race_results. This skips races that
    are on the calendar (in dim_races) but haven't had qualifying run yet —
    e.g. a future race added to the schedule with no session data at all.
    """
    races_df = races_df.copy()
    races_df["race_date"] = pd.to_datetime(races_df["race_date"])

    races_with_quali = results_df.dropna(subset=["qualifying_position"])["race_id"].unique()
    eligible = races_df[races_df["race_id"].isin(races_with_quali)]

    if eligible.empty:
        raise ValueError("No races found with qualifying data in fact_race_results.")

    return eligible.sort_values("race_date", ascending=False).iloc[0]


def get_target_race(races_df: pd.DataFrame, race_id: str | None):
    races_df = races_df.copy()
    races_df["race_date"] = pd.to_datetime(races_df["race_date"])

    if race_id is not None:
        row = races_df[races_df["race_id"].astype(str) == str(race_id)]
        if row.empty:
            raise ValueError(f"race_id {race_id} not found in dim_races")
        return row.iloc[0]

    # Default: the race with the most recent date in the dataset.
    latest = races_df.sort_values("race_date", ascending=False).iloc[0]
    return latest


def load_model(target: str, model_name: str):
    path = os.path.join(MODELS_DIR, f"{target}_{model_name}.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No saved model at {path}. Run "
            f"`python -m ml.train.train_model --target {target}` first."
        )
    return joblib.load(path)


def predict_for_race(target_race, all_features: pd.DataFrame, target: str, model_name: str, top_n: int = 3):
    race_rows = all_features[all_features["race_id"] == target_race["race_id"]].copy()

    if race_rows.empty:
        print(
            f"No entries found for race_id={target_race['race_id']} "
            f"({target_race.get('race_name', 'unknown')}). "
            "This usually means qualifying hasn't been recorded yet in "
            "fact_race_results / exports/gold have not been refreshed."
        )
        return

    # A race with only qualifying done yet (no grid confirmed) will have
    # grid_position as NaN, even though qualifying_position is set — grid
    # positions are only finalized close to race day, after any penalties.
    # Fall back to qualifying_position as the best available estimate of
    # grid position in that case (grid_penalty_positions becomes 0 for
    # those rows, i.e. "assume no penalty until we know otherwise").
    race_rows = race_rows.copy()
    using_quali_fallback = race_rows["grid_position"].isna() & race_rows["qualifying_position"].notna()
    race_rows.loc[using_quali_fallback, "grid_position"] = race_rows.loc[using_quali_fallback, "qualifying_position"]
    race_rows.loc[using_quali_fallback, "grid_penalty_positions"] = 0

    # Rows still missing qualifying position can't be scored at all
    scoreable = race_rows.dropna(subset=["grid_position", "qualifying_position"])
    missing = len(race_rows) - len(scoreable)
    if missing:
        print(f"Note: {missing} driver(s) missing grid/qualifying data, skipped.")
    if using_quali_fallback.any():
        print(
            f"Note: {using_quali_fallback.sum()} driver(s) have no confirmed grid "
            "position yet (pre-penalty) — using qualifying position as an estimate."
        )

    if scoreable.empty:
        print("No drivers have grid/qualifying data yet for this race.")
        return

    model = load_model(target, model_name)
    X = scoreable[FEATURE_COLS]
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)

    scoreable = scoreable.assign(predicted_prob=probs, predicted_label=preds)

    # NOTE: a completed race will still have NaN finish_position for any
    # driver who DNF'd/retired (they're not "classified" with a numeric
    # finish). Requiring ALL drivers to have a result would mean almost no
    # real race ever counts as "finished" — so we check if ANY driver has
    # a result instead, and only score accuracy on drivers who do.
    has_actual = scoreable["finish_position"].notna().any()

    display_cols = ["driver_id", "grid_position", "qualifying_position", "predicted_prob", "predicted_label"]
    ranked = scoreable.sort_values("predicted_prob", ascending=False)
    top_rows = ranked.head(top_n)

    print(f"\n=== Race: {target_race.get('race_name', target_race['race_id'])} "
          f"({target_race['race_date'].date()}) ===")
    print(f"Target: {target} | Model: {model_name}\n")

    if top_n <= 3:
        podium_labels = ["🥇 P1", "🥈 P2", "🥉 P3"]
        for rank, (_, row) in enumerate(top_rows.iterrows()):
            label = podium_labels[rank] if rank < 3 else f"P{rank + 1}"
            actual_str = ""
            if has_actual:
                fp = row["finish_position"]
                if pd.isna(fp):
                    actual_str = "  [actual: DNF]"
                else:
                    hit = "✓" if row["predicted_label"] == row[target] else "✗"
                    actual_str = f"  [actual finish: P{int(fp)} {hit}]"
            print(
                f"{label}: {row['driver_id']}  "
                f"(grid {int(row['grid_position'])}, "
                f"probability {row['predicted_prob']:.1%}){actual_str}"
            )
    else:
        print(top_rows[display_cols].to_string(index=False))

    if has_actual:
        scored_rows = scoreable.dropna(subset=["finish_position"])
        dnf_count = len(scoreable) - len(scored_rows)

        accuracy = (scored_rows["predicted_label"] == scored_rows[target]).mean()
        print(f"\nActual results are available for this race.")
        if dnf_count:
            print(f"({dnf_count} driver(s) DNF'd/retired and are excluded from accuracy scoring)")
        print(f"Prediction accuracy across {len(scored_rows)} classified drivers: {accuracy:.3f}")
    else:
        print(
            f"\n(ranked out of {len(scoreable)} drivers with grid/qualifying data)"
        )
        print(
            "No actual results yet for this race — showing predictions only. "
            "Re-run this script after the race to compare against the real outcome."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--race-id", type=str, default=None)
    parser.add_argument("--target", choices=["top10_finish", "podium_finish"], default="top10_finish")
    parser.add_argument("--model", choices=["logreg", "xgboost"], default="xgboost")
    parser.add_argument("--top", type=int, default=3, help="Number of top drivers to display (default: 3)")
    args = parser.parse_args()

    tables = load_gold_tables()
    all_features = engineer_all(tables)

    target_race = get_target_race(tables["dim_races"], args.race_id)
    predict_for_race(target_race, all_features, args.target, args.model, top_n=args.top)


if __name__ == "__main__":
    main()