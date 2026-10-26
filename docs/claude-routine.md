# The Claude routine (the "double check")

The GitHub Action checks the links in the watchlist at 8am. This routine runs a bit earlier,
at **7:15am UK time**, on your Claude subscription. It searches the web for each item by name
(including Amazon and Argos, which block scripts), checks yesterday's prices still hold, and
writes what it finds to `data/claude_findings.json`. The 8am digest shows these under 🔍 Claude.

It also makes the script better over time: whenever it finds a page the script can read, it
adds that URL to the item so it's checked every day after that.

## Setting it up

In Claude Code, run `/schedule` (or open claude.ai/code → Routines) and create a routine:

- **Repository:** `damienta/price-checker`
- **Schedule:** daily at 07:15, Europe/London
- **Branch pushes:** allow pushing to `main` if the option is offered. If the routine can
  only push to `claude/` branches, that's fine: it falls back to `claude/findings` and the
  morning workflow reads it from there.
- **Prompt:** paste everything in the box below.

```text
You are the daily double-check for a personal UK price tracker in this repo. Read CLAUDE.md
first. Prices are GBP, UK sellers only, new condition unless the item says "condition": "any".

1. Read data/watchlist.json (what to track) and data/latest.json (yesterday's prices from
   the script, including errors for pages it couldn't read).

2. For each item, search the web for its current lowest UK price. Look at: Amazon UK, Argos,
   Currys, John Lewis, AO, Very, the brand's own UK store, PriceSpy UK, PriceRunner UK, and any
   other well-known UK retailer that shows up. Ignore marketplace sellers with no reviews,
   bundles, refurbished/used (unless the item allows them), and anything that isn't exactly
   the same product (check model numbers, sizes, storage, colour if the item names one).

3. Write data/claude_findings.json in exactly this shape:
   {
     "generated_at": "<now, ISO 8601 with timezone, e.g. 2026-10-26T07:20:00+00:00>",
     "findings": [ ... ]
   }
   where each finding is one of:
   - {"item_id", "kind": "cheaper", "price", "seller", "url", "note"}
       a price lower than the item's best in latest.json. "note" is for catches like
       "Prime members only", "ends tonight", "code SAVE10".
   - {"item_id", "kind": "confirmed", "price", "seller", "url"}
       you saw the same best price as latest.json (within 2%).
   - {"item_id", "kind": "mismatch", "note"}
       latest.json looks wrong, e.g. "AO now shows £99, script recorded £79" or
       "PriceSpy link is for the WF-1000XM5, not the WH-1000XM5".
   - {"item_id": "", "kind": "note", "note"}
       at most two general tips worth knowing, e.g. a sale starting this week at a
       retailer that stocks several watched items. Skip if there's nothing useful.
   Prices are numbers in pounds (229.0, not "£229"). Include the product URL, not a search page.

4. Improve the watchlist: if you found a retailer, PriceSpy UK or PriceRunner UK product page
   for an item that isn't in its "urls" yet, run `uv run price-checker probe <url>`. If it prints
   the right product and a price, add the URL to that item in data/watchlist.json (at most two
   new URLs per item per day). Never add Amazon or Argos URLs; they block scripts. If a URL in
   the watchlist is for the wrong product, remove it and mention it as a mismatch.

5. Commit data/claude_findings.json and data/watchlist.json with the message
   "claude: daily findings <date>" and push to main. If pushing to main is refused, push to
   the branch claude/findings instead (force-push is fine on that branch).

Do not change any code, workflows or other files. Do not post to Discord yourself.
```

## Checking it worked

After 7:15 the repo should have a new `claude: daily findings` commit (on `main` or on
`claude/findings`). If the 8am digest has no 🔍 Claude section, open the routine's latest run
in claude.ai/code to see what happened.
