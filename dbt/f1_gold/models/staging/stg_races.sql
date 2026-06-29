SELECT
    season,
    round,
    race_name,
    circuit_id,
    circuit_name,
    country,
    locality,
    race_date,
    _source,
    _ingested_at
FROM f1_catalog.silver.races
