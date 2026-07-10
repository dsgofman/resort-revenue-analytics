{#
    Booking-grain fact, materialized incrementally: on a normal run only bookings
    newer than the current max booking_date are processed (delete+insert keeps the
    unique key clean). This is the pattern used for large append-mostly event
    tables in a real warehouse.
#}
{{
    config(
        materialized='incremental',
        unique_key='booking_id',
        incremental_strategy='delete+insert'
    )
}}

with enriched as (
    select * from {{ ref('int_bookings_enriched') }}
)

select
    booking_id,
    guest_id,
    resort_id,
    agent_id,
    booking_date,
    checkin_date,
    checkout_date,
    room_type,
    nights,
    channel,
    status,
    booked_amount_cents,
    recognized_amount_cents,
    variance_cents,
    {{ cents_to_dollars('booked_amount_cents') }}     as booked_amount_usd,
    {{ cents_to_dollars('recognized_amount_cents') }} as recognized_amount_usd,
    {{ cents_to_dollars('variance_cents') }}          as variance_usd
from enriched

{% if is_incremental() %}
where booking_date > (select max(booking_date) from {{ this }})
{% endif %}
