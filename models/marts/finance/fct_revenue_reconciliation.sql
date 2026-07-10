{#
    THE CENTERPIECE. Resort x month grain. Compares booked revenue (what was
    committed at booking) against recognized revenue (settled payments net of
    refunds) and surfaces the variance and variance percentage - the same
    booked-vs-reported reconciliation problem that, on the job, resolved ~$25M of
    variance into a governed single source of truth. Here it runs on synthetic data.
#}
with bookings as (
    select * from {{ ref('fct_bookings') }}
),

resorts as (
    select resort_id, resort_name, region from {{ ref('dim_resort') }}
),

by_resort_month as (
    select
        b.resort_id,
        date_trunc('month', b.booking_date)      as booking_month,
        count(*)                                 as booking_count,
        sum(b.booked_amount_cents)               as booked_cents,
        sum(b.recognized_amount_cents)           as recognized_cents
    from bookings b
    group by 1, 2
)

select
    m.resort_id,
    r.resort_name,
    r.region,
    m.booking_month,
    m.booking_count,
    {{ cents_to_dollars('m.booked_cents') }}                        as booked_revenue_usd,
    {{ cents_to_dollars('m.recognized_cents') }}                    as recognized_revenue_usd,
    {{ cents_to_dollars('m.booked_cents - m.recognized_cents') }}   as variance_usd,
    round(
        (m.booked_cents - m.recognized_cents) * 100.0 / nullif(m.booked_cents, 0), 2
    )                                                               as variance_pct
from by_resort_month m
inner join resorts r
    on m.resort_id = r.resort_id
