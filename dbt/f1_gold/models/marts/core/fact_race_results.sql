SELECT
    CONCAT(CAST(r.season AS STRING), '_',
           LPAD(CAST(r.round AS STRING), 2, '0'), '_',
           r.driver_id)                     AS result_id,
    CONCAT(CAST(r.season AS STRING), '_',
           LPAD(CAST(r.round AS STRING), 2, '0')) AS race_id,
    r.season,
    r.round,
    r.driver_id,
    r.constructor_id,
    r.grid_position,
    r.finish_position,
    r.position_text,
    r.points,
    r.laps_completed,
    r.status,
    r.fastest_lap_rank,
    r.fastest_lap_time,
    r.is_classified,
    q.position          AS qualifying_position,
    q.q1_ms,
    q.q2_ms,
    q.q3_ms
FROM {{ ref('stg_results') }} r
LEFT JOIN {{ ref('stg_qualifying') }} q
    ON r.season = q.season
    AND r.round = q.round
    AND r.driver_id = q.driver_id
