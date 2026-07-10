-- Singular data-quality test: the reconciliation mart must not lose or invent money.
-- Total booked revenue in fct_revenue_reconciliation has to equal total booked
-- revenue in fct_bookings, to the cent. Any row returned = a failure.
with recon as (
    select sum(booked_revenue_usd) as total from {{ ref('fct_revenue_reconciliation') }}
),

fact as (
    select sum(booked_amount_usd) as total from {{ ref('fct_bookings') }}
)

select
    recon.total as reconciliation_total,
    fact.total  as bookings_total,
    recon.total - fact.total as difference
from recon
cross join fact
where abs(recon.total - fact.total) > 0.01
