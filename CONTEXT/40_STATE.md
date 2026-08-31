# State — dbt-resort-analytics

**Last updated:** 2026-08-31 (night shift, via /project-init — no code touched)

## Current phase
Portfolio-presentation polish, post-MVP. The dbt warehouse and the AI analyst app are
both feature-complete and green (`dbt build` passing, gate tests passing per README
badges). Recent commit history (newest first) is entirely about presentation, not new
functionality:
- `3f6b94b` — acknowledge destructive asks with a read-only notice; label offline default fallback
- `42966b4` — keep content clear of Streamlit's fixed header
- `786c7a1` — deck-matched visual system, chart engine by data shape, direct gate-test panel
- `d65aacc` — Portfolio presentation pass: visual README, hosted docs, app polish
- `99591b2` — Add AI analyst app: NL-to-SQL over the warehouse via Claude Code + a verification gate
- `49e71db` — Initial commit: resort revenue analytics dbt project

## Priorities / next steps
`(unverified — ask David)` — no open TODOs, issues, or roadmap surfaced in the repo
(no issue tracker, no TODO/FIXME comments found, no NIGHTLOG.md). Likely candidates based
on repo shape alone, not confirmed:
- Keep the Streamlit visual pass going if more polish is wanted (three of the last four
  commits are UI/visual refinements).
- The project isn't yet registered in `~/claude-brain/projects.md` — that classification
  (State/priority) is David's call, separately flagged to `nightshift/proposed.md`.

## Known gaps at init time
- No CLAUDE.md, no CONTEXT/, no NIGHTLOG.md existed before this session — this project
  had not yet been onboarded to the standard memory schema despite being actively committed.
- No CI configured (no `.github/workflows/`) — `dbt build` and `pytest` are run manually per README.
