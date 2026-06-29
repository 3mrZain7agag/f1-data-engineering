SELECT
    season,
    round,
    driver_id,
    constructor_id,
    grid            AS grid_position,
    position        AS finish_position,
    position_text,
    points,
    laps            AS laps_completed,
    status,
    fastest_lap_rank,
    fastest_lap_time,
    is_classified,
    _source,
    _ingested_at
FROM f1_catalog.silver.race_results
