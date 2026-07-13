"""Resort AI Analyst - a Streamlit app that turns plain-English questions into governed,
read-only SQL over the dbt warehouse.

Flow: question -> Claude Code writes SQL -> verification gate -> read-only DuckDB -> chart.
Run:  streamlit run app.py
"""
import os

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from generator import claude_available, nl_to_sql
from guardrails import validate_sql
from schema_context import ALLOWED_TABLES, get_schema_context

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("AI_ANALYST_DB", os.path.join(REPO_ROOT, "resort.duckdb"))

st.set_page_config(page_title="Resort AI Analyst", layout="wide")


def auto_chart(df):
    if df is None or df.empty:
        return
    num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    if num and cat and len(df) <= 50:
        st.subheader("Chart")
        st.altair_chart(
            alt.Chart(df.head(50)).mark_bar().encode(
                x=alt.X(cat[0], sort="-y"), y=alt.Y(num[0]), tooltip=list(df.columns)
            ),
            use_container_width=True,
        )


st.title("Resort AI Analyst")
st.caption(
    "Ask in plain English. Claude Code writes the SQL, a verification gate confirms it is "
    "read-only and touches only approved tables, and it runs against the dbt warehouse."
)

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. **Claude Code** turns your question into SQL (headless `claude -p`, no API key)\n"
        "2. A **verification gate** rejects anything that is not read-only or that references "
        "tables outside the approved set\n"
        "3. The query runs **read-only** on DuckDB\n"
        "4. You get the result and a chart\n\n"
        "The gate is the same *verify-before-you-trust-AI-output* discipline this project "
        "is modeled on."
    )
    force_demo = st.checkbox("Offline demo mode (no Claude Code call)", value=not claude_available())
    engine_label = (
        "offline demo" if force_demo
        else "Claude Code (headless)" if claude_available()
        else "offline demo (Claude Code not found)"
    )
    st.caption(f"Engine: {engine_label}")
    st.caption(f"Warehouse: {os.path.basename(DB_PATH)}")

EXAMPLES = [
    "Which resort-months had the biggest booked vs recognized revenue variance?",
    "Total booked revenue by region",
    "Top agents by commission",
    "Monthly booked vs recognized revenue trend",
]
st.write("**Try one:**")
for col, ex in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    if col.button(ex, use_container_width=True):
        st.session_state["question"] = ex

question = st.text_input("Your question", key="question")

if question:
    schema = get_schema_context(DB_PATH)
    with st.spinner("Asking Claude Code for SQL..." if not force_demo else "Building SQL..."):
        sql, engine = nl_to_sql(question, schema, prefer_demo=force_demo)

    st.subheader("Generated SQL")
    st.caption(f"engine: {engine}")
    st.code(sql, language="sql")

    ok, reason, safe_sql = validate_sql(sql, ALLOWED_TABLES)
    if not ok:
        st.error(f"Verification gate BLOCKED this query: {reason}")
    else:
        st.success("Verification gate passed: read-only, approved tables only.")
        try:
            con = duckdb.connect(DB_PATH, read_only=True)
            df = con.execute(safe_sql).fetchdf()
            con.close()
            st.subheader("Result")
            st.dataframe(df, use_container_width=True)
            auto_chart(df)
        except Exception as exc:
            st.error(f"Query failed: {exc}")
