SELECT
    season,
    round,
    driver_id,
    lap_number,
    position,
    lap_time,
    lap_time_ms
FROM {{ ref('stg_lap_times') }}
WHERE lap_time_ms IS NOT NULL
