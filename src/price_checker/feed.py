"""The "For you" feed: what's on HotUKDeals right now, ranked by what you care about.

Reads the public hot and new feeds plus a tag feed for each interest, scores every deal,
and writes the top ones to data/feed.json for the website. Interests come from
data/interests.json and from the watchlist (its tags and items count automatically).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from price_checker.http import Fetcher, FetchError
from price_checker.matching import parse_price, title_matches
from price_checker.models import Item
from price_checker.sources.hotukdeals import BASE, parse_feed

DEFAULT_INTERESTS: dict[str, Any] = {
    "tags": [],
    "categories": [],
    "keywords": [],
    "muted_categories": [],
    "muted_merchants": [],
    "muted_words": [],
}

# How much each signal adds to a deal's score.
WEIGHT_WATCHLIST = 60
WEIGHT_KEYWORD = 35
WEIGHT_TAG = 25
WEIGHT_CATEGORY = 15
# Votes: log scale so a 1,000° deal doesn't drown everything else.
WEIGHT_TEMPERATURE = 12
# A deal loses half its freshness every this many hours.
HALF_LIFE_HOURS = 18


@dataclass
class FeedDeal:
    id: str
    title: str
    url: str
    price: float | None
    merchant: str
    category: str
    image: str
    posted_at: str
    temperature: int | None
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    feeds: list[str] = field(default_factory=list)
    watchlist_item: str = ""


def load_interests(path: Path) -> dict[str, Any]:
    if not path.exists():
        return dict(DEFAULT_INTERESTS)
    data = json.loads(path.read_text(encoding="utf-8"))
    return {**DEFAULT_INTERESTS, **data}


def build_feed(
    fetcher: Fetcher,
    interests: dict[str, Any],
    watchlist: list[Item],
    now: datetime | None = None,
    limit: int = 60,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    tags = list(dict.fromkeys(interests["tags"] + [t for i in watchlist for t in i.hotukdeals_tags]))
    feeds = ["hot", "new"] + [f"tag/{t}" for t in tags]

    deals: dict[str, FeedDeal] = {}
    errors = []
    for feed in feeds:
        try:
            entries = parse_feed(fetcher.get_text(f"{BASE}/rss/{feed}"))
        except FetchError as exc:
            errors.append({"feed": feed, "reason": str(exc)})
            continue
        for entry in entries:
            deal = deals.get(entry["link"])
            if deal is None:
                deal = deals[entry["link"]] = _to_deal(entry)
            elif deal.temperature is None and entry.get("temperature"):
                deal.temperature = int(entry["temperature"])
            deal.feeds.append(feed)

    ranked = []
    for deal in deals.values():
        if _muted(deal, interests):
            continue
        _score(deal, interests, watchlist, now)
        ranked.append(deal)
    ranked.sort(key=lambda d: d.score, reverse=True)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "interests": {"tags": tags, "categories": interests["categories"], "keywords": interests["keywords"]},
        "deals": [asdict(d) for d in ranked[:limit]],
        "errors": errors,
    }


def _to_deal(entry: dict[str, str]) -> FeedDeal:
    temperature = entry.get("temperature")
    return FeedDeal(
        id=entry["link"].rsplit("-", 1)[-1],
        title=entry.get("title", ""),
        url=entry["link"],
        price=parse_price(entry.get("price", "")),
        merchant=entry.get("merchant", ""),
        category=entry.get("category", ""),
        image=entry.get("image", ""),
        posted_at=entry.get("posted_at", ""),
        temperature=int(temperature) if temperature else None,
    )


def _muted(deal: FeedDeal, interests: dict[str, Any]) -> bool:
    title = deal.title.lower()
    return (
        deal.category in interests["muted_categories"]
        or deal.merchant.lower() in (m.lower() for m in interests["muted_merchants"])
        or any(w.lower() in title for w in interests["muted_words"])
    )


def _score(deal: FeedDeal, interests: dict[str, Any], watchlist: list[Item], now: datetime) -> None:
    score = 0.0
    for item in watchlist:
        if title_matches(item, deal.title):
            score += WEIGHT_WATCHLIST
            deal.watchlist_item = item.id
            deal.reasons.append(f"On your watchlist: {item.name}")
            break
    for keyword in interests["keywords"]:
        if keyword.lower() in deal.title.lower():
            score += WEIGHT_KEYWORD
            deal.reasons.append(f"Mentions {keyword}")
            break
    tag_feeds = [f.removeprefix("tag/") for f in deal.feeds if f.startswith("tag/")]
    if tag_feeds:
        score += WEIGHT_TAG
        deal.reasons.append(f"You follow {tag_feeds[0]}")
    if deal.category in interests["categories"]:
        score += WEIGHT_CATEGORY
        deal.reasons.append(f"In {deal.category}")
    if deal.temperature and deal.temperature > 0:
        score += WEIGHT_TEMPERATURE * math.log10(1 + deal.temperature)
        if deal.temperature >= 100:
            deal.reasons.append(f"Hot: {deal.temperature}°")
    deal.score = round(score * _freshness(deal.posted_at, now), 2)


def _freshness(posted_at: str, now: datetime) -> float:
    try:
        hours = max((now - datetime.fromisoformat(posted_at)).total_seconds() / 3600, 0)
    except ValueError:
        return 0.5
    # Never below 0.2, so a very hot deal from yesterday can still show.
    return max(0.5 ** (hours / HALF_LIFE_HOURS), 0.2)
