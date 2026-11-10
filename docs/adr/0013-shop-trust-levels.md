# 0013. Name the real shop, and decide which shops to believe

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

PriceSpy's structured data only says "lowest price £174.99 across 15 shops". The digest showed
that as the best price, but the shop behind it was OnBuy, a marketplace where the actual seller
is often unknown. A headline price you wouldn't buy from is worse than no headline at all.

## Decision

1. **Read the shops, not the summary.** `sources/pricespy.py` reads the first five shop offers
   PriceSpy renders on the product page: logo alt text gives the shop, and each offer's
   screen-reader label ends in its price. If PriceSpy changes its markup, we fall back to the
   structured-data lowest price.

   `sources/pricerunner.py` does the same for PriceRunner, which gives more: its product page
   embeds the app's own data, a `merchants` map and an `offers` list with **every individual
   listing** (33 for AirPods Pro 3): shop, title, price, delivery cost, stock and a link that
   goes straight to that shop. The list follows the page's default filters (new or unspecified
   condition, in stock). Delivery is added to the price. If that data moves, it falls back to the
   "filter by shop" menu (`af_MERCHANT`), then to structured data.

   Every price links to the seller: PriceSpy's `go-to-shop` and PriceRunner's `gotostore`
   redirects take a click to that shop's listing, not to the comparison page. (Those redirect
   paths are off-limits to bots in robots.txt; the script never fetches them, it only stores the
   link for you to click.)
2. **Sort shops into three groups** in `data/shops.json`:
   - **trusted**: well-known UK retailers
   - **blocked** (OnBuy, Comet, Fruugo, Wish, Temu, AliExpress, ...): dropped as soon as a check
     finds them. Not saved, not in the digest, not on the site. Each check also removes their
     rows from `history.csv`, so a shop blocked later disappears from the chart and the 30-day
     low too. Comet is on the list because OnBuy bought the brand in 2025 and its listings are
     the same marketplace listings (identical titles and prices).
   - **unverified**: everything else. Counts, but is labelled in the digest and on the site.
   - `"only_trusted": true` treats unverified shops as blocked.
   - A listed name matches a shop name that starts with it at a word break: "John Lewis" matches
     "John Lewis & Partners", but "AO" doesn't match "Aosom".
3. Older history rows that only said "cheapest of N shops" are left out of "lowest in 30 days"
   and the price chart, since they may have been a blocked shop.

## Consequences

- AirPods Pro 3: the headline used to be £174.99 with no shop named (it was OnBuy). Now it's
  £194.99 at Gadcet (unverified), with Amazon and AO at £200 as the cheapest trusted shops.
- Only PriceSpy's first five shops are visible to the script; PriceRunner covers the rest.
- Both readers depend on page markup that isn't a public API. Tests use trimmed copies of the
  real pages, and each falls back to the structured-data price, so a redesign degrades the
  detail rather than losing the item.
- The trusted list is a judgement call. Edit `data/shops.json` (or ask Claude) as you learn
  which shops you're happy buying from.
