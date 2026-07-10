with source as (
    select * from {{ source('raw', 'guests') }}
)

select
    guest_id,
    first_name,
    last_name,
    email,
    country,
    loyalty_tier,
    cast(created_at as timestamp) as created_at
from source
