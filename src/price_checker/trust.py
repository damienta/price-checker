"""Which shops to believe.

Comparison sites list anyone with a product feed, including marketplaces where the seller
behind the listing is unknown. data/shops.json sorts shops into three groups:

- trusted:  well-known UK retailers
- blocked:  never counts as the best price (still shown, marked as blocked)
- anything else is "unverified": it counts, but the digest and site label it

Set "only_trusted": true to ignore unverified shops too.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from price_checker.models import Offer

TRUSTED = "trusted"
UNVERIFIED = "unverified"
BLOCKED = "blocked"


def _words(name: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", name.lower().replace("'", "")))


def _matches(listed: str, shop: str) -> bool:
    """"John Lewis" matches "John Lewis & Partners" and "KRCS" matches "KRCS Apple Premium
    Reseller", but "AO" doesn't match "Aosom": the listed name must end at a word break."""
    listed, shop = _words(listed), _words(shop)
    return bool(listed) and (shop == listed or shop.startswith(listed + " "))


@dataclass
class ShopTrust:
    trusted: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    only_trusted: bool = False

    @classmethod
    def load(cls, path: Path) -> ShopTrust:
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            trusted=data.get("trusted", []),
            blocked=data.get("blocked", []),
            only_trusted=bool(data.get("only_trusted", False)),
        )

    def is_blocked(self, shop: str) -> bool:
        return any(_matches(b, shop) for b in self.blocked)

    def level(self, offer: Offer) -> str:
        # The shop is the seller when a comparison site names one, otherwise the site itself.
        shop = offer.seller if offer.seller and not offer.seller.startswith("cheapest of") else offer.source
        if any(_matches(b, shop) for b in self.blocked):
            return BLOCKED
        if any(_matches(t, shop) for t in self.trusted):
            return TRUSTED
        return UNVERIFIED

    def apply(self, offers: list[Offer]) -> list[Offer]:
        """Label each offer. With only_trusted, unverified shops are treated as blocked."""
        for offer in offers:
            level = self.level(offer)
            offer.trust = BLOCKED if self.only_trusted and level == UNVERIFIED else level
        return offers
