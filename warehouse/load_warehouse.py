"""
F1 Data Warehouse Loader — Step 02
-----------------------------------
Reads raw CSVs from data/raw/ and loads them into
PostgreSQL Star Schema tables.

Usage:
    python -m warehouse.load_warehouse
"""

import pandas as pd
from sqlalchemy import create_engine, text
from utils.logger import get_logger

log = get_logger(__name__)

DB_URL  = "postgresql://f1user:f1password@localhost:5432/f1_warehouse"
RAW_DIR = "data/raw"


def get_engine():
    engine = create_engine(DB_URL)
    log.info("Connected to PostgreSQL")
    return engine


# ── Helpers ────────────────────────────────────────────────────────────────

def time_to_ms(t: str) -> int:
    """Convert lap time string '1:23.456' to milliseconds."""
    try:
        if not t or str(t) == 'nan':
            return None
        t = str(t).strip()
        if ':' in t:
            mins, rest = t.split(':')
            return int(int(mins) * 60000 + float(rest) * 1000)
        return int(float(t) * 1000)
    except:
        return None


# ── Dimension Loaders ──────────────────────────────────────────────────────

def load_dim_drivers(engine) -> dict:
    df = pd.read_csv(f"{RAW_DIR}/drivers.csv")
    df = df[['driver_id','code','permanent_number',
             'full_name','given_name','family_name',
             'date_of_birth','nationality']].drop_duplicates('driver_id')

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dim_drivers RESTART IDENTITY CASCADE"))
        df.to_sql('dim_drivers', conn, if_exists='append', index=False)

    # Return lookup: driver_id → driver_key
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT driver_key, driver_id FROM dim_drivers")).fetchall()
    log.info(f"dim_drivers: {len(rows)} rows loaded")
    return {r.driver_id: r.driver_key for r in rows}


def load_dim_constructors(engine) -> dict:
    df = pd.read_csv(f"{RAW_DIR}/constructors.csv")
    df = df[['constructor_id','name','nationality']].drop_duplicates('constructor_id')

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dim_constructors RESTART IDENTITY CASCADE"))
        df.to_sql('dim_constructors', conn, if_exists='append', index=False)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT constructor_key, constructor_id FROM dim_constructors")).fetchall()
    log.info(f"dim_constructors: {len(rows)} rows loaded")
    return {r.constructor_id: r.constructor_key for r in rows}


def load_dim_circuits(engine) -> dict:
    df = pd.read_csv(f"{RAW_DIR}/circuits.csv")
    df = df[['circuit_id','circuit_name','locality','country','lat','long']].drop_duplicates('circuit_id')

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dim_circuits RESTART IDENTITY CASCADE"))
        df.to_sql('dim_circuits', conn, if_exists='append', index=False)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT circuit_key, circuit_id FROM dim_circuits")).fetchall()
    log.info(f"dim_circuits: {len(rows)} rows loaded")
    return {r.circuit_id: r.circuit_key for r in rows}


def load_dim_races(engine) -> dict:
    df = pd.read_csv(f"{RAW_DIR}/races.csv")
    df = df.rename(columns={'date': 'race_date'})
    df = df[['season','round','race_name','race_date','circuit_id']].drop_duplicates(['season','round'])

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dim_races RESTART IDENTITY CASCADE"))
        df.to_sql('dim_races', conn, if_exists='append', index=False)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT race_key, season, round FROM dim_races")).fetchall()
    log.info(f"dim_races: {len(rows)} rows loaded")
    return {(r.season, r.round): r.race_key for r in rows}


def load_dim_dates(engine) -> dict:
    df = pd.read_csv(f"{RAW_DIR}/races.csv")
    dates = pd.to_datetime(df['date'].dropna()).dt.date
    dates = pd.Series(sorted(set(dates)), name='full_date')

    date_df = pd.DataFrame({
        'full_date':  dates,
        'year':       pd.to_datetime(dates).dt.year,
        'month':      pd.to_datetime(dates).dt.month,
        'quarter':    pd.to_datetime(dates).dt.quarter,
        'day':        pd.to_datetime(dates).dt.day,
        'month_name': pd.to_datetime(dates).dt.strftime('%B'),
        'is_weekend': pd.to_datetime(dates).dt.dayofweek >= 5,
    })

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE dim_dates RESTART IDENTITY CASCADE"))
        date_df.to_sql('dim_dates', conn, if_exists='append', index=False)

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT date_key, full_date FROM dim_dates")).fetchall()
    log.info(f"dim_dates: {len(rows)} rows loaded")
    return {str(r.full_date): r.date_key for r in rows}


# ── Fact Loaders ───────────────────────────────────────────────────────────

def load_fact_results(engine, race_map, driver_map, constructor_map, circuit_map, date_map):
    results = pd.read_csv(f"{RAW_DIR}/results.csv")
    races   = pd.read_csv(f"{RAW_DIR}/races.csv")

    results = results.drop_duplicates(['season','round','driver_id'])
    races_slim = races[['season','round','date','circuit_id']].drop_duplicates(['season','round'])
    df = results.merge(
        races_slim,
        on=['season','round'], how='left'
    )

    df['race_key']         = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key']       = df['driver_id'].map(driver_map)
    df['constructor_key']  = df['constructor_id'].map(constructor_map)
    df['circuit_key']      = df['circuit_id'].map(circuit_map)
    df['date_key']         = df['date'].map(date_map)

    df = df.rename(columns={
        'grid':            'grid_position',
        'position':        'finish_position',
        'points':          'points',
        'laps':            'laps_completed',
        'fastest_lap_rank':'fastest_lap_rank',
        'fastest_lap_time':'fastest_lap_time',
    })

    cols = ['race_key','driver_key','constructor_key','circuit_key','date_key',
            'grid_position','finish_position','position_text','points',
            'laps_completed','status','fastest_lap_rank','fastest_lap_time']

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_race_results RESTART IDENTITY CASCADE"))
        df[cols].to_sql('fact_race_results', conn, if_exists='append', index=False)

    log.info(f"fact_race_results: {len(df)} rows loaded")


def load_fact_lap_times(engine, race_map, driver_map):
    df = pd.read_csv(f"{RAW_DIR}/lap_times.csv")

    df['race_key']   = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key'] = df['driver_id'].map(driver_map)
    df['lap_time_ms']= df['time'].apply(time_to_ms)

    df = df.rename(columns={'time': 'lap_time'})
    cols = ['race_key','driver_key','lap_number','position','lap_time','lap_time_ms']

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_lap_times RESTART IDENTITY CASCADE"))
        df[cols].to_sql('fact_lap_times', conn, if_exists='append', index=False)

    log.info(f"fact_lap_times: {len(df)} rows loaded")


def load_fact_pit_stops(engine, race_map, driver_map):
    df = pd.read_csv(f"{RAW_DIR}/pit_stops.csv")

    df['race_key']   = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key'] = df['driver_id'].map(driver_map)

    df = df.rename(columns={
        'stop': 'stop_number',
        'lap':  'lap',
        'time': 'time_of_day',
    })
    cols = ['race_key','driver_key','stop_number','lap','time_of_day','duration']

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_pit_stops RESTART IDENTITY CASCADE"))
        df[cols].to_sql('fact_pit_stops', conn, if_exists='append', index=False)

    log.info(f"fact_pit_stops: {len(df)} rows loaded")


def load_fact_qualifying(engine, race_map, driver_map, constructor_map):
    df = pd.read_csv(f"{RAW_DIR}/qualifying.csv")

    df['race_key']        = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key']      = df['driver_id'].map(driver_map)
    df['constructor_key'] = df['constructor_id'].map(constructor_map)

    df = df.rename(columns={
        'position': 'position',
        'q1': 'q1_time',
        'q2': 'q2_time',
        'q3': 'q3_time',
    })
    cols = ['race_key','driver_key','constructor_key','position','q1_time','q2_time','q3_time']

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE fact_qualifying RESTART IDENTITY CASCADE"))
        df[cols].to_sql('fact_qualifying', conn, if_exists='append', index=False)

    log.info(f"fact_qualifying: {len(df)} rows loaded")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    engine = get_engine()

    log.info("Loading dimension tables...")
    driver_map      = load_dim_drivers(engine)
    constructor_map = load_dim_constructors(engine)
    circuit_map     = load_dim_circuits(engine)
    race_map        = load_dim_races(engine)
    date_map        = load_dim_dates(engine)

    log.info("Loading fact tables...")
    load_fact_results(engine, race_map, driver_map, constructor_map, circuit_map, date_map)
    load_fact_lap_times(engine, race_map, driver_map)
    load_fact_pit_stops(engine, race_map, driver_map)
    load_fact_qualifying(engine, race_map, driver_map, constructor_map)

    log.info("✅ Warehouse load complete!")

    # Print summary
    with engine.connect() as conn:
        print("\n── Warehouse Summary ─────────────────────────")
        for table in ['dim_drivers','dim_constructors','dim_circuits',
                      'dim_races','dim_dates','fact_race_results',
                      'fact_lap_times','fact_pit_stops','fact_qualifying']:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:<25} {count:>8,} rows")
        print("──────────────────────────────────────────────")


if __name__ == "__main__":
    main()
