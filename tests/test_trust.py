import csv
from pathlib import Path

from price_checker import store
from price_checker.matching import best_offer
from price_checker.models import CheckRun, Item, Offer
from price_checker.sources.pages import extract_offers
from price_checker.trust import ShopTrust

PRICESPY = (Path(__file__).parent / "fixtures" / "pricespy_offers.html").read_text(encoding="utf-8")
URL = "https://pricespy.co.uk/product.php?p=15415649"


def test_pricespy_lists_each_shop_not_just_the_lowest():
    offers = extract_offers(PRICESPY, URL, "airpods")
    assert [(o.seller, o.price) for o in offers] == [
        ("OnBuy", 174.99),
        ("Gadcet", 194.99),
        ("A1 Tech Deals", 198.99),
    ]
    assert all(o.source == "PriceSpy" and o.in_stock for o in offers)
    # Each price links to that shop through PriceSpy's redirect, not to the comparison page.
    assert offers[1].url == "https://pricespy.co.uk/go-to-shop/40430/offer/55996075868538?client_id=1551"
    assert offers[1].title.startswith("Apple AirPods Pro 3 Wireless Earbuds")
    assert offers[1].where() == "Gadcet (via PriceSpy)"


def test_pricerunner_reads_each_listing_with_its_shop_link_and_delivery():
    page = (Path(__file__).parent / "fixtures" / "pricerunner_listings.html").read_text(encoding="utf-8")
    url = "https://www.pricerunner.com/pl/94-3216399795/Headphones/Apple-AirPods-Pro-3-White-Compare-Prices"
    offers = extract_offers(page, url, "airpods")
    assert [(o.seller, o.price) for o in offers] == [
        ("OnBuy", 174.99),
        ("Amazon", 200.0),
        ("Laptops Direct", 203.99),  # £199.00 + £4.99 delivery
        ("Comet", 174.99),
        ("Gadcet", 194.99),
    ]
    assert all(o.url.startswith("https://clk.klarna.com/uk/gotostore/") for o in offers)
    assert offers[1].title.startswith("Apple AirPods Pro 3")


def test_blocked_shops_are_dropped_from_the_check():
    from price_checker.checker import run_check

    class Fake:
        name = "fake"

        def check(self, item):
            return [Offer(item.id, "PriceRunner", 174.99, "u", seller="OnBuy"), Offer(item.id, "PriceRunner", 200, "u", seller="Amazon")], []

    run = run_check([Item(id="a", name="A")], [Fake()], trust=ShopTrust(trusted=["Amazon"], blocked=["OnBuy"]))
    assert [(o.seller, o.trust) for o in run.offers] == [("Amazon", "trusted")]


def test_history_rows_for_blocked_shops_can_be_dropped(tmp_path):
    store.append_history(
        CheckRun("t1", [Offer("a", "PriceRunner", 174.99, "u", seller="Comet"), Offer("a", "Apple", 219, "u")]),
        tmp_path,
    )
    trust = ShopTrust(blocked=["Comet"])
    assert store.drop_history_rows(lambda r: trust.is_blocked(r["seller"] or r["source"]), tmp_path) == 1
    assert [r["source"] for r in store.load_history(tmp_path)] == ["Apple"]


def test_pricerunner_lists_every_shop_from_its_filter_menu():
    page = (Path(__file__).parent / "fixtures" / "pricerunner_offers.html").read_text(encoding="utf-8")
    url = "https://www.pricerunner.com/pl/94-3216399795/Headphones/Apple-AirPods-Pro-3-White-Compare-Prices"
    offers = extract_offers(page, url, "airpods")
    assert [(o.seller, o.price) for o in offers] == [
        ("A1 Tech Deals", 198.99),
        ("Amazon", 200.0),
        ("Ao", 200.0),
        ("Apple", 219.0),
    ]
    assert all(o.source == "PriceRunner" and o.condition == "new" for o in offers)
    # Without the shop menu, fall back to the single structured-data offer.
    [only] = extract_offers(page.split("<body>")[0], url)
    assert (only.seller, only.price) == ("OnBuy", 174.99)


def test_pricespy_falls_back_to_structured_data():
    page = (
        '<script type="application/ld+json">{"@type":"Product","name":"X","offers":'
        '{"@type":"AggregateOffer","lowPrice":10,"offerCount":3,"priceCurrency":"GBP"}}</script>'
    )
    [offer] = extract_offers(page, URL)
    assert offer.price == 10
    assert offer.where() == "PriceSpy"


def test_trust_levels_and_best_price():
    trust = ShopTrust(trusted=["Apple", "John Lewis"], blocked=["OnBuy"])
    offers = trust.apply(
        [
            Offer("a", "PriceSpy", 174.99, "u", seller="OnBuy"),
            Offer("a", "PriceSpy", 194.99, "u", seller="Gadcet"),
            Offer("a", "Apple", 219.0, "u"),
            Offer("a", "PriceRunner", 210.0, "u", seller="John Lewis & Partners"),
        ]
    )
    assert [o.trust for o in offers] == ["blocked", "unverified", "trusted", "trusted"]
    # A listed name only matches at a word break.
    assert ShopTrust(trusted=["AO"]).level(Offer("a", "PriceRunner", 1, "u", seller="Aosom")) == "unverified"
    assert ShopTrust(trusted=["AO"]).level(Offer("a", "PriceRunner", 1, "u", seller="Ao")) == "trusted"
    item = Item(id="a", name="A")
    assert best_offer(item, offers).seller == "Gadcet"

    strict = ShopTrust(trusted=["Apple", "John Lewis"], blocked=["OnBuy"], only_trusted=True)
    assert best_offer(item, strict.apply(offers)).price == 210.0


def test_load_missing_file_trusts_nobody_and_blocks_nobody(tmp_path):
    trust = ShopTrust.load(tmp_path / "shops.json")
    assert trust.apply([Offer("a", "Shop", 1, "u")])[0].trust == "unverified"


def test_history_header_is_upgraded(tmp_path):
    path = tmp_path / "history.csv"
    old = store.HISTORY_FIELDS[:-1]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=old, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"checked_at": "t1", "item_id": "a", "source": "S", "price": "5", "url": "u"})
    store.append_history(CheckRun("t2", [Offer("a", "S", 4, "u", trust="trusted")]), tmp_path)
    rows = store.load_history(tmp_path)
    assert [r["trust"] for r in rows] == ["", "trusted"]
    assert [r["price"] for r in rows] == ["5", "4"]
