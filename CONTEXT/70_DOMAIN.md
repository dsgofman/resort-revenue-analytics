# Domain — dbt-resort-analytics

## The fictional business
"The Cabana Collection" — 40 resorts, 9,000 bookings, guests, booking agents, payments,
and commissions. All entities and data are synthetic (Faker), designed to *look* like a
real vacation-resort finance dataset.

## Core concepts
- **Booking** — a guest reserving a stay at a resort, possibly through an agent (who
  earns a commission). `fct_bookings` is the booking-grain fact (incremental).
- **Booked revenue** vs **recognized revenue** — the central business problem this
  project models:
  - *Booked* = the amount the booking record says is owed.
  - *Recognized* = what payment activity actually shows (partial deposits, refunds,
    rounding, never-charged cancellations all cause it to diverge from booked).
  - The gap between them, by resort × month, is the **reconciliation** —
    `fct_revenue_reconciliation` (`variance_usd`, `variance_pct`). Current synthetic
    result: $21.90M booked vs $19.25M recognized = $2.64M / 12.08% variance.
  - A singular test (`tests/assert_reconciliation_ties_to_bookings.sql`) asserts the
    reconciliation ties back to `fct_bookings` **to the cent** — the mart must never
    silently lose or invent money.
  - README notes this mart is deliberately modeled on a real problem David solved on
    the job (a large booked-vs-reported revenue gap), rebuilt on synthetic data.
- **Commission** — `fct_commissions` tracks expected-vs-recorded commission drift for
  agents (a smaller, parallel reconciliation pattern to the revenue one).
- **Governed AI surface** — the AI analyst is only ever allowed to see/query the mart
  layer (`ALLOWED_TABLES` in `ai_analyst/schema_context.py`: `fct_bookings`,
  `fct_revenue_reconciliation`, `fct_commissions`, `dim_resort`, `dim_agent`,
  `dim_guest`, `dim_date`) — staging and intermediate models are invisible to the model
  by construction, independent of the SQL gate.

## Vocabulary
- **The gate** = `ai_analyst/guardrails.py`'s `validate_sql()` — shorthand used in
  README/code comments for the verification step between AI-drafted SQL and execution.
- **Governed AI** — this project's throughline: an LLM may draft/propose, but a
  deterministic check decides what's allowed to actually run. Same discipline applied to
  both the dbt tests (data can't silently drift) and the SQL gate (AI can't silently act).
