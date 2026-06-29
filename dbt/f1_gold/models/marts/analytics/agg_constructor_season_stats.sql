SELECT
    season,
    constructor_id,
    COUNT(DISTINCT driver_id)                   AS drivers_used,
    COUNT(*)                                    AS race_entries,
    SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) AS podiums,
    SUM(points)                                 AS total_points,
    AVG(finish_position)                        AS avg_finish_position,
    SUM(CASE WHEN status = 'Finished' THEN 1 ELSE 0 END) AS finishes,
    SUM(CASE WHEN NOT is_classified THEN 1 ELSE 0 END)    AS dnfs,
    ROUND(SUM(CASE WHEN NOT is_classified THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS dnf_rate_pct
FROM {{ ref('fact_race_results') }}
GROUP BY season, constructor_id
ORDER BY season DESC, total_points DESC
