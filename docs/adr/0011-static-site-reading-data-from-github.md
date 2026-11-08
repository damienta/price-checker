# 0011. A static website that reads data straight from GitHub

- **Status:** Accepted
- **Date:** 2026-11-08

## Context

The site shows the watchlist, today's prices, price history and the For you feed. The data
already lives in `data/` in a public repo (ADR 0002). It should cost nothing, need no server,
and show new prices as soon as a workflow commits them.

## Options considered

- **Bake the data into each build**: simple, but workflows that commit with `GITHUB_TOKEN` don't
  trigger other workflows, so the site would never redeploy after a price check.
- **An API in front of a database**: needed one day for other users, overkill for one.
- **Static site that fetches `raw.githubusercontent.com/.../data/*` at runtime**: always current,
  CORS is allowed, and only rebuilds when the website code changes.

## Decision

React + Vite in `web/`, deployed to GitHub Pages by `.github/workflows/pages.yml` when `web/**`
changes. In production it fetches `watchlist.json`, `latest.json`, `history.csv` and `feed.json`
from the `main` branch on raw.githubusercontent.com. In dev, Vite serves the local `data/` folder.

UI is built from the same pieces as the portfolio: shadcn/ui base components, React Bits
(Aurora, SpotlightCard, BlurText), Skiper UI (animated link underline, progressive blur) and
Framer Motion for scroll-in and layout animation.

## Consequences

- raw.githubusercontent.com caches for about five minutes, so the site can lag a commit slightly.
- The site is read-only. Adding items still happens through Claude Code (or later, a form that
  opens a pull request or calls an API).
- Anyone can load the site, the same as anyone can read the repo.

**Revisit when:** there are other users, or adding and editing items from the site is wanted.
Both need an API and auth.
