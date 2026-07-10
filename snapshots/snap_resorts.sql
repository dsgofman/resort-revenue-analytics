{#
    SCD2 snapshot of the resort dimension. Uses the `check` strategy on the
    attributes most likely to change over time (room_count, region), so if a
    resort adds rooms or is re-regioned, history is preserved with valid_from /
    valid_to rows rather than being overwritten. Demonstrates the snapshot pattern;
    on first run it captures the current state as the initial version.
#}
{% snapshot snap_resorts %}
{{
    config(
        target_schema='snapshots',
        unique_key='resort_id',
        strategy='check',
        check_cols=['room_count', 'region']
    )
}}

select
    resort_id,
    resort_name,
    city,
    state,
    region,
    room_count
from {{ ref('stg_resorts') }}

{% endsnapshot %}
