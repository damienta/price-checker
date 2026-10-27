# price-checker

A personal UK price tracker. Tell Claude what you want ("track the Sony WH-1000XM5, alert me
under £250"), and every morning at 8am a digest lands in Discord with the best price found
across UK shops, price comparison sites and deal communities.

It runs for free on GitHub Actions. There is no server and no database: the watchlist and price
history are JSON and CSV files in [`data/`](data/), committed by the morning run, ready for a
frontend to read later.

```
 you → Claude Code ──► data/watchlist.json
                              │
 07:15  Claude routine ───────┤  searches by name (incl. Amazon, Argos), double-checks
                              │  yesterday's prices, adds new readable links
                              ▼
 08:00  GitHub Action ──► check every source ──► data/latest.json, data/history.csv
                              │
                              └──► Discord webhook: one morning digest
```

## Price sources

| Source | What it gives | Setup |
|---|---|---|
| **Product pages** (Currys, John Lewis, AO, Richer Sounds, ...) | That shop's price and stock, from the page's schema.org data | none |
| **PriceSpy UK** product pages | Lowest price across every shop PriceSpy tracks, per colour | none |
| **PriceRunner UK** product pages | Cheapest shop and its price | none |
| **HotUKDeals** RSS (per tag, plus "new" and "hot") | Deals and voucher codes people post, often before shops advertise them | none |
| **eBay UK** Browse API | Cheapest new buy-it-now listings delivered to the UK | free eBay developer keys |
| **Google Shopping UK** via SerpApi | Prices from shops not covered above | free SerpApi key (250 searches/month, budgeted automatically) |
| **Claude routine** | Anything else on the web, including Amazon and Argos | a Claude subscription |

The script uses an honest user agent (`price-checker/0.1`), waits between requests to the same
site, and obeys robots.txt, including wildcard rules. That's why it reads PriceRunner product
pages but not its search results, and HotUKDeals feeds but not its search.

## Morning message

```
☀️ Price check · Mon 26 Oct

🔥 Below target
Sony WH-1000XM5: £229.00 at Currys · target £250.00 · ↓£40.00 · ✅ 3 sources agree · lowest in 30 days

📉 Cheaper than last check
Air fryer: £79.00 at AO · target £60.00 · ↓£10.00

🆕 New deals posted
Air fryer: £74.99 at Argos · Ninja AF101 with code ...

🔍 Claude
Air fryer: £55.00 at Amazon · Prime only

⚠️ Couldn't check
TV: John Lewis: blocked by site (HTTP 403)
```

## Commands

```bash
uv sync
uv run price-checker add "Sony WH-1000XM5" --target 250 --url https://pricespy.co.uk/product.php?p=... --tag headphones
uv run price-checker probe https://www.currys.co.uk/products/...   # can the script read this page?
uv run price-checker check            # check everything now
uv run price-checker list             # latest prices
uv run price-checker digest           # print the morning message (--post sends it)
uv run pytest -q
```

Setup: **[docs/SETUP.md](docs/SETUP.md)**. The Claude routine: [docs/claude-routine.md](docs/claude-routine.md).

> This repo is public, so the watchlist and price history are public too. Secrets (Discord
> webhook, API keys) live only in GitHub Actions secrets.
