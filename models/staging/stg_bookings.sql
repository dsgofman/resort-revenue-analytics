with source as (
    select * from {{ source('raw', 'bookings') }}
)

select
    booking_id,
    guest_id,
    resort_id,
    agent_id,
    cast(booking_date as date)          as booking_date,
    cast(checkin_date as date)          as checkin_date,
    cast(checkout_date as date)         as checkout_date,
    room_type,
    cast(nights as integer)             as nights,
    cast(nightly_rate_cents as bigint)  as nightly_rate_cents,
    cast(booked_amount_cents as bigint) as booked_amount_cents,
    {{ cents_to_dollars('booked_amount_cents') }} as booked_amount_usd,
    channel,
    status
from source
