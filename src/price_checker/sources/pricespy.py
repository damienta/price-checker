"""PriceSpy UK product pages: the individual shops, not just the lowest price.

PriceSpy's structured data only gives "lowest price across N shops", which hides who's
selling. The page also server-renders its first few shop offers, cheapest first. Each one
has the shop's logo (alt text = shop name) and a screen-reader label ending in the price:

    <img alt="OnBuy" ...> ... <a data-test="OfferClickoutButton">
      <span class="sr-only">OnBuy, Apple AirPods Pro 3 ..., £174.99</span>

We read those. If PriceSpy changes its markup, `extract_offers` falls back to the
structured-data lowest price, so the item doesn't go dark.
"""

from __future__ import annotations

import html as html_lib
import re

from price_checker.matching import condition_from_title, parse_price
from price_checker.models import Offer

_ROW = re.compile(r'data-sentry-component="OfferListItemTopLeft"')
_LOGO = re.compile(r'<img[^>]*\salt="([^"]+)"')
_LABEL = re.compile(
    r'data-test="OfferClickoutButton"[^>]*>\s*<span class="sr-only">(.*?)</span>', re.DOTALL
)
_PRICE_AT_END = re.compile(r",\s*(£[\d,]+(?:\.\d+)?)\s*$")
_OUT_OF_STOCK = re.compile(r"out of stock|not in stock|sold out", re.IGNORECASE)


def is_pricespy(url: str) -> bool:
    return "pricespy.co.uk/" in url


def shop_offers(page: str, url: str, item_id: str = "") -> list[Offer]:
    offers = []
    rows = _ROW.split(page)[1:]
    for row in rows:
        logo = _LOGO.search(row)
        label = _LABEL.search(row)
        if not logo or not label:
            continue
        shop = html_lib.unescape(logo.group(1)).strip()
        text = html_lib.unescape(label.group(1)).strip()
        price_match = _PRICE_AT_END.search(text)
        price = parse_price(price_match.group(1)) if price_match else None
        if not shop or price is None:
            continue
        # The label is "Shop, listing title, £price".
        title = text[: price_match.start()].removeprefix(shop).strip(" ,")
        offers.append(
            Offer(
                item_id=item_id,
                source="PriceSpy",
                price=price,
                url=url,
                seller=shop,
                title=title,
                in_stock=False if _OUT_OF_STOCK.search(row[:6000]) else True,
                condition=condition_from_title(title),
            )
        )
    return offers
