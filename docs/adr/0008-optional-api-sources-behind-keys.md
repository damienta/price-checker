# 0008. Keep paid-tier APIs optional and budgeted

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Official APIs are more reliable than pages, but most have free tiers with limits, need sign-up,
or turn paid at volume. The project must work at £0 with no keys at all.

## Decision

- The core sources (product pages, HotUKDeals) need nothing.
- **eBay Browse API** turns on when `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` are set. The
  default free limit (5,000 calls a day) is far above our use.
- **Google Shopping via SerpApi** turns on when `SERPAPI_KEY` is set. The free plan has 250
  searches a month, so each run spends at most `budget / 31` searches on the items searched
  longest ago, and usage is recorded in `data/serpapi_usage.json` so the monthly cap is never
  passed. The budget defaults to 240 and can be changed with the `SERPAPI_MONTHLY_BUDGET`
  repository variable.
- Error messages from API sources never include request URLs, because SerpApi keys travel in the
  query string.

## Consequences

- With 8+ items, each item gets a Google Shopping search every few days rather than daily.
- Paid data sources (Keepa for Amazon history, Apify actors, PriceRunner partner data) were
  left out on cost. Each would be one new file in `sources/` if it becomes worth paying for.

**Revisit when:** there are other users (free tiers are per account, so API costs grow with
users), or Amazon price history becomes important enough to pay Keepa for.
