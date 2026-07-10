with source as (
    select * from {{ source('raw', 'commissions') }}
)

select
    commission_id,
    booking_id,
    agent_id,
    cast(commission_rate as double)         as commission_rate,
    cast(commission_amount_cents as bigint) as commission_amount_cents,
    {{ cents_to_dollars('commission_amount_cents') }} as commission_amount_usd
from source
