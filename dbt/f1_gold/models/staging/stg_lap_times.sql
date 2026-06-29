SELECT
    season,
    round,
    driver_id,
    lap_number,
    position,
    lap_time,
    lap_time_ms,
    _source,
    _ingested_at
FROM f1_catalog.silver.lap_times
