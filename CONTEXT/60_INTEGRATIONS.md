# Integrations — dbt-resort-analytics

## Claude Code CLI (the NL→SQL engine)
- `ai_analyst/generator.py` shells out to `claude -p "<prompt>" --output-format text`
  (optionally `--model <name>`), 180s timeout. Uses the **local Claude Code login** — no
  API key, no metered usage tracked by this repo.
- Auto-detection: `claude_available()` checks `shutil.which("claude")`. If absent, or if
  the subprocess raises for any reason, `nl_to_sql()` silently falls back to
  `demo_nl_to_sql()` (keyword-matched canned queries) — the app never hard-fails on a
  missing/broken CLI.
- No secrets/env vars involved for this integration.

## DuckDB
- Embedded, file-based (`resort.duckdb` at repo root, gitignored, rebuilt by `dbt build`).
- The AI analyst opens its connection `read_only=True` (`ai_analyst/app.py`) — deliberate
  defense in depth alongside the SQL gate.

## Snowflake (portability target, not actively used)
- `profiles.yml` `snowflake` target reads `SNOWFLAKE_ACCOUNT` / `_USER` / `_PASSWORD` /
  `_ROLE` (default `TRANSFORMER`) / `_DATABASE` (default `RESORT_ANALYTICS`) /
  `_WAREHOUSE` (default `COMPUTE_WH`) / `_SCHEMA` (default `ANALYTICS`) from the
  environment. No credentials committed; no evidence this target has been exercised
  against a real account (demonstrates portability, not a live integration).

## GitHub Pages
- Serves the committed `docs/` folder (dbt-generated static docs/lineage) at
  https://dsgofman.github.io/resort-revenue-analytics/. Regenerated locally via
  `dbt docs generate --profiles-dir .` and committed — no CI/CD publishes it
  automatically (see 40_STATE.md — no `.github/workflows/`).

## GitHub repo
- `origin` → https://github.com/dsgofman/resort-revenue-analytics.git (personal
  `dsgofman` account, per brain machines.md's work/personal GitHub separation — this is
  a personal-account project).
