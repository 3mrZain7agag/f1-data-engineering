SELECT
    CONCAT(CAST(COALESCE(r.season, q.season) AS STRING), '_',
           LPAD(CAST(COALESCE(r.round, q.round) AS STRING), 2, '0'), '_',
           COALESCE(r.driver_id, q.driver_id))                     AS result_id,
    CONCAT(CAST(COALESCE(r.season, q.season) AS STRING), '_',
           LPAD(CAST(COALESCE(r.round, q.round) AS STRING), 2, '0')) AS race_id,
    COALESCE(r.season, q.season)         AS season,
    COALESCE(r.round, q.round)           AS round,
    COALESCE(r.driver_id, q.driver_id)   AS driver_id,
    COALESCE(r.constructor_id, q.constructor_id) AS constructor_id,
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
FULL OUTER JOIN {{ ref('stg_qualifying') }} q
    ON r.season = q.season
    AND r.round = q.round
    AND r.driver_id = q.driver_id

-- NOTE: this is a FULL OUTER JOIN, not a LEFT JOIN, on purpose.
-- Jolpica's `results.json` endpoint has no data at all for a race until
-- that race has actually been run — but `qualifying.json` populates as
-- soon as qualifying finishes, often a day or more earlier. A LEFT JOIN
-- from stg_results would silently produce ZERO rows for a race that has
-- qualifying but no results yet, which breaks any prediction workflow
-- that needs grid_position/qualifying_position for an upcoming race
-- (see ml/predict/predict_race.py). The FULL OUTER JOIN + COALESCE lets
-- a row exist from qualifying alone, with finish_position/points/etc.
-- staying NULL until results actually land.