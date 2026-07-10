{#
    Collapse the payment ledger to one row per booking and derive RECOGNIZED
    revenue: settled charges net of refunds, with pending amounts excluded.
    This is the number that legitimately diverges from booked revenue and drives
    the reconciliation mart.
#}
with payments as (
    select * from {{ ref('stg_payments') }}
)

select
    booking_id,
    sum(case when payment_status in ('settled', 'refunded') then amount_cents else 0 end)
        as recognized_amount_cents,
    sum(case when payment_status = 'settled'  then amount_cents else 0 end) as settled_amount_cents,
    sum(case when payment_status = 'refunded' then amount_cents else 0 end) as refunded_amount_cents,
    sum(case when payment_status = 'pending'  then amount_cents else 0 end) as pending_amount_cents,
    count(*) as payment_event_count
from payments
group by 1
