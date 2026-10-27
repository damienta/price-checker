# 0007. Use price comparison sites as the main sources

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

The goal is the best UK price, not the price at one shop. Checking every retailer directly means
finding and maintaining dozens of links per item.

## Options considered

- **Retailer pages only**: exact, but you only see the shops you thought to add.
- **Search engines / Google Shopping only**: broad, but rate-limited or paid at volume.
- **Price comparison product pages**: PriceSpy UK and PriceRunner UK already track many shops per
  product, and their product pages are allowed by robots.txt and publish structured data.

## Decision

For each item, aim for: a PriceSpy UK page (lowest across all its shops, per colour), a PriceRunner
UK page (cheapest shop and its name), and 1 to 3 retailer pages as independent checks. Add
HotUKDeals tag feeds for deals and voucher codes that comparison sites miss. `CLAUDE.md` tells
Claude to find these when an item is added.

## Consequences

- A handful of links per item covers dozens of shops.
- Comparison sites update on their own schedule, so their price can lag the shop by hours. The
  retailer pages and the Claude routine catch disagreements (ADR 0010).
- Comparison sites may include marketplace sellers or items with expensive delivery. The digest
  shows who the seller is, so you can judge.
- Some products aren't on PriceSpy or PriceRunner (niche or own-brand items). For those, retailer
  pages and search sources do the work.
