"""Introspect the dbt-built DuckDB warehouse and produce a compact schema description
for the model prompt. Only the mart tables are exposed - the AI analyst never sees or
touches staging/intermediate models, which keeps the governed surface small and the
prompt focused."""
import duckdb

# The only tables the AI analyst may see or query (the governed semantic surface).
ALLOWED_TABLES = [
    "fct_bookings",
    "fct_revenue_reconciliation",
    "fct_commissions",
    "dim_resort",
    "dim_agent",
    "dim_guest",
    "dim_date",
]


def get_schema_context(db_path):
    """Return a compact 'table(col type, ...)' description of the allowed marts."""
    con = duckdb.connect(db_path, read_only=True)
    lines = []
    for table in ALLOWED_TABLES:
        try:
            cols = con.execute(f"PRAGMA table_info('{table}')").fetchall()
        except Exception:
            continue  # table not built yet; skip it rather than fail
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        lines.append(f"- {table}({col_desc})")
    con.close()
    return "\n".join(lines)
