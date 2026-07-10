with source as (
    select * from {{ source('raw', 'agents') }}
)

select
    agent_id,
    agent_name,
    cast(hire_date as date) as hire_date,
    territory,
    case
        when lower(cast(is_active as varchar)) in ('true', '1', 't') then true
        else false
    end as is_active
from source
