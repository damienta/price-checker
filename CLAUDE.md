# price-checker

Personal UK price tracker. Python 3.11+, managed with `uv`. All state is plain files in `data/`;
there is no database. Prices are always GBP.

## Commands

```bash
uv sync                          # install
uv run pytest -q                 # tests
uv run price-checker list        # watchlist with latest prices
uv run price-checker probe URL   # what the script can read from a page
uv run price-checker add "Name" --target 250 --url URL --tag slug --keyword K --exclude W
uv run price-checker check --item ID   # check one item now and record it
uv run price-checker feed              # rebuild the For you feed (data/feed.json)
cd web && npm run dev                  # website, reading the local data/ folder
```

`data/shops.json` decides which shops count: `blocked` ones (OnBuy and other marketplaces) are
shown but never the best price, `trusted` ones are known UK retailers, anything else is labelled
unverified. When the user says they do or don't trust a shop, edit that file.

Items can also be added from the website: it opens a GitHub issue (`.github/ISSUE_TEMPLATE/track.yml`)
and `.github/workflows/track.yml` runs `price-checker add-from-issue`.

The website (`web/`, React + Vite + Tailwind) reads `data/*.json` at runtime. If you change a
data file's shape, update `web/src/lib/types.ts` to match. The user's interests for the For you
feed are in `data/interests.json`; edit it when they say what they do or don't want to see.

## When the user asks to track something

The user will name products or paste links in chat. For each one:

1. **Pin down the exact product.** Model number, size, colour if it matters. Ask only if it's
   genuinely ambiguous (e.g. "AirPods" could be four products).
2. **Find pages the script can check every day.** Web search for, in this order:
   - its **PriceSpy UK** page (`pricespy.co.uk/product.php?p=...`): lowest price across many shops
   - its **PriceRunner UK** page (`pricerunner.com/pl/...`): cheapest shop and its name
   - 1 to 3 big UK retailer pages that stock it (Currys, John Lewis, AO, Very, Richer Sounds, ...)
   Run `uv run price-checker probe URL` on each. Only add URLs that print a price. Amazon and
   Argos block scripts: don't add them as URLs (the Claude routine checks those instead).
3. **Pick search words.** `--keyword` for each word a listing title must contain (brand plus model
   number is usually right), `--exclude` for look-alikes (accessories, cases, older models,
   "for", "compatible"). Set `--min-price` to about 40% of the normal price so accessories and
   scams are ignored.
4. **Find a HotUKDeals tag.** Check `https://www.hotukdeals.com/rss/tag/<slug>` returns items
   (e.g. `headphones`, `sony`, `air-fryer`). Add one or two with `--tag`.
5. **Add it**, then `uv run price-checker check --item <id>` and show the user what was found.
6. Commit `data/watchlist.json` (and the updated `data/latest.json` / `data/history.csv`) with a
   message like `track: Sony WH-1000XM5 (target £250)` and push to `main`, so the morning run
   picks it up. Ask before pushing if the user hasn't said to.

Target price: use what the user says. If they don't give one, ask, or suggest the current best
price minus about 10%.

## Architecture decisions

Read `docs/adr/` before changing how data is stored, scheduled, fetched or sent. When you make
a decision of that size (new storage, new hosting, a new kind of source, anything with a cost
or a legal angle), add an ADR from `docs/adr/template.md` and list it in `docs/adr/README.md`.

## Rules

- Respect robots.txt: the fetcher enforces it, so never work around a "robots.txt asks bots not
  to read this page" error by changing the user agent or URL.
- The user agent is honest (`price-checker/0.1`). Don't impersonate a browser.
- The repo is public: never commit secrets. Webhook URLs and API keys live in GitHub secrets.
