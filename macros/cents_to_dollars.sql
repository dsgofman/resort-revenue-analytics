{#
    Convert an integer cents column to a rounded dollar amount.
    Money is stored as integer cents in the raw layer to avoid float drift;
    this macro is the single place that conversion happens, so every model
    presents dollars consistently.
#}
{% macro cents_to_dollars(column_name, precision=2) -%}
    round(({{ column_name }}) / 100.0, {{ precision }})
{%- endmacro %}
