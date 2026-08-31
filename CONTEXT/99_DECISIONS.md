# Decisions journal — dbt-resort-analytics

Append-only. Records why, not what (git history is the what).

## 2026-08-31 — Onboarded to the standard CONTEXT/ memory schema
Project was found during the brain's weekly drift pass: actively committed (6 commits
since initial commit, most recently 2026-08-31 per `night/2026-08-31` branch context)
but had no CLAUDE.md and no CONTEXT/ at all. Ran `/project-init` to scaffold
INDEX/OVERVIEW/ARCHITECTURE/OPERATIONS/STATE/INTEGRATIONS/DOMAIN/DECISIONS from the
repo's actual current state (README, dbt project files, `ai_analyst/` source) — no
existing docs were renamed, moved, or duplicated; this is new coverage, not a migration.
Registry classification (State/priority in `~/claude-brain/projects.md`) intentionally
left untouched — that's David's call, flagged separately to `nightshift/proposed.md`.
