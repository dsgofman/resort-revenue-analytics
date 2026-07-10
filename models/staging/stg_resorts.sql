with source as (
    select * from {{ source('raw', 'resorts') }}
)

select
    resort_id,
    resort_name,
    city,
    state,
    country,
    region,
    cast(room_count as integer)   as room_count,
    cast(opened_date as date)     as opened_date
from source
