"""HotUKDeals: community-posted deals, often with voucher codes the shops don't advertise.

Uses the public RSS feeds (`/rss/tag/<slug>`, `/rss/new`, `/rss/hot`), which robots.txt
allows. The site's search pages are disallowed for bots, so tags are how we narrow it down.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from price_checker.http import Fetcher, FetchError
from price_checker.matching import condition_from_title, parse_price, title_matches
from price_checker.models import CheckError, Item, Offer

BASE = "https://www.hotukdeals.com"
# Fetched once per run and searched for every item, on top of each item's own tags.
GENERAL_FEEDS = ("new", "hot")


class HotUKDealsSource:
    name = "HotUKDeals"

    def __init__(self, fetcher: Fetcher, now: datetime | None = None, max_age_hours: int = 48) -> None:
        self.fetcher = fetcher
        self.cutoff = (now or datetime.now(timezone.utc)) - timedelta(hours=max_age_hours)
        self._feeds: dict[str, list[dict[str, str]] | FetchError] = {}

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]:
        offers: dict[str, Offer] = {}
        errors: list[CheckError] = []
        feeds = [f"tag/{t}" for t in item.hotukdeals_tags] + list(GENERAL_FEEDS)
        for feed in feeds:
            entries = self._feed(feed)
            if isinstance(entries, FetchError):
                # The general feeds are a bonus; only report the item's own tags.
                if feed.startswith("tag/"):
                    errors.append(CheckError(item.id, self.name, str(entries), f"{BASE}/rss/{feed}"))
                continue
            for entry in entries:
                offer = self._to_offer(item, entry)
                if offer and offer.url not in offers:
                    offers[offer.url] = offer
        return list(offers.values()), errors

    def _feed(self, feed: str) -> list[dict[str, str]] | FetchError:
        if feed not in self._feeds:
            try:
                self._feeds[feed] = parse_feed(self.fetcher.get_text(f"{BASE}/rss/{feed}"))
            except FetchError as exc:
                self._feeds[feed] = exc
            except ET.ParseError:
                self._feeds[feed] = FetchError("feed was not valid RSS")
        return self._feeds[feed]

    def _to_offer(self, item: Item, entry: dict[str, str]) -> Offer | None:
        title = entry.get("title", "")
        price = parse_price(entry.get("price", ""))
        if price is None or not title_matches(item, title):
            return None
        posted = entry.get("posted_at", "")
        if posted:
            try:
                if datetime.fromisoformat(posted) < self.cutoff:
                    return None
            except ValueError:
                pass
        return Offer(
            item_id=item.id,
            source=self.name,
            price=price,
            url=entry.get("link", ""),
            seller=entry.get("merchant", ""),
            title=title,
            condition=condition_from_title(title),
            kind="deal",
            posted_at=posted,
        )


def parse_feed(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    entries = []
    for node in root.iter("item"):
        entry = {
            "title": (node.findtext("title") or "").strip(),
            "link": (node.findtext("link") or "").strip(),
        }
        when = node.findtext("pubDate")
        if when:
            try:
                entry["posted_at"] = parsedate_to_datetime(when).isoformat()
            except (TypeError, ValueError):
                pass
        for child in node:
            # <pepper:merchant name="Currys" price="£229.00"/> in the site's own namespace.
            if child.tag.endswith("}merchant") or child.tag == "merchant":
                entry["merchant"] = child.get("name", "")
                entry["price"] = child.get("price", "")
        entries.append(entry)
    return entries
