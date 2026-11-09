from datetime import datetime, timezone

import httpx

from price_checker.feed import DEFAULT_INTERESTS, build_feed
from price_checker.http import Fetcher, new_client
from price_checker.models import Item
from price_checker.sources.hotukdeals import parse_feed

NOW = datetime(2026, 11, 8, 20, 0, tzinfo=timezone.utc)


def rss(*items):
    body = "".join(
        f"""<item><category><![CDATA[{cat}]]></category>
        <pepper:merchant name="{shop}" price="£{price}"/>
        <media:content medium="image" url="https://images.hotukdeals.com/t/re/150x150/qt/55/{n}.jpg"/>
        <title><![CDATA[{title}]]></title>
        <link>https://www.hotukdeals.com/deals/thing-{n}</link>
        <pubDate>{posted}</pubDate></item>"""
        for n, title, cat, shop, price, posted in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss xmlns:pepper="http://www.pepper.com/rss" '
        'xmlns:media="http://search.yahoo.com/mrss/" version="2.0"><channel>' + body + "</channel></rss>"
    )


FRESH = "Sun, 08 Nov 2026 19:00:00 +0000"
OLD = "Thu, 05 Nov 2026 19:00:00 +0000"

FEEDS = {
    "/rss/hot": rss(
        (1, "250° - Ninja Air Fryer AF101", "Home & Living", "Argos", "79.00", FRESH),
        (2, "120° - Pork belly slices 800g", "Groceries", "ASDA", "5.50", FRESH),
    ),
    "/rss/new": rss(
        (3, "Apple AirPods Pro 3", "Electronics", "Amazon", "169.00", FRESH),
        (1, "Ninja Air Fryer AF101", "Home & Living", "Argos", "79.00", FRESH),
    ),
    "/rss/tag/headphones": rss(
        (3, "Apple AirPods Pro 3", "Electronics", "Amazon", "169.00", FRESH),
        (4, "Sony WH-CH520", "Electronics", "Currys", "29.00", OLD),
    ),
}


def fetcher():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=FEEDS.get(request.url.path, rss()))

    return Fetcher(new_client(transport=httpx.MockTransport(handler)), delay=0)


def test_parse_temperature_category_and_image():
    [hot, _] = parse_feed(FEEDS["/rss/hot"])
    assert hot["temperature"] == "250"
    assert hot["title"] == "Ninja Air Fryer AF101"
    assert hot["category"] == "Home & Living"
    assert hot["image"].endswith("/re/300x300/qt/55/1.jpg")


def test_watchlist_and_interests_rank_first_and_mutes_apply():
    interests = {**DEFAULT_INTERESTS, "tags": ["headphones"], "muted_categories": ["Groceries"]}
    watchlist = [Item(id="airpods-pro-3", name="Apple AirPods Pro 3", keywords=["airpods pro 3"])]
    feed = build_feed(fetcher(), interests, watchlist, now=NOW)

    ids = [d["id"] for d in feed["deals"]]
    assert ids[0] == "3"  # on the watchlist and in a followed tag
    assert "2" not in ids  # groceries muted
    top = feed["deals"][0]
    assert top["watchlist_item"] == "airpods-pro-3"
    assert "On your watchlist: Apple AirPods Pro 3" in top["reasons"]
    assert "You follow headphones" in top["reasons"]
    assert sorted(top["feeds"]) == ["new", "tag/headphones"]

    fryer = next(d for d in feed["deals"] if d["id"] == "1")
    assert fryer["temperature"] == 250  # kept from the hot feed even though "new" had none
    assert "Hot: 250°" in fryer["reasons"]

    # Older deals sink below fresh ones with the same signals.
    assert ids.index("4") > ids.index("3")
    assert feed["interests"]["tags"] == ["headphones"]
