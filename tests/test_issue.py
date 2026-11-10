import httpx

from price_checker import store
from price_checker.http import Fetcher, new_client
from price_checker.issue import add_from_issue, parse_issue

BODY = """### Product

Apple AirPods Pro 3

### Links

https://shop.test/airpods
https://blocked.test/airpods.
https://shop.test/airpods

### Target price (£)

£160

### Notes

_No response_
"""

PAGE = (
    '<script type="application/ld+json">{"@type":"Product","name":"AirPods Pro 3",'
    '"offers":{"@type":"Offer","price":"199.00","priceCurrency":"GBP"}}</script>'
)


def test_parse_issue_form_body():
    request = parse_issue(BODY)
    assert request.name == "Apple AirPods Pro 3"
    assert request.links == ["https://shop.test/airpods", "https://blocked.test/airpods"]
    assert request.target == 160.0
    assert request.notes == ""


def test_add_from_issue_keeps_only_readable_links(tmp_path, monkeypatch):
    monkeypatch.setenv("PRICE_CHECKER_DATA", str(tmp_path))

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.host == "blocked.test":
            return httpx.Response(403)
        return httpx.Response(200, text=PAGE)

    fetcher = Fetcher(new_client(transport=httpx.MockTransport(handler)), delay=0)
    item, reply = add_from_issue(BODY, fetcher)

    assert item.id == "apple-airpods-pro-3"
    assert item.urls == ["https://shop.test/airpods"]
    assert "case" in item.exclude
    assert store.load_watchlist(tmp_path)[0].target_price == 160.0
    assert "Added **Apple AirPods Pro 3** with a target of £160.00" in reply
    assert "✅ Shop: £199.00" in reply
    assert "❌ Blocked: blocked by site (HTTP 403)" in reply


def test_issue_without_product_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("PRICE_CHECKER_DATA", str(tmp_path))
    item, reply = add_from_issue("### Product\n\n_No response_\n")
    assert item is None and "couldn't find" in reply


def test_remove_from_issue_by_id_or_name(tmp_path, monkeypatch):
    from price_checker.issue import remove_from_issue
    from price_checker.models import CheckRun, Item, Offer

    monkeypatch.setenv("PRICE_CHECKER_DATA", str(tmp_path))
    items = [Item(id="airpods-pro-3", name="Apple AirPods Pro 3"), Item(id="kettle", name="Kettle")]
    store.save_watchlist(items, tmp_path)
    store.save_latest(items, CheckRun("t", [Offer("kettle", "S", 30, "u")]), tmp_path)

    item, reply = remove_from_issue("### Item\n\nKettle\n")
    assert item.id == "kettle" and "Removed **Kettle**" in reply
    assert [i.id for i in store.load_watchlist(tmp_path)] == ["airpods-pro-3"]
    assert "kettle" not in store.load_latest(tmp_path)["items"]

    item, reply = remove_from_issue("### Item\n\nnot-a-thing\n")
    assert item is None and "`airpods-pro-3`" in reply
