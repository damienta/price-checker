"""Product pages: retailers, PriceSpy and PriceRunner.

Almost every shop puts schema.org Product data in the page as JSON-LD so search
engines can show prices. Reading that is far sturdier than scraping the visible
HTML, which changes every time a site is redesigned.
"""

from __future__ import annotations

import html as html_lib
import json
import re
from typing import Any, Iterator
from urllib.parse import urlsplit

from price_checker.http import Fetcher, FetchError
from price_checker.matching import parse_price
from price_checker.models import CheckError, Item, Offer

_JSONLD = re.compile(
    r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_META = re.compile(r"<meta\s[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", re.DOTALL)

SITE_NAMES = {
    "pricespy.co.uk": "PriceSpy",
    "pricerunner.com": "PriceRunner",
    "hotukdeals.com": "HotUKDeals",
    "amazon.co.uk": "Amazon",
    "argos.co.uk": "Argos",
    "currys.co.uk": "Currys",
    "johnlewis.com": "John Lewis",
    "ao.com": "AO",
    "very.co.uk": "Very",
    "ebay.co.uk": "eBay",
    "richersounds.com": "Richer Sounds",
    "scan.co.uk": "Scan",
    "box.co.uk": "Box",
    "overclockers.co.uk": "Overclockers",
    "diy.com": "B&Q",
    "screwfix.com": "Screwfix",
    "halfords.com": "Halfords",
    "boots.com": "Boots",
    "backmarket.co.uk": "Back Market",
    "ikea.com": "IKEA",
    "game.co.uk": "GAME",
    "smythstoys.com": "Smyths",
    "selfridges.com": "Selfridges",
    "harveynichols.com": "Harvey Nichols",
}

_IN_STOCK = ("instock", "limitedavailability", "onlineonly", "instoreonly", "preorder", "presale")
_OUT_OF_STOCK = ("outofstock", "soldout", "discontinued", "backorder")


def site_name(url: str) -> str:
    host = urlsplit(url).netloc.lower().split(":")[0]
    host = host.removeprefix("www.")
    for domain, name in SITE_NAMES.items():
        if host == domain or host.endswith("." + domain):
            return name
    return host.split(".")[0].capitalize() if host else "Unknown site"


class PageSource:
    name = "pages"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]:
        offers: list[Offer] = []
        errors: list[CheckError] = []
        for url in item.urls:
            site = site_name(url)
            try:
                found = extract_offers(self.fetcher.get_text(url), url, item.id)
            except FetchError as exc:
                errors.append(CheckError(item.id, site, str(exc), url))
                continue
            if not found:
                errors.append(CheckError(item.id, site, "no price found on the page", url))
            offers.extend(found)
        return offers, errors


def extract_offers(page: str, url: str, item_id: str = "") -> list[Offer]:
    """Every GBP price the page publishes for its main product."""
    site = site_name(url)
    products = list(_products(_jsonld_blocks(page)))
    chosen = [p for p in products if _same_url(p.get("url"), url)] or products
    offers = [o for product in chosen for o in _product_offers(product, url, site, item_id)]
    if not offers:
        offers = _meta_offers(page, url, site, item_id)
    return [o for o in offers if o.currency == "GBP"]


def _jsonld_blocks(page: str) -> Iterator[Any]:
    for raw in _JSONLD.findall(page):
        raw = raw.strip()
        if raw.startswith("<!--"):
            raw = raw.removeprefix("<!--").removesuffix("-->")
        try:
            yield json.loads(raw, strict=False)
        except json.JSONDecodeError:
            continue


def _types(node: dict[str, Any]) -> set[str]:
    kind = node.get("@type", [])
    return {kind} if isinstance(kind, str) else set(kind)


def _products(blocks: Iterator[Any]) -> Iterator[dict[str, Any]]:
    """The page's own products. Deliberately does not recurse into keys like
    `isSimilarTo`, so "customers also bought" prices are never picked up."""
    stack = list(blocks)
    while stack:
        node = stack.pop(0)
        if isinstance(node, list):
            stack.extend(node)
            continue
        if not isinstance(node, dict):
            continue
        types = _types(node)
        if "ProductGroup" in types:
            variants = node.get("hasVariant") or []
            stack.extend(variants if isinstance(variants, list) else [variants])
            if node.get("offers"):
                yield node
        elif "Product" in types or "IndividualProduct" in types:
            yield node
        else:
            for key in ("@graph", "mainEntity"):
                if key in node:
                    stack.append(node[key])


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _product_offers(product: dict[str, Any], url: str, site: str, item_id: str) -> list[Offer]:
    name = str(product.get("name") or "")
    offers: list[Offer] = []
    for raw in _as_list(product.get("offers")):
        if not isinstance(raw, dict):
            continue
        if "AggregateOffer" in _types(raw):
            nested = [o for o in _as_list(raw.get("offers")) if isinstance(o, dict)]
            expanded = [_offer(o, url, site, item_id, name) for o in nested]
            expanded = [o for o in expanded if o is not None]
            if expanded:
                offers.extend(expanded)
                continue
            price = parse_price(raw.get("lowPrice", raw.get("price")))
            if price is None:
                continue
            count = raw.get("offerCount")
            offers.append(
                Offer(
                    item_id=item_id,
                    source=site,
                    price=price,
                    url=url,
                    seller=f"cheapest of {count} shops" if count else "",
                    title=name,
                    in_stock=True,
                    currency=str(raw.get("priceCurrency") or "GBP").upper(),
                )
            )
        else:
            offer = _offer(raw, url, site, item_id, name)
            if offer is not None:
                offers.append(offer)
    return offers


def _offer(raw: dict[str, Any], url: str, site: str, item_id: str, name: str) -> Offer | None:
    spec = next((s for s in _as_list(raw.get("priceSpecification")) if isinstance(s, dict)), {})
    price = parse_price(raw.get("price", spec.get("price")))
    if price is None or price <= 0:
        return None
    currency = str(raw.get("priceCurrency") or spec.get("priceCurrency") or "GBP").upper()
    seller = raw.get("seller") or {}
    seller_name = seller.get("name", "") if isinstance(seller, dict) else str(seller)
    return Offer(
        item_id=item_id,
        source=site,
        price=price,
        url=url,
        seller=str(seller_name or ""),
        title=name,
        in_stock=_availability(raw.get("availability")),
        condition=_condition(raw.get("itemCondition")),
        currency=currency,
    )


def _availability(value: Any) -> bool | None:
    if not isinstance(value, str):
        return None
    key = value.rsplit("/", 1)[-1].lower()
    if key in _IN_STOCK:
        return True
    if key in _OUT_OF_STOCK:
        return False
    return None


def _condition(value: Any) -> str:
    if not isinstance(value, str):
        return "new"
    key = value.rsplit("/", 1)[-1].lower()
    if "refurbished" in key:
        return "refurbished"
    if "used" in key or "damaged" in key:
        return "used"
    return "new"


def _meta_offers(page: str, url: str, site: str, item_id: str) -> list[Offer]:
    """Fallback for pages with Open Graph product tags but no JSON-LD."""
    values: dict[str, str] = {}
    for tag in _META.findall(page):
        attrs = {k.lower(): html_lib.unescape(v) for k, _, v in _ATTR.findall(tag)}
        key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
        if key and "content" in attrs:
            values.setdefault(key.lower(), attrs["content"])
    price = parse_price(
        values.get("product:price:amount") or values.get("og:price:amount") or values.get("price")
    )
    if price is None:
        return []
    currency = (
        values.get("product:price:currency")
        or values.get("og:price:currency")
        or values.get("pricecurrency")
        or "GBP"
    )
    return [
        Offer(
            item_id=item_id,
            source=site,
            price=price,
            url=url,
            title=values.get("og:title", ""),
            currency=currency.upper(),
        )
    ]


def _same_url(candidate: Any, url: str) -> bool:
    if not isinstance(candidate, str):
        return False
    return html_lib.unescape(candidate).rstrip("/") == url.rstrip("/")
