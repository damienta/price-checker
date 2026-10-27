# 0002. Store state as files in git, not a database

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

The state is small: a watchlist of maybe 5 to 50 items, one price row per source per item per
day, and the latest results. It must cost nothing to run, be easy to edit by hand or by Claude,
and be readable by a future frontend.

## Options considered

- **DynamoDB / Postgres / Supabase**: proper queries and multi-user support, but needs an
  account, credentials in CI, and a backend in front of it for the frontend to read.
- **SQLite file committed to git**: queryable, but binary diffs, and Claude can't easily edit it.
- **JSON and CSV in `data/`**: human-readable diffs, editable by anyone, free, and a static
  frontend can fetch them straight from GitHub.

## Decision

`data/watchlist.json` (input), `data/latest.json` (latest check, including the previous best
price per item), `data/history.csv` (append-only price log), `data/claude_findings.json` and
`data/serpapi_usage.json`. The morning workflow commits them.

## Consequences

- Git history is a free audit log of every price change.
- A frontend can be fully static (GitHub Pages / Vercel) and read the files directly.
- Two writers (the 8am workflow and the 7:15 Claude routine) can collide; the workflow does
  `pull --rebase` and retries, which is enough at two writes a day.
- `history.csv` grows by roughly 10 to 30 rows per item per day. That's fine for years at
  personal scale.

**Revisit when:** there's more than one user (per-user data, auth), anything needs writing from
a frontend, or `history.csv` passes about 50 MB. At that point move to a real database (e.g.
Postgres or DynamoDB, keyed by `user_id`) and keep the file layout as an export format.
