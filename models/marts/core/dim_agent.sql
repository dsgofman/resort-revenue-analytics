with agents as (
    select * from {{ ref('stg_agents') }}
)

select
    agent_id,
    agent_name,
    territory,
    hire_date,
    is_active
from agents
