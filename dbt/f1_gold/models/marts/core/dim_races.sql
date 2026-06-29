SELECT
    CONCAT(CAST(season AS STRING), '_', LPAD(CAST(round AS STRING), 2, '0')) AS race_id,
    season,
    round,
    race_name,
    circuit_id,
    country,
    race_date,
    YEAR(race_date)    AS race_year,
    MONTH(race_date)   AS race_month
FROM {{ ref('stg_races') }}
