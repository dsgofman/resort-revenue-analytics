# dbt-resort-analytics (Resort Revenue Analytics)

A dbt warehouse (DuckDB/Snowflake-portable) modeling a fictional resort company, plus a
Streamlit AI-analyst app that turns NL questions into governed, read-only SQL via
headless Claude Code and a deterministic verification gate. Full pitch: README.md.

## Project memory (CONTEXT/)
- Skim CONTEXT/INDEX.md first; read only the files the task needs.
- After a change that affects documented knowledge, update the mapped file.
- 99_DECISIONS.md is append-only: decisions/findings (why, not what — git is the what).
- End of a meaningful session: refresh 40_STATE.md (dated).

## Hard rules
- **All data stays synthetic.** `data/raw/*.csv` is Faker-generated and committed on
  purpose. Never add real, proprietary, or personal data to this repo.
- **Don't loosen the AI analyst's verification gate** (`ai_analyst/guardrails.py`) or
  widen `ALLOWED_TABLES` (`ai_analyst/schema_context.py`) without deliberately deciding
  to — the gate blocking non-read-only/non-whitelisted SQL is the entire point of the
  demo, not incidental strictness.
- **Don't regenerate `data/raw/*.csv`** (`scripts/generate_data.py`) casually — it
  reshuffles the synthetic data and changes the headline reconciliation numbers
  ($21.90M booked / $19.25M recognized / $2.64M variance) that the README and screenshots
  reference.
- `resort.duckdb` is a build artifact (gitignored) — never hand-edit or commit it.

## Running things
See CONTEXT/20_OPERATIONS.md for full setup/build/test commands (`dbt build
--profiles-dir .`, `streamlit run ai_analyst/app.py`, `pytest ai_analyst/`).

## Git
Personal GitHub account (`dsgofman`), remote `origin` →
github.com/dsgofman/resort-revenue-analytics. No project-specific commit-message
convention observed yet beyond plain descriptive messages (see `git log`).
