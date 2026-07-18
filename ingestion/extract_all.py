"""
F1 ETL — Step 01
----------------
Extracts historical F1 data from the Ergast API for seasons 2015–2026
and saves it as CSV files + an SQLite database in data/raw/.

Usage:
    python ingestion/extract_all.py                  # all seasons
    python ingestion/extract_all.py --seasons 2023   # single season
    python ingestion/extract_all.py --seasons 2022 2023 2024
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from ingestion.ergast_client import ErgastClient
from utils.logger import get_logger

log      = get_logger(__name__)
RAW_DIR  = Path("data/raw")
DB_PATH  = RAW_DIR / "f1.db"
SEASONS  = list(range(2015, 2027))   # 2015 → 2026 inclusive


# ── Helpers ────────────────────────────────────────────────────────────────

def save_csv(df: pd.DataFrame, name: str) -> None:
    path = RAW_DIR / f"{name}.csv"
    if path.exists():
        # Append only new rows (incremental by checking existing)
        existing = pd.read_csv(path)
        df = pd.concat([existing, df]).drop_duplicates()
    df.to_csv(path, index=False)
    log.info(f"Saved {len(df)} rows → {path}")


def save_sqlite(df: pd.DataFrame, table: str, conn: sqlite3.Connection) -> None:
    df.to_sql(table, conn, if_exists="replace", index=False)
    log.info(f"SQLite: wrote {len(df)} rows → {table}")


# ── Extractors ─────────────────────────────────────────────────────────────

def extract_races(client: ErgastClient, seasons: list[int]) -> pd.DataFrame:
    rows = []
    for season in tqdm(seasons, desc="Races"):
        for race in client.get_races(season):
            rows.append({
                "season":       season,
                "round":        race.get("round"),
                "race_name":    race.get("raceName"),
                "circuit_id":   race.get("Circuit", {}).get("circuitId"),
                "circuit_name": race.get("Circuit", {}).get("circuitName"),
                "country":      race.get("Circuit", {}).get("Location", {}).get("country"),
                "locality":     race.get("Circuit", {}).get("Location", {}).get("locality"),
                "date":         race.get("date"),
                "time":         race.get("time"),
            })
    return pd.DataFrame(rows)


def extract_results(client: ErgastClient, races_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, race in tqdm(races_df.iterrows(), total=len(races_df), desc="Results"):
        for r in client.get_results(int(race["season"]), int(race["round"])):
            rows.append({
                "season":          race["season"],
                "round":           race["round"],
                "race_name":       race["race_name"],
                "driver_id":       r.get("Driver", {}).get("driverId"),
                "constructor_id":  r.get("Constructor", {}).get("constructorId"),
                "grid":            r.get("grid"),
                "position":        r.get("position"),
                "position_text":   r.get("positionText"),
                "points":          r.get("points"),
                "laps":            r.get("laps"),
                "status":          r.get("status"),
                "fastest_lap_rank":r.get("FastestLap", {}).get("rank"),
                "fastest_lap_time":r.get("FastestLap", {}).get("Time", {}).get("time"),
            })
    return pd.DataFrame(rows)


def extract_laps(client: ErgastClient, races_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, race in tqdm(races_df.iterrows(), total=len(races_df), desc="Lap times"):
        for lap in client.get_lap_times(int(race["season"]), int(race["round"])):
            lap["season"] = race["season"]
            lap["round"]  = race["round"]
            rows.append(lap)
    return pd.DataFrame(rows)


def extract_pit_stops(client: ErgastClient, races_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, race in tqdm(races_df.iterrows(), total=len(races_df), desc="Pit stops"):
        for ps in client.get_pit_stops(int(race["season"]), int(race["round"])):
            rows.append({
                "season":     race["season"],
                "round":      race["round"],
                "driver_id":  ps.get("driverId"),
                "stop":       ps.get("stop"),
                "lap":        ps.get("lap"),
                "time":       ps.get("time"),
                "duration":   ps.get("duration"),
            })
    return pd.DataFrame(rows)


def extract_qualifying(client: ErgastClient, races_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, race in tqdm(races_df.iterrows(), total=len(races_df), desc="Qualifying"):
        for q in client.get_qualifying(int(race["season"]), int(race["round"])):
            rows.append({
                "season":         race["season"],
                "round":          race["round"],
                "driver_id":      q.get("Driver", {}).get("driverId"),
                "constructor_id": q.get("Constructor", {}).get("constructorId"),
                "position":       q.get("position"),
                "q1":             q.get("Q1"),
                "q2":             q.get("Q2"),
                "q3":             q.get("Q3"),
            })
    return pd.DataFrame(rows)


def extract_drivers(client: ErgastClient, seasons: list[int]) -> pd.DataFrame:
    seen, rows = set(), []
    for season in tqdm(seasons, desc="Drivers"):
        for d in client.get_drivers(season):
            did = d.get("driverId")
            if did not in seen:
                seen.add(did)
                rows.append({
                    "driver_id":        did,
                    "code":             d.get("code"),
                    "permanent_number": d.get("permanentNumber"),
                    "given_name":       d.get("givenName"),
                    "family_name":      d.get("familyName"),
                    "full_name":        f"{d.get('givenName','')} {d.get('familyName','')}".strip(),
                    "date_of_birth":    d.get("dateOfBirth"),
                    "nationality":      d.get("nationality"),
                })
    return pd.DataFrame(rows)


def extract_constructors(client: ErgastClient, seasons: list[int]) -> pd.DataFrame:
    seen, rows = set(), []
    for season in tqdm(seasons, desc="Constructors"):
        for c in client.get_constructors(season):
            cid = c.get("constructorId")
            if cid not in seen:
                seen.add(cid)
                rows.append({
                    "constructor_id": cid,
                    "name":           c.get("name"),
                    "nationality":    c.get("nationality"),
                })
    return pd.DataFrame(rows)


def extract_circuits(client: ErgastClient, seasons: list[int]) -> pd.DataFrame:
    seen, rows = set(), []
    for season in tqdm(seasons, desc="Circuits"):
        for c in client.get_circuits(season):
            cid = c.get("circuitId")
            if cid not in seen:
                seen.add(cid)
                rows.append({
                    "circuit_id":   cid,
                    "circuit_name": c.get("circuitName"),
                    "locality":     c.get("Location", {}).get("locality"),
                    "country":      c.get("Location", {}).get("country"),
                    "lat":          c.get("Location", {}).get("lat"),
                    "long":         c.get("Location", {}).get("long"),
                })
    return pd.DataFrame(rows)


# ── Main ───────────────────────────────────────────────────────────────────

def main(seasons: list[int]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    client = ErgastClient()
    conn   = sqlite3.connect(DB_PATH)

    log.info(f"Starting F1 ETL for seasons: {seasons}")

    # 1. Races (needed first — other extractors iterate over it)
    races_df = extract_races(client, seasons)
    save_csv(races_df, "races")
    save_sqlite(races_df, "races", conn)

    # 2. Drivers & Constructors (reference data)
    drivers_df = extract_drivers(client, seasons)
    save_csv(drivers_df, "drivers")
    save_sqlite(drivers_df, "drivers", conn)

    constructors_df = extract_constructors(client, seasons)
    save_csv(constructors_df, "constructors")
    save_sqlite(constructors_df, "constructors", conn)

    circuits_df = extract_circuits(client, seasons)
    save_csv(circuits_df, "circuits")
    save_sqlite(circuits_df, "circuits", conn)

    # 3. Race-level data
    results_df = extract_results(client, races_df)
    save_csv(results_df, "results")
    save_sqlite(results_df, "results", conn)

    qualifying_df = extract_qualifying(client, races_df)
    save_csv(qualifying_df, "qualifying")
    save_sqlite(qualifying_df, "qualifying", conn)

    pit_stops_df = extract_pit_stops(client, races_df)
    save_csv(pit_stops_df, "pit_stops")
    save_sqlite(pit_stops_df, "pit_stops", conn)

    # 4. Lap times (largest dataset — last)
    laps_df = extract_laps(client, races_df)
    save_csv(laps_df, "lap_times")
    save_sqlite(laps_df, "lap_times", conn)

    conn.close()
    log.info("ETL complete. All data saved to data/raw/")

    # Summary
    print("\n── Summary ───────────────────────────────")
    for name, df in [
        ("races",        races_df),
        ("drivers",      drivers_df),
        ("constructors", constructors_df),
        ("circuits",     circuits_df),
        ("results",      results_df),
        ("qualifying",   qualifying_df),
        ("pit_stops",    pit_stops_df),
        ("lap_times",    laps_df),
    ]:
        print(f"  {name:<15} {len(df):>8,} rows")
    print("──────────────────────────────────────────")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F1 ETL — Step 01")
    parser.add_argument(
        "--seasons", nargs="+", type=int,
        default=SEASONS,
        help="Seasons to fetch (default: 2015–2026)"
    )
    args = parser.parse_args()
    main(args.seasons)