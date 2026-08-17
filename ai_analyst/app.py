"""Resort AI Analyst - a Streamlit app that turns plain-English questions into governed,
read-only SQL over the dbt warehouse.

Flow: question -> Claude Code writes SQL -> verification gate -> read-only DuckDB -> chart.
Run:  streamlit run app.py

The visual layer matches the project's deck (navy ink, cool grays, red reserved for
refusals). Chart colors are CVD-validated pairs; red/green are reserved for gate verdicts
and never reused as series colors.
"""
import html
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

st.set_page_config(page_title="Resort AI Analyst", layout="wide", page_icon=":shield:")

# ---- design tokens (deck-matched; chart pairs validated for CVD separation) ----
INK, INK2, MUTE = "#16202e", "#43536a", "#6b7a90"
GRID, EDGE = "#e8ecf1", "#dce1e7"
BLUE, AMBER = "#3a62b0", "#c07f16"   # series pair: identity
RED, GREEN = "#b3341f", "#1e7a4c"    # reserved: verdicts and negative-variance polarity only

st.markdown(
    """
    <style>
      [data-testid="stToolbar"] { display: none; }
      #MainMenu, footer { visibility: hidden; }
      .block-container { padding-top: 2.4rem; max-width: 1080px; }
      .rk { font-size: .72rem; letter-spacing: .16em; color: #6b7a90; font-weight: 600;
            text-transform: uppercase; }
      .rt { font-size: 2.05rem; letter-spacing: -.02em; color: #16202e; font-weight: 700;
            margin: .05rem 0 .15rem; line-height: 1.15; }
      .rsub { color: #43536a; max-width: 68ch; margin: 0 0 .4rem; }
      .stButton button { border: 1px solid #dce1e7; color: #43536a; font-size: .84rem;
                         min-height: 3.3rem; }
      .stButton button:hover { border-color: #10233f; color: #10233f; }
      .gate { border-left: 4px solid; border-radius: 0 8px 8px 0;
              padding: .75rem 1rem; margin: .35rem 0 .9rem; }
      .gate .glab { font-size: .64rem; letter-spacing: .14em; color: #6b7a90;
                    font-weight: 600; margin-bottom: .12rem; text-transform: uppercase; }
      .gate .gmsg { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
                    font-weight: 600; font-size: .93rem; line-height: 1.45; }
      .gate.blocked { border-color: #b3341f; background: #fbf3f1; }
      .gate.blocked .gmsg { color: #b3341f; }
      .gate.passed { border-color: #1e7a4c; background: #eef7f1; }
      .gate.passed .gmsg { color: #1e7a4c; }
      code { color: #10233f; }
    </style>
    """,
    unsafe_allow_html=True,
)


def gate_verdict(ok, reason):
    """Render the gate verdict as a styled panel (mirrors the deck's refusal styling)."""
    cls = "passed" if ok else "blocked"
    msg = "PASSED &middot; " + html.escape(reason) if ok else "BLOCKED &middot; " + html.escape(reason)
    st.markdown(
        f'<div class="gate {cls}"><div class="glab">Verification gate</div>'
        f'<div class="gmsg">{msg}</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- charts

MONEY_KEYS = ("usd", "revenue", "commission", "booked", "recognized", "amount", "variance")


def _money(col):
    c = col.lower()
    return any(k in c for k in MONEY_KEYS) and not c.endswith("pct")


def _title(col):
    return col.replace("_", " ")


def _themed(chart):
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(gridColor=GRID, gridDash=[2, 3], labelColor=MUTE, titleColor=INK2,
                        domainColor=EDGE, tickColor=EDGE, labelFontSize=12, titleFontSize=12,
                        labelLimit=280)
        .configure_legend(orient="top", direction="horizontal", title=None,
                          labelColor=INK2, labelFontSize=12, symbolSize=110)
    )


def _time_col(df):
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    return None


def auto_chart(df):
    """Pick the chart by the data's job: polarity for variance, a line for time,
    sorted bars for category x measure. Chart failures never break the app."""
    if df is None or df.empty or len(df) > 60:
        return
    try:
        num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        tcol = _time_col(df)
        # categorical labels exclude the time column - a datetime is an axis, never a label
        cat = [c for c in df.columns
               if not pd.api.types.is_numeric_dtype(df[c]) and c != tcol]
        var_cols = [c for c in num if "variance" in c.lower() and not c.lower().endswith("pct")]
        # variance ranking needs a nameable row; time-only frames are trends, not rankings
        rankable = bool(cat) or ("resort_name" in df.columns and tcol is not None)

        plot = df.copy()
        note = None
        if len(plot) > 15 and (var_cols and rankable or not tcol):
            note = f"Chart shows the top 15 of {len(df)} rows - the full result is in the table."
            plot = plot.head(15)

        if var_cols and rankable:
            # Polarity: signed variance bars, red reserved for the negative pole.
            v = var_cols[0]
            if "resort_name" in plot.columns and tcol is not None:
                plot["label"] = (plot["resort_name"].astype(str) + "  -  "
                                 + pd.to_datetime(plot[tcol]).dt.strftime("%b %Y"))
                label = "label"
            else:
                label = cat[0]
            bars = (
                alt.Chart(plot)
                .mark_bar(cornerRadiusEnd=4, height=20)
                .encode(
                    y=alt.Y(f"{label}:N", sort=alt.EncodingSortField(field=v, order="descending"),
                            title=None),
                    x=alt.X(f"{v}:Q", title=_title(v), axis=alt.Axis(format="$~s")),
                    color=alt.condition(alt.datum[v] < 0, alt.value(RED), alt.value(BLUE)),
                    tooltip=[alt.Tooltip(c, format="$,.2f") if _money(c)
                             else alt.Tooltip(c) for c in df.columns],
                )
                .properties(height=max(240, 34 * len(plot)))
            )
            st.altair_chart(_themed(bars), use_container_width=True)

        elif tcol and num:
            # Change over time: chronological line(s), one hue per measure (validated pair).
            measures = [c for c in num if _money(c)][:2] or num[:2]
            longf = plot.melt(id_vars=[tcol], value_vars=measures,
                              var_name="series", value_name="value")
            longf["series"] = longf["series"].map(_title)
            line = (
                alt.Chart(longf)
                .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(filled=True, size=45))
                .encode(
                    x=alt.X(f"{tcol}:T", title=None, axis=alt.Axis(format="%b %Y")),
                    y=alt.Y("value:Q", title=None, axis=alt.Axis(format="$~s")),
                    color=alt.Color("series:N",
                                    scale=alt.Scale(domain=[_title(m) for m in measures],
                                                    range=[BLUE, AMBER][: len(measures)])),
                    tooltip=[alt.Tooltip(f"{tcol}:T", format="%b %Y", title="month"),
                             alt.Tooltip("series:N"),
                             alt.Tooltip("value:Q", format="$,.2f")],
                )
                .properties(height=340)
            )
            st.altair_chart(_themed(line), use_container_width=True)

        elif num and cat:
            # Category x measure: horizontal bars, sorted, direct labels when sparse.
            x, y = num[0], cat[0]
            money = _money(x)
            fmt_axis = "$~s" if money else "~s"
            base = alt.Chart(plot).encode(
                y=alt.Y(f"{y}:N", sort="-x", title=None),
                x=alt.X(f"{x}:Q", title=_title(x), axis=alt.Axis(format=fmt_axis)),
                tooltip=[alt.Tooltip(c, format="$,.2f") if _money(c)
                         else alt.Tooltip(c) for c in df.columns],
            )
            bars = base.mark_bar(color=BLUE, cornerRadiusEnd=4, height=20)
            layers = bars
            if len(plot) <= 12:
                labels = base.mark_text(align="left", dx=5, color=INK2, fontSize=11.5).encode(
                    text=alt.Text(f"{x}:Q", format="$,.0f" if money else ",.0f")
                )
                layers = bars + labels
            st.altair_chart(
                _themed(layers.properties(height=max(240, 34 * len(plot)))),
                use_container_width=True,
            )
        else:
            return

        if note:
            st.caption(note)
    except Exception:
        pass  # a chart is a bonus, never a point of failure


# ---------------------------------------------------------------- page

st.markdown('<div class="rk">Resort Revenue Analytics &middot; governed text-to-SQL</div>',
            unsafe_allow_html=True)
st.markdown('<div class="rt">Resort AI Analyst</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="rsub">Ask in plain English. Claude Code writes the SQL, a verification gate '
    'confirms it is read-only and touches only approved tables, and it runs against the '
    'dbt warehouse.</p>',
    unsafe_allow_html=True,
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
    st.markdown(
        "**The five checks**\n"
        "1. Single statement only\n"
        "2. Read-only `SELECT` / `WITH`\n"
        "3. No side-effecting keywords\n"
        "4. Approved tables only\n"
        "5. Row cap enforced"
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
    gate_verdict(ok, reason if not ok else "read-only, approved tables only")
    if ok:
        try:
            con = duckdb.connect(DB_PATH, read_only=True)
            df = con.execute(safe_sql).fetchdf()
            con.close()
            st.subheader("Result")
            st.caption(f"{len(df)} row{'s' if len(df) != 1 else ''}")
            colcfg = {}
            for c in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[c]):
                    colcfg[c] = st.column_config.DatetimeColumn(_title(c), format="MMM YYYY")
                elif c.lower().endswith("pct") and pd.api.types.is_numeric_dtype(df[c]):
                    colcfg[c] = st.column_config.NumberColumn(_title(c), format="%.1f%%")
                elif pd.api.types.is_numeric_dtype(df[c]) and _money(c):
                    colcfg[c] = st.column_config.NumberColumn(_title(c), format="dollar")
                elif not pd.api.types.is_numeric_dtype(df[c]):
                    colcfg[c] = st.column_config.TextColumn(_title(c))
            try:
                st.dataframe(df, use_container_width=True, column_config=colcfg, hide_index=True)
            except Exception:
                st.dataframe(df, use_container_width=True)
            auto_chart(df)
        except Exception as exc:
            st.error(f"Query failed: {exc}")

with st.expander("Test the gate directly - paste raw SQL"):
    st.caption(
        "Feed the verification gate any SQL, bypassing generation. Verdict only - "
        "nothing entered here is ever executed."
    )
    raw_sql = st.text_area(
        "SQL to validate", key="gate_sql", height=100,
        placeholder="DELETE FROM fct_bookings WHERE cancelled = true",
    )
    if st.button("Run the gate") and raw_sql.strip():
        g_ok, g_reason, _ = validate_sql(raw_sql, ALLOWED_TABLES)
        gate_verdict(g_ok, g_reason if not g_ok else "read-only, approved tables only")
