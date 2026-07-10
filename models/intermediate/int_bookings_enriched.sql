{#
    Booking grain, enriched with recognized revenue and the booked-vs-recognized
    variance. Bookings with no payment rows (e.g. never-charged cancellations)
    recognize zero, so the left join is deliberate.
#}
with bookings as (
    select * from {{ ref('stg_bookings') }}
),

booking_payments as (
    select * from {{ ref('int_booking_payments') }}
)

select
    b.booking_id,
    b.guest_id,
    b.resort_id,
    b.agent_id,
    b.booking_date,
    b.checkin_date,
    b.checkout_date,
    b.room_type,
    b.nights,
    b.channel,
    b.status,
    b.booked_amount_cents,
    coalesce(bp.recognized_amount_cents, 0) as recognized_amount_cents,
    coalesce(bp.pending_amount_cents, 0)    as pending_amount_cents,
    b.booked_amount_cents - coalesce(bp.recognized_amount_cents, 0) as variance_cents,
    coalesce(bp.payment_event_count, 0)     as payment_event_count
from bookings b
left join booking_payments bp
    on b.booking_id = bp.booking_id
