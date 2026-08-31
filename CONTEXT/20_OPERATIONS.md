# Operations — dbt-resort-analytics

## Setup
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
dbt deps                              # installs dbt_utils into dbt_packages/
```

## Build / test the warehouse
```bash
python scripts/generate_data.py       # optional — regenerates data/raw/*.csv (see 10_ARCHITECTURE.md caveat)
dbt build --profiles-dir .            # runs + tests every model, seed, snapshot against DuckDB
```
`profiles.yml` is project-local (not `~/.dbt/profiles.yml`), hence `--profiles-dir .`
everywhere. Default target `dev` = DuckDB, writes `resort.duckdb` (gitignored, rebuilt
each run). Alt target `snowflake`:
```bash
export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_PASSWORD=...
dbt build --profiles-dir . --target snowflake
```

## Run the AI analyst app
```bash
pip install -r ai_analyst/requirements.txt
streamlit run ai_analyst/app.py       # http://localhost:8501
```
Requires `resort.duckdb` to already exist (run `dbt build` first). Live NL→SQL needs the
`claude` CLI on PATH and logged in (no API key/env var needed); otherwise the app
auto-falls-back to its offline demo mode.

## Tests
- dbt: `dbt build` (or `dbt test`) — 61 models/tests/snapshots, README badge tracks the count.
- AI analyst gate: `pytest ai_analyst/test_guardrails.py` (or `pytest ai_analyst/`) — 10 unit
  tests on `guardrails.py`, README badge tracks the count.

## Docs site
`docs/` (`index.html`, `manifest.json`, `catalog.json`) is the committed output of
`dbt docs generate`, served by GitHub Pages at
https://dsgofman.github.io/resort-revenue-analytics/. Regenerate with:
```bash
dbt docs generate --profiles-dir .
```
then commit the changed files under `docs/` if the model graph changed.

## Environments / ports
- No deployed environment — DuckDB is a local file, the Streamlit app runs locally only
  (port 8501 default). GitHub Pages is the only "deployed" surface, and it's static docs.
- Secrets: none committed. Snowflake creds (if ever used) come from env vars
  (`SNOWFLAKE_ACCOUNT`/`USER`/`PASSWORD`/`ROLE`/`DATABASE`/`WAREHOUSE`/`SCHEMA`) — never
  put values in `profiles.yml`.

## Gitignore notes
`target/`, `dbt_packages/`, `logs/`, `.user.yml`, `*.duckdb`(`.wal`), `.venv/`,
`__pycache__/`, `*.pyc` are ignored. `data/raw/*.csv` is the one dbt-adjacent data
directory that IS committed (intentional — see 10_ARCHITECTURE.md).
