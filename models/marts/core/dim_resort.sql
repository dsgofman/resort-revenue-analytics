with resorts as (
    select * from {{ ref('stg_resorts') }}
)

select
    resort_id,
    resort_name,
    city,
    state,
    country,
    region,
    room_count,
    opened_date,
    date_diff('year', opened_date, current_date) as years_in_operation
from resorts
