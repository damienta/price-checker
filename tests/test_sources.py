import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from price_checker.http import Fetcher, new_client
from price_checker.models import Item
from price_checker.sources.ebay import EbaySource
from price_checker.sources.google_shopping import GoogleShoppingSource
from price_checker.sources.hotukdeals import HotUKDealsSource, parse_feed

FEED = (Path(__file__).parent / "fixtures" / "hotukdeals_headphones.xml").read_text(encoding="utf-8")
NOW = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)


def mock_client(handler):
    return new_client(transport=httpx.MockTransport(handler))


def test_parse_real_feed():
    entries = parse_feed(FEED)
    assert entries[0]["merchant"] == "eBay"
    assert entries[0]["price"] == "£97.30"
    assert entries[0]["title"].startswith("Sony WH-1000XM5")
    assert entries[0]["posted_at"] == "2026-10-26T15:27:40+00:00"


def test_hotukdeals_matches_item_and_fetches_each_feed_once():
    requested = []

    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /search\n")
        return httpx.Response(200, text=FEED)

    source = HotUKDealsSource(Fetcher(mock_client(handler), delay=0), now=NOW)
    xm5 = Item(id="xm5", name="Sony WH-1000XM5", hotukdeals_tags=["headphones"], condition="any")
    offers, errors = source.check(xm5)
    assert errors == []
    [offer] = offers  # same deal in all three feeds is reported once
    assert (offer.price, offer.seller, offer.condition, offer.kind) == (97.30, "eBay", "refurbished", "deal")

    other = Item(id="ex15", name="Sony MDR-EX15AP", hotukdeals_tags=["headphones"])
    assert [o.price for o in source.check(other)[0]] == [4.11]
    assert requested.count("/rss/tag/headphones") == 1
    assert requested.count("/rss/new") == 1


def test_hotukdeals_drops_old_posts():
    def handler(request):
        return httpx.Response(200, text="" if request.url.path == "/robots.txt" else FEED)

    later = datetime(2026, 11, 5, tzinfo=timezone.utc)
    source = HotUKDealsSource(Fetcher(mock_client(handler), delay=0), now=later)
    assert source.check(Item(id="x", name="Sony WH-1000XM5", condition="any"))[0] == []


def test_ebay_search():
    def handler(request):
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 7200})
        assert request.headers["authorization"] == "Bearer tok"
        assert request.headers["x-ebay-c-marketplace-id"] == "EBAY_GB"
        assert "conditionIds:{1000|1500}" in request.url.params["filter"]
        return httpx.Response(
            200,
            json={
                "itemSummaries": [
                    {"title": "Sony WH-1000XM5 Black NEW", "price": {"value": "229.00", "currency": "GBP"},
                     "itemWebUrl": "https://www.ebay.co.uk/itm/1", "conditionId": "1000",
                     "seller": {"username": "bob"},
                     "shippingOptions": [{"shippingCost": {"value": "4.99", "currency": "GBP"}}]},
                    {"title": "Ear pads for Sony WH-1000XM5", "price": {"value": "15", "currency": "GBP"},
                     "itemWebUrl": "https://www.ebay.co.uk/itm/2", "conditionId": "1000"},
                ]
            },
        )

    source = EbaySource(mock_client(handler), "id", "secret")
    item = Item(id="xm5", name="Sony WH-1000XM5", exclude=["pads"])
    offers, errors = source.check(item)
    assert errors == []
    assert [(o.price, o.seller) for o in offers] == [(233.99, "eBay seller bob")]


def test_google_shopping_respects_budget(tmp_path):
    calls = []

    def handler(request):
        calls.append(request.url.params["q"])
        return httpx.Response(
            200,
            json={"shopping_results": [
                {"title": "Ninja AF101 Air Fryer", "extracted_price": 79.0, "source": "Argos", "product_link": "https://g/1"},
                {"title": "Ninja AF101 Air Fryer (Renewed)", "extracted_price": 49.0, "source": "Amazon"},
            ]},
        )

    items = [Item(id=f"i{n}", name="Ninja AF101") for n in range(3)]
    usage = tmp_path / "serpapi_usage.json"
    source = GoogleShoppingSource(mock_client(handler), "key", usage, items, monthly_budget=62, now=NOW)
    results = [source.check(i)[0] for i in items]
    assert len(calls) == 2  # 62 a month = 2 a day
    assert [(o.price, o.condition) for o in results[0]] == [(49.0, "refurbished"), (79.0, "new")]
    assert results[0][1].seller == "Argos"
    assert json.loads(usage.read_text())["used"] == 2

    # Next run starts with the item that wasn't searched.
    again = GoogleShoppingSource(mock_client(handler), "key", usage, items, monthly_budget=62, now=NOW)
    assert "i2" in again.selected

    # Out of budget for the month: nothing runs.
    usage.write_text(json.dumps({"month": "2026-10", "used": 62, "last_searched": {}}))
    spent = GoogleShoppingSource(mock_client(handler), "key", usage, items, monthly_budget=62, now=NOW)
    assert spent.selected == set()
