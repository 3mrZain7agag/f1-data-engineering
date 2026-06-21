"""
F1 Data Warehouse Loader — Step 02
------------------------------------
Reads raw CSVs from data/raw/ and loads them into
PostgreSQL Star Schema using psycopg2 directly.
"""

import psycopg2
import psycopg2.extras
import pandas as pd
from utils.logger import get_logger

log = get_logger(__name__)

DB_PARAMS = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "f1_warehouse",
    "user":     "f1user",
    "password": "f1password",
}
RAW_DIR = "data/raw"


def get_conn():
    conn = psycopg2.connect(**DB_PARAMS)
    log.info("Connected to PostgreSQL")
    return conn


def time_to_ms(t):
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


def insert_df(conn, table, df):
    """Insert a DataFrame into a PostgreSQL table using psycopg2."""
    if df.empty:
        return
    cols    = list(df.columns)
    values  = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False)]
    col_str = ', '.join(cols)
    val_str = ', '.join(['%s'] * len(cols))
    query   = f"INSERT INTO {table} ({col_str}) VALUES ({val_str})"
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, query, values, page_size=500)
    conn.commit()


def load_dim_drivers(conn):
    df = pd.read_csv(f"{RAW_DIR}/drivers.csv")
    df = df[['driver_id','code','permanent_number','full_name',
             'given_name','family_name','date_of_birth','nationality']
            ].drop_duplicates('driver_id')
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_drivers RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'dim_drivers', df)
    with conn.cursor() as cur:
        cur.execute("SELECT driver_key, driver_id FROM dim_drivers")
        rows = cur.fetchall()
    log.info(f"dim_drivers: {len(rows)} rows loaded")
    return {r[1]: r[0] for r in rows}


def load_dim_constructors(conn):
    df = pd.read_csv(f"{RAW_DIR}/constructors.csv")
    df = df[['constructor_id','name','nationality']].drop_duplicates('constructor_id')
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_constructors RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'dim_constructors', df)
    with conn.cursor() as cur:
        cur.execute("SELECT constructor_key, constructor_id FROM dim_constructors")
        rows = cur.fetchall()
    log.info(f"dim_constructors: {len(rows)} rows loaded")
    return {r[1]: r[0] for r in rows}


def load_dim_circuits(conn):
    df = pd.read_csv(f"{RAW_DIR}/circuits.csv")
    df = df[['circuit_id','circuit_name','locality','country','lat','long']
            ].drop_duplicates('circuit_id')
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_circuits RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'dim_circuits', df)
    with conn.cursor() as cur:
        cur.execute("SELECT circuit_key, circuit_id FROM dim_circuits")
        rows = cur.fetchall()
    log.info(f"dim_circuits: {len(rows)} rows loaded")
    return {r[1]: r[0] for r in rows}


def load_dim_races(conn):
    df = pd.read_csv(f"{RAW_DIR}/races.csv")
    df = df.rename(columns={'date': 'race_date'})
    df = df[['season','round','race_name','race_date','circuit_id']
            ].drop_duplicates(['season','round'])
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_races RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'dim_races', df)
    with conn.cursor() as cur:
        cur.execute("SELECT race_key, season, round FROM dim_races")
        rows = cur.fetchall()
    log.info(f"dim_races: {len(rows)} rows loaded")
    return {(r[1], r[2]): r[0] for r in rows}


def load_dim_dates(conn):
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
    with conn.cursor() as cur:
        cur.execute("TRUNCATE dim_dates RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'dim_dates', date_df)
    with conn.cursor() as cur:
        cur.execute("SELECT date_key, full_date FROM dim_dates")
        rows = cur.fetchall()
    log.info(f"dim_dates: {len(rows)} rows loaded")
    return {str(r[1]): r[0] for r in rows}


def load_fact_results(conn, race_map, driver_map, constructor_map, circuit_map, date_map):
    results    = pd.read_csv(f"{RAW_DIR}/results.csv")
    races      = pd.read_csv(f"{RAW_DIR}/races.csv")
    results    = results.drop_duplicates(['season','round','driver_id'])
    races_slim = races[['season','round','date','circuit_id']].drop_duplicates(['season','round'])
    df = results.merge(races_slim, on=['season','round'], how='left')
    df['race_key']        = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key']      = df['driver_id'].map(driver_map)
    df['constructor_key'] = df['constructor_id'].map(constructor_map)
    df['circuit_key']     = df['circuit_id'].map(circuit_map)
    df['date_key']        = df['date'].map(date_map)
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
    with conn.cursor() as cur:
        cur.execute("TRUNCATE fact_race_results RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'fact_race_results', df[cols])
    log.info(f"fact_race_results: {len(df)} rows loaded")


def load_fact_lap_times(conn, race_map, driver_map):
    df = pd.read_csv(f"{RAW_DIR}/lap_times.csv")
    df['race_key']    = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key']  = df['driver_id'].map(driver_map)
    df['lap_time_ms'] = df['time'].apply(time_to_ms)
    df = df.rename(columns={'time': 'lap_time'})
    cols = ['race_key','driver_key','lap_number','position','lap_time','lap_time_ms']
    with conn.cursor() as cur:
        cur.execute("TRUNCATE fact_lap_times RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'fact_lap_times', df[cols])
    log.info(f"fact_lap_times: {len(df)} rows loaded")


def load_fact_pit_stops(conn, race_map, driver_map):
    df = pd.read_csv(f"{RAW_DIR}/pit_stops.csv")
    df['race_key']   = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key'] = df['driver_id'].map(driver_map)
    df = df.rename(columns={'stop': 'stop_number', 'time': 'time_of_day'})
    cols = ['race_key','driver_key','stop_number','lap','time_of_day','duration']
    with conn.cursor() as cur:
        cur.execute("TRUNCATE fact_pit_stops RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'fact_pit_stops', df[cols])
    log.info(f"fact_pit_stops: {len(df)} rows loaded")


def load_fact_qualifying(conn, race_map, driver_map, constructor_map):
    df = pd.read_csv(f"{RAW_DIR}/qualifying.csv")
    df['race_key']        = df.apply(lambda r: race_map.get((r['season'], r['round'])), axis=1)
    df['driver_key']      = df['driver_id'].map(driver_map)
    df['constructor_key'] = df['constructor_id'].map(constructor_map)
    df = df.rename(columns={'q1': 'q1_time', 'q2': 'q2_time', 'q3': 'q3_time'})
    cols = ['race_key','driver_key','constructor_key','position','q1_time','q2_time','q3_time']
    with conn.cursor() as cur:
        cur.execute("TRUNCATE fact_qualifying RESTART IDENTITY CASCADE")
    conn.commit()
    insert_df(conn, 'fact_qualifying', df[cols])
    log.info(f"fact_qualifying: {len(df)} rows loaded")


def main():
    conn = get_conn()
    log.info("Loading dimension tables...")
    driver_map      = load_dim_drivers(conn)
    constructor_map = load_dim_constructors(conn)
    circuit_map     = load_dim_circuits(conn)
    race_map        = load_dim_races(conn)
    date_map        = load_dim_dates(conn)
    log.info("Loading fact tables...")
    load_fact_results(conn, race_map, driver_map, constructor_map, circuit_map, date_map)
    load_fact_lap_times(conn, race_map, driver_map)
    load_fact_pit_stops(conn, race_map, driver_map)
    load_fact_qualifying(conn, race_map, driver_map, constructor_map)
    log.info("✅ Warehouse load complete!")
    with conn.cursor() as cur:
        print("\n── Warehouse Summary ─────────────────────────")
        for table in ['dim_drivers','dim_constructors','dim_circuits',
                      'dim_races','dim_dates','fact_race_results',
                      'fact_lap_times','fact_pit_stops','fact_qualifying']:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table:<25} {count:>8,} rows")
        print("──────────────────────────────────────────────")
    conn.close()


if __name__ == "__main__":
    main()
