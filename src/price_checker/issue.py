"""Add or remove items from GitHub issues (the website's "Add item" and "Remove" buttons open
one). Adding uses .github/ISSUE_TEMPLATE/track.yml, removing uses untrack.yml.

The issue form (.github/ISSUE_TEMPLATE/track.yml) renders its answers as markdown:

    ### Product
    Apple AirPods Pro 3
    ### Links
    https://pricespy.co.uk/product.php?p=15415649
    ### Target price (£)
    160
    ### Notes
    _No response_

`track.yml` passes that body here. Links are probed and only readable ones are kept. The
Claude routine fills in more links the next morning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from price_checker import store
from price_checker.http import Fetcher, FetchError
from price_checker.matching import parse_price
from price_checker.models import Item
from price_checker.sources.pages import extract_offers, site_name

_HEADING = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_URL = re.compile(r"https?://[^\s<>\"')]+")
NO_RESPONSE = "_No response_"
# Accessory words that make look-alike listings, used as default excludes.
DEFAULT_EXCLUDES = ["case", "cover", "compatible", "replacement", "for", "skin", "protector"]


@dataclass
class IssueRequest:
    name: str
    links: list[str] = field(default_factory=list)
    target: float | None = None
    notes: str = ""


def _sections(body: str) -> dict[str, str]:
    """{"product": "Apple AirPods Pro 3", ...} from the form's "### Heading" blocks."""
    sections: dict[str, str] = {}
    matches = list(_HEADING.finditer(body))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        value = body[match.end():end].strip()
        sections[match.group(1).lower()] = "" if value == NO_RESPONSE else value
    return sections


def parse_issue(body: str) -> IssueRequest:
    sections = _sections(body)

    def find(prefix: str) -> str:
        return next((v for k, v in sections.items() if k.startswith(prefix)), "")

    name = find("product").splitlines()[0].strip() if find("product") else ""
    links = list(dict.fromkeys(u.rstrip(".,") for u in _URL.findall(find("links"))))
    if not name and links:
        name = links[0]
    return IssueRequest(name=name, links=links, target=parse_price(find("target")), notes=find("notes"))


def add_from_issue(body: str, fetcher: Fetcher | None = None) -> tuple[Item | None, str]:
    """Add the requested item. Returns it (or None) and a markdown reply for the issue."""
    request = parse_issue(body)
    if not request.name:
        return None, "I couldn't find a product name or link in this issue."

    fetcher = fetcher or Fetcher()
    kept, notes = [], []
    for url in request.links:
        try:
            offers = extract_offers(fetcher.get_text(url), url)
        except FetchError as exc:
            notes.append(f"- ❌ {site_name(url)}: {exc}. The Claude routine will look for it instead.")
            continue
        if not offers:
            notes.append(f"- ❌ {site_name(url)}: no price on the page.")
            continue
        kept.append(url)
        cheapest = min(offers, key=lambda o: o.price)
        notes.append(f"- ✅ {site_name(url)}: £{cheapest.price:,.2f} ({cheapest.where()})")

    item = Item(
        id=store.slugify(request.name),
        name=request.name,
        target_price=request.target,
        exclude=list(DEFAULT_EXCLUDES),
        urls=kept,
        added=date.today().isoformat(),
        notes=request.notes,
    )
    items, created = store.upsert_item(store.load_watchlist(), item)
    store.save_watchlist(items)

    target = f" with a target of £{request.target:,.2f}" if request.target else ""
    reply = [f"{'Added' if created else 'Updated'} **{request.name}**{target} (`{item.id}`)."]
    if notes:
        reply += ["", "Links:", *notes]
    if not kept:
        reply += [
            "",
            "No readable links yet. The 7:15 Claude routine will search for this by name and add "
            "PriceSpy, PriceRunner and shop pages it can check.",
        ]
    return item, "\n".join(reply)


def remove_from_issue(body: str) -> tuple[Item | None, str]:
    """Remove the item named in an untrack issue ("### Item" holds its id or name)."""
    ref = (_sections(body).get("item") or "").splitlines()[0:1]
    if not ref or not ref[0].strip():
        return None, "I couldn't find which item to remove in this issue."
    item = store.remove_item(ref[0].strip())
    if item is None:
        ids = ", ".join(f"`{i.id}`" for i in store.load_watchlist()) or "nothing"
        return None, f"Nothing on the watchlist matches `{ref[0].strip()}`. Tracked now: {ids}."
    return item, f"Removed **{item.name}** (`{item.id}`). Its price history is kept in `data/history.csv`."
