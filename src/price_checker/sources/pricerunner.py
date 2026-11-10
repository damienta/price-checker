"""PriceRunner UK product pages: every individual listing, with a link to the shop.

The structured data on a PriceRunner product page names only the single cheapest offer. The
page also embeds the app's own data, which has two parts we use:

    "merchants": {"2137": {"id": "2137", "name": "Amazon", ...}, ...}
    "offers": [{"id": "...", "merchantId": "2137",
                "url": "https://clk.klarna.com/uk/gotostore/v1/...",   <- goes to the shop
                "name": "Apple AirPods Pro 3 ...",                      <- the shop's title
                "price": {"amount": "200.00"}, "shippingCost": {"amount": "0.00"},
                "stockStatus": "IN_STOCK", ...}, ...]

That list follows the page's default filters (new or unspecified condition, in stock), so used
and refurbished listings aren't in it. Each listing's title is also checked for words like
"refurbished", and delivery is added to the price.

If PriceRunner changes that data, we fall back to its "filter by shop" menu (`af_MERCHANT`,
shop names and lowest prices but no shop links), then to the structured data.
"""

from __future__ import annotations

import json
import re

from price_checker.matching import condition_from_title, parse_price
from price_checker.models import Offer

_OFFERS = re.compile(r'"offers":\[\{"id":"')
_MERCHANTS = '"merchants":{'
_MERCHANT_FILTER = re.compile(r'"id":"af_MERCHANT".*?"filterOptions":(\[.*?\]),"type":"MERCHANT"', re.DOTALL)
_decoder = json.JSONDecoder()


def is_pricerunner(url: str) -> bool:
    return "pricerunner.com/" in url and "/pl/" in url


def shop_offers(page: str, url: str, item_id: str = "") -> list[Offer]:
    return _listings(page, url, item_id) or _merchant_filter(page, url, item_id)


def _decode_at(page: str, start: int) -> object | None:
    """Parse one JSON value starting at `start` in the page, wherever it ends."""
    try:
        value, _ = _decoder.raw_decode(page, start)
    except ValueError:
        return None
    return value


def _listings(page: str, url: str, item_id: str) -> list[Offer]:
    for match in _OFFERS.finditer(page):
        offers = _decode_at(page, match.start() + len('"offers":'))
        merchants_at = page.rfind(_MERCHANTS, 0, match.start())
        merchants = _decode_at(page, merchants_at + len(_MERCHANTS) - 1) if merchants_at >= 0 else None
        if not isinstance(offers, list) or not isinstance(merchants, dict):
            continue
        found = []
        for raw in offers:
            if not isinstance(raw, dict) or "merchantId" not in raw:
                continue
            shop = (merchants.get(str(raw["merchantId"])) or {}).get("name")
            price = parse_price((raw.get("price") or {}).get("amount"))
            if not shop or price is None or (raw.get("price") or {}).get("currency", "GBP") != "GBP":
                continue
            delivery = parse_price((raw.get("shippingCost") or {}).get("amount")) or 0.0
            title = str(raw.get("name") or "")
            found.append(
                Offer(
                    item_id=item_id,
                    source="PriceRunner",
                    price=round(price + delivery, 2),
                    url=str(raw.get("url") or url),
                    seller=shop,
                    title=title,
                    in_stock=raw.get("stockStatus") in (None, "IN_STOCK", "PREORDER"),
                    condition=condition_from_title(title),
                )
            )
        if found:
            return found
    return []


def _merchant_filter(page: str, url: str, item_id: str) -> list[Offer]:
    match = _MERCHANT_FILTER.search(page)
    options = _decode_at(match.string, match.start(1)) if match else None
    if not isinstance(options, list):
        return []
    found = []
    for option in options:
        if not isinstance(option, dict):
            continue
        low = option.get("lowestPrice") or {}
        price = parse_price(low.get("amount"))
        name = str(option.get("name") or "").strip()
        if not name or price is None or low.get("currency", "GBP") != "GBP":
            continue
        found.append(
            Offer(item_id=item_id, source="PriceRunner", price=price, url=url, seller=name, in_stock=True)
        )
    return found
