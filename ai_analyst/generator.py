"""Natural-language question -> SQL, powered by the local Claude Code CLI in headless
mode (`claude -p`).

This uses your existing Claude Code install, so there is no metered API key: the same
"agentic SQL via Claude Code" pattern this project is modeled on, running the app.
If the CLI is not on PATH, it falls back to a small offline demo generator so the app
still runs (and can be tested) on a machine without Claude Code.
"""
import re
import shutil
import subprocess

_PROMPT = """You convert a business question into ONE read-only DuckDB SQL query.

Return ONLY the SQL. No prose, no explanation, no markdown code fences.

Rules:
- SELECT or WITH only. Never write, modify, or use any DDL/DML.
- Use ONLY these tables and columns:
{schema}
- For booked-vs-recognized revenue or variance questions, use fct_revenue_reconciliation.
- Alias aggregates, round money to 2 decimals, and add a sensible LIMIT for large results.

Question: {question}
"""


def claude_available():
    return shutil.which("claude") is not None


def _extract_sql(text):
    text = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    return text.strip().rstrip(";").strip()


def claude_nl_to_sql(question, schema, model=None, timeout=180):
    """Generate SQL by shelling out to `claude -p` (headless Claude Code)."""
    prompt = _PROMPT.format(schema=schema, question=question)
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if model:
        cmd += ["--model", model]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "claude CLI returned a non-zero exit code")
    return _extract_sql(result.stdout)


# --- offline demo fallback (keyword-matched canned queries) ---
_DEMO = [
    (("variance", "reconcil", "booked", "recognized", "gap"),
     "SELECT resort_name, booking_month, booked_revenue_usd, recognized_revenue_usd, "
     "variance_usd, variance_pct FROM fct_revenue_reconciliation ORDER BY variance_usd DESC LIMIT 10"),
    (("region",),
     "SELECT r.region, ROUND(SUM(b.booked_amount_usd), 2) AS booked_revenue "
     "FROM fct_bookings b JOIN dim_resort r ON b.resort_id = r.resort_id GROUP BY 1 ORDER BY 2 DESC"),
    (("agent", "commission"),
     "SELECT a.agent_name, ROUND(SUM(c.recorded_commission_usd), 2) AS commission "
     "FROM fct_commissions c JOIN dim_agent a ON c.agent_id = a.agent_id GROUP BY 1 ORDER BY 2 DESC LIMIT 10"),
    (("month", "trend", "time"),
     "SELECT booking_month, ROUND(SUM(booked_revenue_usd), 2) AS booked, "
     "ROUND(SUM(recognized_revenue_usd), 2) AS recognized "
     "FROM fct_revenue_reconciliation GROUP BY 1 ORDER BY 1"),
]
_DEMO_DEFAULT = ("SELECT resort_name, ROUND(SUM(booked_revenue_usd), 2) AS booked_revenue "
                 "FROM fct_revenue_reconciliation GROUP BY 1 ORDER BY 2 DESC LIMIT 10")


def demo_nl_to_sql(question):
    q = question.lower()
    for keys, sql in _DEMO:
        if any(k in q for k in keys):
            return sql
    return _DEMO_DEFAULT


def nl_to_sql(question, schema, prefer_demo=False, model=None):
    """Return (sql, engine) where engine is 'claude-code' or 'demo'."""
    if not prefer_demo and claude_available():
        try:
            return claude_nl_to_sql(question, schema, model=model), "claude-code"
        except Exception:
            pass  # fall back rather than crash the app
    return demo_nl_to_sql(question), "demo"
