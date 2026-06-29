SELECT
    circuit_id,
    circuit_name,
    locality,
    country,
    lat,
    long
FROM {{ ref('stg_circuits') }}
