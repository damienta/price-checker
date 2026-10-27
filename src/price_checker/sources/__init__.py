"""Where prices come from. Each source turns an Item into Offers (and errors).

Product pages and HotUKDeals need no setup. eBay and Google Shopping switch on when
their API keys are in the environment (GitHub secrets in the scheduled run).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from price_checker.http import Fetcher
from price_checker.models import CheckError, Item, Offer
from price_checker.sources.ebay import EbaySource
from price_checker.sources.google_shopping import GoogleShoppingSource
from price_checker.sources.hotukdeals import HotUKDealsSource
from price_checker.sources.pages import PageSource


class Source(Protocol):
    name: str

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]: ...


def build_sources(fetcher: Fetcher, items: list[Item], data: Path) -> list[Source]:
    sources: list[Source] = [PageSource(fetcher), HotUKDealsSource(fetcher)]
    if os.environ.get("EBAY_CLIENT_ID") and os.environ.get("EBAY_CLIENT_SECRET"):
        sources.append(
            EbaySource(fetcher.client, os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"])
        )
    if os.environ.get("SERPAPI_KEY"):
        sources.append(
            GoogleShoppingSource(
                fetcher.client,
                os.environ["SERPAPI_KEY"],
                data / "serpapi_usage.json",
                items,
                monthly_budget=int(os.environ.get("SERPAPI_MONTHLY_BUDGET", "240")),
            )
        )
    return sources


def describe(sources: list[Source]) -> str:
    return ", ".join(s.name for s in sources)
