SELECT
    season,
    round,
    driver_id,
    stop_number,
    lap,
    time_of_day,
    duration,
    duration_ms
FROM {{ ref('stg_pit_stops') }}
WHERE duration_ms IS NOT NULL
