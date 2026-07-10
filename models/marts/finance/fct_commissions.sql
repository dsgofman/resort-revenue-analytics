{#
    Commission-grain fact. Recomputes the expected commission (booked amount x
    contractual channel rate) and flags where the recorded amount drifts from it -
    a small injected error rate that the data-quality tests are designed to catch.
#}
with commissions as (
    select * from {{ ref('stg_commissions') }}
),

bookings as (
    select booking_id, resort_id, channel, booked_amount_cents
    from {{ ref('stg_bookings') }}
)

select
    c.commission_id,
    c.booking_id,
    c.agent_id,
    b.resort_id,
    b.channel,
    c.commission_rate,
    c.commission_amount_cents                                   as recorded_commission_cents,
    cast(round(b.booked_amount_cents * c.commission_rate) as bigint) as expected_commission_cents,
    {{ cents_to_dollars('c.commission_amount_cents') }}         as recorded_commission_usd,
    {{ cents_to_dollars('cast(round(b.booked_amount_cents * c.commission_rate) as bigint)') }}
                                                                as expected_commission_usd,
    abs(c.commission_amount_cents - round(b.booked_amount_cents * c.commission_rate)) > 100
                                                                as is_commission_mismatch
from commissions c
inner join bookings b
    on c.booking_id = b.booking_id
