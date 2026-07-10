with guests as (
    select * from {{ ref('stg_guests') }}
)

select
    guest_id,
    first_name || ' ' || last_name as full_name,
    email,
    country,
    loyalty_tier,
    created_at
from guests
