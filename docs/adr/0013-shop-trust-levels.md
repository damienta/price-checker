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
2. **Sort shops into three groups** in `data/shops.json`:
   - **trusted**: well-known UK retailers
   - **blocked** (OnBuy, Fruugo, Wish, Temu, AliExpress, ...): still recorded and shown, struck
     through, but never the best price. The digest says when one was cheaper and got ignored.
   - **unverified**: everything else. Counts, but is labelled in the digest and on the site.
   - `"only_trusted": true` treats unverified shops as blocked.
3. Older history rows that only said "cheapest of N shops" are left out of "lowest in 30 days"
   and the price chart, since they may have been a blocked shop.

## Consequences

- AirPods Pro 3's best went from £174.99 (OnBuy) to £194.99 (Gadcet, unverified). That's the
  honest number.
- Only PriceSpy's first five shops are visible to the script. If all five are blocked, PriceSpy
  contributes nothing that day. Other sources and the Claude routine still run.
- The trusted list is a judgement call. Edit `data/shops.json` (or ask Claude) as you learn
  which shops you're happy buying from.
