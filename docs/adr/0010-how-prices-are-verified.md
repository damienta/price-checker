# 0010. How prices are verified before you're alerted

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

A wrong alert is worse than no alert: you'd go to buy something and find it was a different
model, out of stock, refurbished, or a £15 accessory. The question is how much checking happens
automatically and what's left to you.

## Decision

Checks run in layers, each catching what the one before misses.

**1. When an item is added (Claude in chat)**
- The exact product is pinned down (model number, size, colour).
- Each link is probed. Only pages that show a price for the right product are kept.
- Keywords and exclude words are set for search sources, plus a minimum price at about 40% of
  normal, so accessories and scams are filtered out.

**2. Every listing, every run (the script)**
- GBP only, in stock only, new only unless the item allows used or refurbished. Condition comes
  from the page's `itemCondition` or from words like "refurbished" or "renewed" in the title.
- Search results must contain every keyword and none of the exclude words.
- Anything under the minimum price is ignored (25% of target if no minimum is set).
- On product pages, related-product blocks are skipped so another product's price isn't used.

**3. Across sources (the digest)**
- "✅ N sources agree" when other sources are within 2% of the best price.
- "lowest in 30 days" from the price history.
- Change since the last check (↓ or ↑), so a sudden odd jump stands out.
- Sources that couldn't be read are listed, not hidden.

**4. A second opinion (the Claude routine, ADR 0009)**
- Confirms or disputes the script's prices and flags wrong-product links as mismatches.

**5. You, before buying**
- Click through and check the price in the basket. No automated check sees delivery charges,
  membership-only prices (Prime, My John Lewis), basket-level vouchers or regional stock.

## Consequences

You shouldn't need to double-check the tracking, but you should always glance at the checkout
price, the same as with PriceSpy or camelcamelcamel.

Known gaps, in order of value to fix next:

1. **A "below target" alert backed by one source only** isn't marked as less certain. The digest
   could say "1 source, unconfirmed" and the Claude routine could re-check every below-target
   item specifically.
2. **No guard against sudden drops.** A price falling more than about 50% overnight is more often
   a parsing error or a different product than a real deal. It should be flagged, not celebrated.
3. **Delivery costs** are only included for eBay.
4. **Claude checks yesterday's results** rather than today's, so it can't confirm a drop the
   script finds the same morning.
