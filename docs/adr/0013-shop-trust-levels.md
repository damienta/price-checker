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
   embeds the data behind its "filter by shop" menu (`af_MERCHANT`), listing **every** shop with
   its lowest price (27 for AirPods Pro 3). That menu follows the page's default filters, new or
   unspecified condition and in stock, so used and refurbished offers aren't mixed in.
2. **Sort shops into three groups** in `data/shops.json`:
   - **trusted**: well-known UK retailers
   - **blocked** (OnBuy, Fruugo, Wish, Temu, AliExpress, ...): still recorded and shown, struck
     through, but never the best price. The digest says when one was cheaper and got ignored.
   - **unverified**: everything else. Counts, but is labelled in the digest and on the site.
   - `"only_trusted": true` treats unverified shops as blocked.
   - A listed name matches a shop name that starts with it at a word break: "John Lewis" matches
     "John Lewis & Partners", but "AO" doesn't match "Aosom".
3. Older history rows that only said "cheapest of N shops" are left out of "lowest in 30 days"
   and the price chart, since they may have been a blocked shop.

## Consequences

- AirPods Pro 3: the headline used to be £174.99 with no shop named (it was OnBuy). Now it's
  £174.99 at Comet (unverified), with OnBuy shown and struck through, and Laptops Direct at
  £199 as the cheapest trusted shop.
- Only PriceSpy's first five shops are visible to the script; PriceRunner covers the rest.
- Both readers depend on page markup that isn't a public API. Tests use trimmed copies of the
  real pages, and each falls back to the structured-data price, so a redesign degrades the
  detail rather than losing the item.
- The trusted list is a judgement call. Edit `data/shops.json` (or ask Claude) as you learn
  which shops you're happy buying from.
