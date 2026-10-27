# 0006. Respect robots.txt and identify the bot honestly

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Sites publish robots.txt to say which pages bots may read. Many price tools ignore it, pretend
to be a browser, or rotate IP addresses to avoid blocks. The repo is public and meant to grow
into something other people use, so how it behaves matters.

## Decision

- User agent `price-checker/0.1` with a link to this repo. No browser impersonation.
- Every page fetch is checked against robots.txt with our own parser, which supports `*` and `$`
  wildcards. Python's built-in parser silently ignores wildcard rules, so it would have allowed
  PriceRunner search pages that the site disallows.
- At least 2 seconds between requests to the same site.
- When a site blocks us, report it ("blocked by site (HTTP 403)") and move on. No workarounds.
- Prefer official feeds and APIs (HotUKDeals RSS, eBay Browse API) over pages.

## Consequences

- Some data is off-limits: PriceRunner and HotUKDeals search, and Amazon/Argos pages in practice.
  We use product pages, tag feeds and the Claude routine instead.
- Sites can opt out of this tool specifically by naming `price-checker` in robots.txt.
- Before this becomes a product, the terms of service of each source should be checked, not
  only robots.txt. Commercial use may need permission or an affiliate/data agreement.

**Revisit when:** turning this into a business. Robots.txt is the minimum, not a licence.
