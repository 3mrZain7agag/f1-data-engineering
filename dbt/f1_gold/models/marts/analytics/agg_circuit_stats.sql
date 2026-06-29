SELECT
    r.circuit_id,
    r.country,
    COUNT(DISTINCT r.season)                    AS seasons_held,
    COUNT(DISTINCT r.race_id)                   AS total_races,
    MIN(r.season)                               AS first_season,
    MAX(r.season)                               AS last_season,
    AVG(f.lap_time_ms)                          AS avg_lap_time_ms,
    MIN(f.lap_time_ms)                          AS fastest_lap_ms
FROM {{ ref('dim_races') }} r
LEFT JOIN {{ ref('fact_lap_times') }} f
    ON r.season = f.season
    AND r.round = f.round
GROUP BY r.circuit_id, r.country
ORDER BY total_races DESC
