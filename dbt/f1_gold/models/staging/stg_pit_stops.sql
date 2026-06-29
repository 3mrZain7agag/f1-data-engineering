SELECT
    season,
    round,
    driver_id,
    stop_number,
    lap,
    time_of_day,
    duration,
    duration_ms,
    _source,
    _ingested_at
FROM f1_catalog.silver.pit_stops
