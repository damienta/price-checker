"""PriceRunner UK product pages: every shop, not just the cheapest.

The structured data on a PriceRunner product page names only the single cheapest offer. But
the page also embeds the data for its "filter by shop" menu, which lists every shop with its
lowest price:

    {"id":"af_MERCHANT", ... "filterOptions":[
        {"type":"merchantFilterOption","id":"104426","name":"OnBuy","count":1,
         "lowestPrice":{"amount":"174.99","currency":"GBP"}, ...}, ...]}

That menu follows the page's default filters, which are new (or unspecified) condition and in
stock. Used and refurbished offers are off by default, so these are prices for new stock.
"""

from __future__ import annotations

import json
import re

from price_checker.models import Offer

_MERCHANT_FILTER = re.compile(r'"id":"af_MERCHANT".*?"filterOptions":(\[.*?\]),"type":"MERCHANT"', re.DOTALL)


def is_pricerunner(url: str) -> bool:
    return "pricerunner.com/" in url and "/pl/" in url


def shop_offers(page: str, url: str, item_id: str = "") -> list[Offer]:
    match = _MERCHANT_FILTER.search(page)
    if not match:
        return []
    try:
        options = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    offers = []
    for option in options:
        if not isinstance(option, dict):
            continue
        low = option.get("lowestPrice") or {}
        try:
            price = float(low.get("amount"))
        except (TypeError, ValueError):
            continue
        name = str(option.get("name") or "").strip()
        if not name or low.get("currency", "GBP") != "GBP":
            continue
        offers.append(
            Offer(
                item_id=item_id,
                source="PriceRunner",
                price=price,
                url=url,
                seller=name,
                in_stock=True,
                condition="new",
            )
        )
    return offers
