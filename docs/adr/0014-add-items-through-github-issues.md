# 0014. Add items from the website through GitHub issues

- **Status:** Accepted
- **Date:** 2026-11-10

## Context

The website is static (ADR 0011), so it can't write to `data/watchlist.json`. Adding an item
meant opening Claude Code. A form on the site is quicker, but needs somewhere to send the request.

## Options considered

- **An API with auth** (e.g. a Cloudflare Worker holding a GitHub token): smooth, but a secret
  to protect and something new to host.
- **Edit the JSON on GitHub**: no new parts, but fiddly on a phone.
- **A pre-filled GitHub issue**: the form opens GitHub's issue page with everything filled in.
  You're already signed in to GitHub, so that's the authentication. A workflow does the rest.

## Decision

- "Add item" on the site opens `issues/new?template=track.yml` with the product, links, target
  and notes filled in (`.github/ISSUE_TEMPLATE/track.yml`).
- `.github/workflows/track.yml` runs on issues labelled `track` **opened by the repo owner only**,
  since the repo is public and anyone can open an issue. The issue body reaches the script as an
  environment variable, never pasted into a shell command.
- `price-checker add-from-issue` probes each link, keeps the readable ones, adds the item with
  default accessory excludes, checks its price, commits, replies with what it found and closes
  the issue.
- An item added by name only is picked up by the 7:15 Claude routine, which finds and adds
  PriceSpy, PriceRunner and shop links.

## Consequences

- Adding takes one extra click (Submit on GitHub) and works from a phone.
- Without Claude in the loop, a name-only item has no links until the next morning.
- **Revisit when:** other people need to add items. They'd need accounts and their own
  watchlists, which means an API (ADR 0002 and 0011).
