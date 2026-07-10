{#
    Calendar dimension built with the dbt_utils date_spine macro (demonstrates
    package use). Spans the booking window with one row per day.
#}
with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2026-01-01' as date)"
    ) }}
)

select
    cast(date_day as date)                              as date_day,
    extract(year  from date_day)                        as calendar_year,
    extract(quarter from date_day)                      as calendar_quarter,
    extract(month from date_day)                        as calendar_month,
    strftime(cast(date_day as date), '%B')              as month_name,
    extract(day from date_day)                          as day_of_month,
    extract(dow from date_day)                          as day_of_week,
    strftime(cast(date_day as date), '%A')              as day_name,
    case when extract(dow from date_day) in (0, 6)
         then true else false end                       as is_weekend,
    date_trunc('month', cast(date_day as date))         as first_day_of_month
from spine
