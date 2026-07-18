"""
Step 10 — Feature Engineering
Builds a leakage-safe training dataset from the Gold layer CSV exports
(exports/gold/*.csv) for predicting race outcomes.

Design notes:
- We deliberately use PRIOR-SEASON driver/constructor stats as "form" features.
  Using the CURRENT season's aggregated stats would leak future race outcomes
  into the features (since agg_driver_season_stats/agg_constructor_season_stats
  are computed over the whole season).
- Circuit stats (agg_circuit_stats) are all-time aggregates. This is a known
  simplification — ideally we'd use "circuit history up to this race" — but
  with our data volume (233 races), the all-time aggregate is a reasonable
  proxy and is noted here for transparency.

Run:
    python -m ml.features.build_features
Output:
    ml/data/training_dataset.csv
"""

import os
import pandas as pd

GOLD_DIR = "exports/gold"
OUTPUT_DIR = "ml/data"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "training_dataset.csv")


def load_gold_tables():
    tables = {}
    for name in [
        "fact_race_results",
        "dim_races",
        "agg_driver_season_stats",
        "agg_constructor_season_stats",
        "agg_circuit_stats",
    ]:
        path = os.path.join(GOLD_DIR, f"{name}.csv")
        tables[name] = pd.read_csv(path)
    return tables


def add_in_season_form(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds rolling, leakage-safe in-season form features per driver:
      - driver_points_this_season_so_far: cumulative points BEFORE this race
      - driver_avg_finish_last_3: average finish position over the driver's
        previous 3 races in the same season (shifted so the current race's
        own result is never included)

    Prior-season aggregates (already in the pipeline) capture "how good was
    this driver last year" but say nothing about current-season form — e.g.
    a driver on a hot streak in round 10 looks identical to one who has been
    struggling, if we only look at last year's totals. This fills that gap.
    """
    df = df.sort_values(["season", "driver_id", "round"]).copy()
    grouped = df.groupby(["season", "driver_id"])

    # Cumulative points BEFORE this race (subtract current row's own points)
    df["driver_points_this_season_so_far"] = (
        grouped["points"].cumsum() - df["points"]
    )

    # Rolling average of finish_position over the previous 3 races (shifted)
    df["driver_avg_finish_last_3"] = grouped["finish_position"].transform(
        lambda s: s.shift(1).rolling(window=3, min_periods=1).mean()
    )
    # First race of a driver's season -> no rolling history yet; fill with median
    df["driver_avg_finish_last_3"] = df["driver_avg_finish_last_3"].fillna(
        df["driver_avg_finish_last_3"].median()
    )

    return df


def engineer_all(tables: dict) -> pd.DataFrame:
    """
    Runs the full feature-engineering pipeline WITHOUT dropping any rows.
    A race that hasn't been run yet will have finish_position/points as NaN,
    but grid_position/qualifying_position will be present once qualifying has
    happened — this function keeps such rows so they can be used for
    prediction (see ml/predict/predict_race.py). Training code should call
    build_features() instead, which drops incomplete rows.
    """
    results = tables["fact_race_results"].copy()
    races = tables["dim_races"].copy()
    driver_stats = tables["agg_driver_season_stats"].copy()
    constructor_stats = tables["agg_constructor_season_stats"].copy()
    circuit_stats = tables["agg_circuit_stats"].copy()

    # Join race metadata (circuit_id, race_date) onto results.
    # Note: fact_race_results already has its own `season` column, so we only
    # pull circuit_id/race_date from dim_races to avoid a season_x/season_y collision.
    df = results.merge(
        races[["race_id", "circuit_id", "race_date"]], on="race_id", how="left"
    )

    # Rolling in-season form (leakage-safe — see function docstring).
    # NOTE: this uses `points`, which is NaN for a race that hasn't been run
    # yet. cumsum() treats NaN as 0 for rows after it in the group, which is
    # correct here since a future race has no points to contribute either way.
    df = add_in_season_form(df)

    # Prior-season driver form: shift season stats forward by 1 year
    driver_prior = driver_stats.copy()
    driver_prior["season"] = driver_prior["season"] + 1
    driver_prior = driver_prior.rename(
        columns={
            "total_points": "driver_prior_season_points",
            "wins": "driver_prior_season_wins",
        }
    )[["driver_id", "season", "driver_prior_season_points", "driver_prior_season_wins"]]

    df = df.merge(driver_prior, on=["driver_id", "season"], how="left")

    # Prior-season constructor form
    constructor_prior = constructor_stats.copy()
    constructor_prior["season"] = constructor_prior["season"] + 1
    constructor_prior = constructor_prior.rename(
        columns={
            "total_points": "constructor_prior_season_points",
            "dnf_rate_pct": "constructor_prior_season_dnf_rate",
        }
    )[
        [
            "constructor_id",
            "season",
            "constructor_prior_season_points",
            "constructor_prior_season_dnf_rate",
        ]
    ]

    df = df.merge(constructor_prior, on=["constructor_id", "season"], how="left")

    # Circuit history (all-time aggregate — see module docstring caveat)
    circuit_cols = circuit_stats.rename(
        columns={
            "avg_lap_time_ms": "circuit_avg_lap_time_ms",
            "total_races": "circuit_races_held",
        }
    )[["circuit_id", "circuit_avg_lap_time_ms", "circuit_races_held"]]

    df = df.merge(circuit_cols, on="circuit_id", how="left")

    # Labels (will be NaN/0 for a race that hasn't happened yet, since
    # finish_position is NaN — that's fine, predict_race.py never uses these
    # labels for the not-yet-run target race, only for comparison if present)
    df["top10_finish"] = (df["finish_position"] <= 10).astype("Int64")
    df["podium_finish"] = (df["finish_position"] <= 3).astype("Int64")

    # Rookies / first-season drivers and new constructors will have NaN prior-season
    # stats. Fill with 0 (treated as "no prior top-flight form") and flag it,
    # rather than silently dropping rows.
    prior_feature_cols = [
        "driver_prior_season_points",
        "driver_prior_season_wins",
        "constructor_prior_season_points",
        "constructor_prior_season_dnf_rate",
    ]
    df["is_rookie_or_new_team"] = df[prior_feature_cols].isna().any(axis=1).astype(int)
    df[prior_feature_cols] = df[prior_feature_cols].fillna(0)

    # Grid penalty: positive means the driver started worse than they
    # qualified (e.g. gearbox/engine penalty); negative means promoted
    # (e.g. another driver's penalty moved them up).
    df["grid_penalty_positions"] = df["grid_position"] - df["qualifying_position"]

    return df


FEATURE_COLS = [
    "season",
    "grid_position",
    "qualifying_position",
    "grid_penalty_positions",
    "driver_prior_season_points",
    "driver_prior_season_wins",
    "constructor_prior_season_points",
    "constructor_prior_season_dnf_rate",
    "circuit_avg_lap_time_ms",
    "circuit_races_held",
    "is_rookie_or_new_team",
    "driver_points_this_season_so_far",
    "driver_avg_finish_last_3",
]
LABEL_COLS = ["top10_finish", "podium_finish"]
ID_COLS = ["race_id", "race_date", "driver_id", "constructor_id", "circuit_id", "finish_position"]


def build_features(tables: dict) -> pd.DataFrame:
    """Training dataset: engineer_all() + drop rows missing required inputs
    (i.e. races that haven't been run / haven't had qualifying yet)."""
    df = engineer_all(tables)
    final = df[ID_COLS + FEATURE_COLS + LABEL_COLS].dropna(
        subset=["grid_position", "finish_position", "qualifying_position"]
    )
    return final


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tables = load_gold_tables()
    dataset = build_features(tables)
    dataset.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(dataset)} rows to {OUTPUT_PATH}")
    print(f"top10_finish positive rate: {dataset['top10_finish'].mean():.3f}")
    print(f"podium_finish positive rate: {dataset['podium_finish'].mean():.3f}")
    print(f"rookie/new-team rows: {dataset['is_rookie_or_new_team'].sum()}")


if __name__ == "__main__":
    main()