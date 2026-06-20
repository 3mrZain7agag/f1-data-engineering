-- ── Dimension Tables ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_drivers (
    driver_key        SERIAL PRIMARY KEY,
    driver_id         VARCHAR(50) UNIQUE NOT NULL,
    code              VARCHAR(5),
    permanent_number  VARCHAR(5),
    full_name         VARCHAR(100),
    given_name        VARCHAR(50),
    family_name       VARCHAR(50),
    date_of_birth     DATE,
    nationality       VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_constructors (
    constructor_key   SERIAL PRIMARY KEY,
    constructor_id    VARCHAR(50) UNIQUE NOT NULL,
    name              VARCHAR(100),
    nationality       VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_circuits (
    circuit_key       SERIAL PRIMARY KEY,
    circuit_id        VARCHAR(50) UNIQUE NOT NULL,
    circuit_name      VARCHAR(100),
    locality          VARCHAR(100),
    country           VARCHAR(100),
    lat               DECIMAL(9,6),
    long              DECIMAL(9,6)
);

CREATE TABLE IF NOT EXISTS dim_races (
    race_key          SERIAL PRIMARY KEY,
    season            INTEGER NOT NULL,
    round             INTEGER NOT NULL,
    race_name         VARCHAR(100),
    race_date         DATE,
    circuit_id        VARCHAR(50),
    UNIQUE (season, round)
);

CREATE TABLE IF NOT EXISTS dim_dates (
    date_key          SERIAL PRIMARY KEY,
    full_date         DATE UNIQUE NOT NULL,
    year              INTEGER,
    month             INTEGER,
    quarter           INTEGER,
    day               INTEGER,
    month_name        VARCHAR(20),
    is_weekend        BOOLEAN
);

-- ── Fact Tables ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_race_results (
    result_key        SERIAL PRIMARY KEY,
    race_key          INTEGER REFERENCES dim_races(race_key),
    driver_key        INTEGER REFERENCES dim_drivers(driver_key),
    constructor_key   INTEGER REFERENCES dim_constructors(constructor_key),
    circuit_key       INTEGER REFERENCES dim_circuits(circuit_key),
    date_key          INTEGER REFERENCES dim_dates(date_key),
    grid_position     INTEGER,
    finish_position   INTEGER,
    position_text     VARCHAR(10),
    points            DECIMAL(5,2),
    laps_completed    INTEGER,
    status            VARCHAR(50),
    fastest_lap_rank  INTEGER,
    fastest_lap_time  VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS fact_lap_times (
    lap_key           SERIAL PRIMARY KEY,
    race_key          INTEGER REFERENCES dim_races(race_key),
    driver_key        INTEGER REFERENCES dim_drivers(driver_key),
    lap_number        INTEGER,
    position          INTEGER,
    lap_time          VARCHAR(20),
    lap_time_ms       INTEGER
);

CREATE TABLE IF NOT EXISTS fact_pit_stops (
    pitstop_key       SERIAL PRIMARY KEY,
    race_key          INTEGER REFERENCES dim_races(race_key),
    driver_key        INTEGER REFERENCES dim_drivers(driver_key),
    stop_number       INTEGER,
    lap               INTEGER,
    time_of_day       VARCHAR(20),
    duration          VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS fact_qualifying (
    qual_key          SERIAL PRIMARY KEY,
    race_key          INTEGER REFERENCES dim_races(race_key),
    driver_key        INTEGER REFERENCES dim_drivers(driver_key),
    constructor_key   INTEGER REFERENCES dim_constructors(constructor_key),
    position          INTEGER,
    q1_time           VARCHAR(20),
    q2_time           VARCHAR(20),
    q3_time           VARCHAR(20)
);
