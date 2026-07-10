"""Tests for the verification gate. These are pure logic and need no warehouse or model,
so they run anywhere: `python -m pytest ai_analyst/test_guardrails.py`.
"""
from guardrails import validate_sql

ALLOWED = ["fct_bookings", "fct_revenue_reconciliation", "dim_resort"]


def test_allows_plain_select_and_adds_limit():
    ok, _, safe = validate_sql("select * from fct_bookings", ALLOWED)
    assert ok
    assert "LIMIT" in safe.upper()


def test_allows_with_cte():
    ok, _, _ = validate_sql(
        "with x as (select resort_id from fct_bookings) select * from x", ALLOWED
    )
    assert ok


def test_preserves_existing_limit():
    ok, _, safe = validate_sql("select * from fct_bookings limit 5", ALLOWED)
    assert ok
    assert safe.lower().count("limit") == 1


def test_blocks_insert():
    ok, _, _ = validate_sql("insert into fct_bookings values (1)", ALLOWED)
    assert not ok


def test_blocks_update():
    ok, _, _ = validate_sql("update fct_bookings set nights = 1", ALLOWED)
    assert not ok


def test_blocks_drop():
    ok, _, _ = validate_sql("drop table fct_bookings", ALLOWED)
    assert not ok


def test_blocks_multiple_statements():
    ok, _, _ = validate_sql("select 1 from fct_bookings; drop table dim_resort", ALLOWED)
    assert not ok


def test_blocks_attach():
    ok, _, _ = validate_sql("attach 'evil.db' as e", ALLOWED)
    assert not ok


def test_blocks_unknown_table():
    ok, reason, _ = validate_sql("select * from secret_table", ALLOWED)
    assert not ok
    assert "approved set" in reason.lower()


def test_allows_scalar_function_named_like_keyword():
    # replace() is a scalar function and must NOT be blocked
    ok, _, _ = validate_sql("select replace(resort_id, 'R', 'X') from fct_bookings", ALLOWED)
    assert ok
