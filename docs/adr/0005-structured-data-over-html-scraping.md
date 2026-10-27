# 0005. Read prices from structured data, not page HTML

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Each shop lays out its pages differently and redesigns them regularly. Writing a scraper per
site (CSS selectors, XPaths) means constant breakage and code to maintain.

## Options considered

- **Per-site CSS selectors**: precise, but one script per shop, and they break silently.
- **A headless browser (Playwright)**: handles JavaScript-only pages, but slow and heavy in CI,
  and looks more like the bots shops are trying to block.
- **An LLM reading every page**: works on anything, but costs money per check and can misread.
- **schema.org JSON-LD**: most shops publish `Product` / `Offer` data in the page so Google can
  show prices in search results. It's stable because breaking it would hurt their search ranking.

## Decision

`sources/pages.py` reads JSON-LD (`Product`, `ProductGroup` variants, `Offer`, `AggregateOffer`,
`@graph`, `priceSpecification`), falls back to Open Graph price tags, and deliberately skips
"similar products" blocks so another product's price isn't picked up. One parser covers every
shop that publishes this data. `price-checker probe URL` shows what it can read before a link is
added.

## Consequences

- Covers PriceSpy, PriceRunner and most big UK retailers without any per-site code.
- Pages that render prices only with JavaScript, or publish no structured data, can't be read.
  Those are left to the Claude routine rather than adding a browser.
- If a page publishes several products, we may report the wrong one. ADR 0010 covers how that's
  caught.

**Revisit when:** an important shop has no structured data. Add a small site-specific source for
that shop only, rather than switching approach.
