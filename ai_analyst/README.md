# Resort AI Analyst

A small Streamlit app that turns plain-English questions into **governed, read-only SQL**
over the dbt warehouse in this repo.

```
question -> Claude Code writes SQL -> verification gate -> read-only DuckDB -> table + chart
```

It is deliberately modeled on the governed-AI pattern it demonstrates: the model is free
to draft SQL, but nothing runs until a **verification gate** confirms the query is
read-only and touches only approved tables. AI drafts; the guardrail decides.

## Why it is built this way

- **No metered API key.** Natural-language-to-SQL runs through the local **Claude Code**
  CLI in headless mode (`claude -p`), so it uses your existing Claude Code rather than a
  paid API. This is the same "agentic SQL via Claude Code" idea, wired into an app.
- **Verification gate (`guardrails.py`).** Rejects anything that is not a single read-only
  `SELECT`/`WITH`, contains DDL/DML, or references a table outside the approved mart set,
  and caps rows. Fully unit-tested (`test_guardrails.py`).
- **Defense in depth.** The DuckDB connection is also opened `read_only=True`, so a query
  that somehow slipped the gate still could not write.
- **Governed surface.** The model only ever sees the mart tables (`schema_context.py`),
  not staging or raw data.

## Run it

From the repo root, after `dbt build` has created `resort.duckdb`:

```bash
pip install -r ai_analyst/requirements.txt
streamlit run ai_analyst/app.py
```

Then ask things like *"Which resort-months had the biggest booked vs recognized revenue
variance?"* If the `claude` CLI is not installed, the app runs in offline demo mode.

## Files

- `app.py` - Streamlit UI and the question -> SQL -> gate -> run -> chart flow
- `generator.py` - Claude Code headless call, with an offline demo fallback
- `guardrails.py` - the verification gate
- `schema_context.py` - exposes only the approved marts to the model
- `test_guardrails.py` - gate unit tests
