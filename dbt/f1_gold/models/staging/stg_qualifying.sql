SELECT
    season,
    round,
    driver_id,
    constructor_id,
    position,
    q1,
    q2,
    q3,
    q1_ms,
    q2_ms,
    q3_ms,
    _source,
    _ingested_at
FROM f1_catalog.silver.qualifying
