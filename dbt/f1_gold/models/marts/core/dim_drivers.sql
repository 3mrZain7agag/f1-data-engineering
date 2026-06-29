SELECT
    driver_id,
    code,
    permanent_number,
    given_name,
    family_name,
    full_name,
    date_of_birth,
    nationality
FROM {{ ref('stg_drivers') }}
