"""Where prices come from. Each source turns an Item into Offers (and errors)."""

from __future__ import annotations

from typing import Protocol

from price_checker.http import Fetcher
from price_checker.models import CheckError, Item, Offer
from price_checker.sources.pages import PageSource


class Source(Protocol):
    name: str

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]: ...


def build_sources(fetcher: Fetcher) -> list[Source]:
    return [PageSource(fetcher)]
