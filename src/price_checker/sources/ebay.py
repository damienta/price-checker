"""eBay UK through the official Browse API (free developer account, 5,000 calls/day).

Only runs when EBAY_CLIENT_ID and EBAY_CLIENT_SECRET are set. Searches new, buy-it-now
listings that deliver to the UK, cheapest first.
"""

from __future__ import annotations

import httpx

from price_checker.matching import condition_from_title, parse_price, title_matches
from price_checker.models import CheckError, Item, Offer

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"
# eBay condition ids: 1000 = New, 1500 = New other (open box).
NEW_CONDITIONS = "{1000|1500}"


class EbaySource:
    name = "eBay"

    def __init__(self, client: httpx.Client, client_id: str, client_secret: str) -> None:
        self.client = client
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]:
        if not item.search:
            return [], []
        try:
            data = self._search(item)
        except (httpx.HTTPError, ValueError) as exc:
            return [], [CheckError(item.id, self.name, f"API error: {exc}")]
        offers = []
        for summary in data.get("itemSummaries", []):
            offer = self._to_offer(item, summary)
            if offer:
                offers.append(offer)
        # The cheapest few are plenty; the rest is noise in latest.json.
        return sorted(offers, key=lambda o: o.price)[:5], []

    def _search(self, item: Item) -> dict:
        filters = ["buyingOptions:{FIXED_PRICE}", "deliveryCountry:GB", "priceCurrency:GBP"]
        if item.condition == "new":
            filters.append(f"conditionIds:{NEW_CONDITIONS}")
        floor = item.price_floor()
        if floor:
            filters.append(f"price:[{floor}..]")
        response = self.client.get(
            SEARCH_URL,
            params={
                "q": " ".join(item.search_terms()),
                "filter": ",".join(filters),
                "sort": "price",
                "limit": "50",
            },
            headers={"Authorization": f"Bearer {self._get_token()}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"},
        )
        response.raise_for_status()
        return response.json()

    def _get_token(self) -> str:
        if self._token is None:
            response = self.client.post(
                TOKEN_URL,
                data={"grant_type": "client_credentials", "scope": SCOPE},
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            self._token = response.json()["access_token"]
        return self._token

    def _to_offer(self, item: Item, summary: dict) -> Offer | None:
        title = summary.get("title", "")
        price_info = summary.get("price") or {}
        price = parse_price(price_info.get("value"))
        if price is None or price_info.get("currency", "GBP") != "GBP" or not title_matches(item, title):
            return None
        shipping = next(iter(summary.get("shippingOptions") or []), {}).get("shippingCost") or {}
        price += parse_price(shipping.get("value")) or 0.0
        condition = "new" if str(summary.get("conditionId", "1000")).startswith("1") else "used"
        if condition == "new":
            condition = condition_from_title(title)
        seller = (summary.get("seller") or {}).get("username", "")
        return Offer(
            item_id=item.id,
            source=self.name,
            price=round(price, 2),
            url=summary.get("itemWebUrl", ""),
            seller=f"eBay seller {seller}" if seller else "",
            title=title,
            in_stock=True,
            condition=condition,
        )
