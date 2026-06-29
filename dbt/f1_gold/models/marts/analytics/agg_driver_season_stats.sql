SELECT
    season,
    driver_id,
    COUNT(*)                                    AS races_entered,
    SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) AS podiums,
    SUM(CASE WHEN finish_position <= 10 AND is_classified THEN 1 ELSE 0 END) AS points_finishes,
    SUM(points)                                 AS total_points,
    AVG(finish_position)                        AS avg_finish_position,
    AVG(grid_position)                          AS avg_grid_position,
    MIN(finish_position)                        AS best_finish,
    SUM(CASE WHEN status = 'Finished' THEN 1 ELSE 0 END) AS races_finished,
    SUM(CASE WHEN status != 'Finished' AND NOT is_classified THEN 1 ELSE 0 END) AS dnfs
FROM {{ ref('fact_race_results') }}
GROUP BY season, driver_id
ORDER BY season DESC, total_points DESC
