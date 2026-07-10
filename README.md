# Resort Revenue Analytics — a dbt project

A production-shaped [dbt](https://www.getdbt.com/) project that models a fictional
vacation-resort company ("the Cabana Collection") end to end: raw operational data →
tested, documented, layered models → a finance-grade **booked-vs-recognized revenue
reconciliation** mart.

It runs on **DuckDB** out of the box (zero setup, no cloud account) and is written to
run unchanged on **Snowflake** by switching the dbt target. All data is **100%
synthetic** (generated with Faker) — there is no real, proprietary, or personal data
anywhere in this repo.

> The reconciliation model is deliberately modeled on a real problem I solved on the
> job — resolving a large booked-vs-reported revenue gap into a governed single source
> of truth — rebuilt here on synthetic data so the technique is fully inspectable.

---

## What it demonstrates

| Area | Where |
|---|---|
| Layered modeling (staging → intermediate → marts) | `models/` |
| Sources read from external CSV (dbt-duckdb) | `models/staging/_sources.yml` |
| Dimensional design (conformed dims + fact tables) | `models/marts/core` |
| Incremental materialization | `models/marts/core/fct_bookings.sql` |
| Ephemeral intermediate models | `models/intermediate/` |
| SCD2 snapshot (`check` strategy) | `snapshots/snap_resorts.sql` |
| Reusable macro | `macros/cents_to_dollars.sql` |
| Generic tests (unique, not_null, relationships, accepted_values, accepted_range) | `models/**/*.yml` |
| Singular / business-rule test | `tests/assert_reconciliation_ties_to_bookings.sql` |
| Package use (`dbt_utils.date_spine`) | `models/marts/core/dim_date.sql` |
| Exposure (downstream dashboard in the lineage graph) | `models/marts/finance/_finance.yml` |
| Docs + generated lineage DAG | `dbt docs generate && dbt docs serve` |

---

## Data model

```
raw CSV sources ──> staging (stg_*) ──> intermediate (int_*) ──> marts
                                                                   ├── core:    dim_resort, dim_agent,
                                                                   │            dim_guest, dim_date,
                                                                   │            fct_bookings (incremental)
                                                                   └── finance: fct_commissions,
                                                                                fct_revenue_reconciliation
```

**The reconciliation:** payments intentionally diverge from booked amounts (partial
deposits, refunds, rounding, never-charged cancellations). `fct_revenue_reconciliation`
aggregates to resort × month and surfaces `booked_revenue_usd`,
`recognized_revenue_usd`, `variance_usd`, and `variance_pct`. A singular test asserts
the mart ties back to the booking fact to the cent, so the reconciliation can't
silently lose or invent money.

---

## Run it

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

dbt deps                              # install dbt_utils
python scripts/generate_data.py       # (optional) regenerate the synthetic CSVs
dbt build --profiles-dir .            # run + test every model, seed, snapshot
dbt docs generate --profiles-dir .    # build the docs site + lineage graph
dbt docs serve --profiles-dir .       # browse it at http://localhost:8080
```

`dbt build` runs all models, snapshots, and tests in one pass. The committed CSVs mean
it works on a fresh clone without the generation step.

## Running on Snowflake

The models are warehouse-portable. `profiles.yml` includes a `snowflake` target that
reads credentials from environment variables:

```bash
export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_PASSWORD=...
dbt build --profiles-dir . --target snowflake
```

No credentials are committed.
