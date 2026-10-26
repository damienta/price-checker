"""Data shapes shared by the sources, the store and the digest."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class Item:
    """One thing on the watchlist."""

    id: str
    name: str
    target_price: float | None = None
    # "new" ignores used/refurbished listings; "any" accepts them.
    condition: str = "new"
    # Words a search result's title must contain. Defaults to the words of `name`.
    keywords: list[str] = field(default_factory=list)
    # Words that rule a search result out (e.g. "case", "replacement pads").
    exclude: list[str] = field(default_factory=list)
    # Ignore anything cheaper than this: filters accessories and scams out of searches.
    min_price: float | None = None
    # Product pages checked directly: retailers, PriceSpy, PriceRunner.
    urls: list[str] = field(default_factory=list)
    # HotUKDeals tag slugs, e.g. "headphones" for hotukdeals.com/tag/headphones.
    hotukdeals_tags: list[str] = field(default_factory=list)
    # Whether keyword search sources (eBay, Google Shopping) look for this item.
    search: bool = True
    added: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Item:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def search_terms(self) -> list[str]:
        return self.keywords or self.name.split()

    def price_floor(self) -> float | None:
        if self.min_price is not None:
            return self.min_price
        if self.target_price:
            return round(self.target_price * 0.25, 2)
        return None


@dataclass
class Offer:
    """A price seen for an item on one source."""

    item_id: str
    source: str
    price: float
    url: str
    seller: str = ""
    title: str = ""
    in_stock: bool | None = None
    # "new", "used", "refurbished" or "unknown".
    condition: str = "new"
    currency: str = "GBP"
    # "price" for a listing we track, "deal" for a one-off post such as HotUKDeals.
    kind: str = "price"
    posted_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Offer:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def where(self) -> str:
        """Human label such as "Currys", "OnBuy (via PriceRunner)" or
        "PriceSpy (cheapest of 11 shops)"."""
        if self.seller.startswith("cheapest of"):
            return f"{self.source} ({self.seller})"
        if self.seller and self.seller.lower() != self.source.lower():
            return f"{self.seller} (via {self.source})"
        return self.source


@dataclass
class CheckError:
    """A source that could not be read for an item."""

    item_id: str
    source: str
    reason: str
    url: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckError:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckRun:
    checked_at: str
    offers: list[Offer] = field(default_factory=list)
    errors: list[CheckError] = field(default_factory=list)
