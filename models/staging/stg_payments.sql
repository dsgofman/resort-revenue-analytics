with source as (
    select * from {{ source('raw', 'payments') }}
)

select
    payment_id,
    booking_id,
    cast(payment_date as date)   as payment_date,
    cast(amount_cents as bigint) as amount_cents,
    {{ cents_to_dollars('amount_cents') }} as amount_usd,
    payment_method,
    payment_status
from source
