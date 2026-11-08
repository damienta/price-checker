# 0012. A "For you" feed built from HotUKDeals RSS

- **Status:** Accepted
- **Date:** 2026-11-08

## Context

Besides tracking known items, it's useful to see good deals you didn't know to look for.
HotUKDeals is the biggest UK deals community, and its public RSS feeds (allowed by robots.txt,
ADR 0006) include title, price, shop, category, image, post time and, on the hot feed, the
community vote score ("107°").

## Decision

`price-checker feed` reads the hot and new feeds plus a tag feed for every followed tag
(from `data/interests.json` and the watchlist), then scores each deal:

| Signal | Points |
|---|---|
| Matches a watchlist item | +60 |
| Contains one of your keywords | +35 |
| Came from a tag you follow | +25 |
| In a category you like | +15 |
| Votes | +12 × log10(1 + °) |

The total is multiplied by a freshness factor that halves every 18 hours (never below 0.2).
Muted categories, shops and words are dropped. The top 60 go to `data/feed.json` with the reasons
shown on each card. `.github/workflows/feed.yml` refreshes it six times a day.

Cards link to the deal on HotUKDeals rather than straight to the shop, so the site that found
the deal gets the visit.

## Consequences

- "Right now" means as of the last workflow run, which GitHub may start late (ADR 0003). The
  site shows the feed's age.
- Each feed returns the latest 30 items, so a very busy day can push deals out between runs.
- Scoring weights are guesses. Tune them in `feed.py` once there's a feel for what's useful.

**Revisit when:** the feed needs to be live. A free Cloudflare Worker that fetches and caches
the RSS for 15 minutes would let the site read it directly.
