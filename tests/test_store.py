from datetime import datetime, timezone

from price_checker import store
from price_checker.models import CheckError, CheckRun, Item, Offer


def test_upsert_merges_links(tmp_path):
    items, created = store.upsert_item([], Item(id="a", name="A", urls=["u1"]))
    assert created
    items, created = store.upsert_item(items, Item(id="a", name="A", urls=["u1", "u2"], target_price=50))
    assert not created
    assert items[0].urls == ["u1", "u2"]
    assert items[0].target_price == 50

    store.save_watchlist(items, tmp_path)
    assert store.load_watchlist(tmp_path) == items


def test_latest_keeps_previous_best(tmp_path):
    item = Item(id="a", name="A")
    first = CheckRun("2026-10-25T07:00:00+00:00", [Offer("a", "S", 100, "u")])
    store.save_latest([item], first, tmp_path)

    second = CheckRun("2026-10-26T07:00:00+00:00", [Offer("a", "S", 90, "u"), Offer("a", "T", 95, "v")])
    latest = store.save_latest([item], second, tmp_path)
    entry = latest["items"]["a"]
    assert entry["best"]["price"] == 90
    assert entry["previous_best"]["price"] == 100
    assert [o["price"] for o in entry["offers"]] == [90, 95]

    # A run where every source failed keeps the last known best as "previous".
    third = CheckRun("2026-10-27T07:00:00+00:00", [], [CheckError("a", "S", "blocked")])
    entry = store.save_latest([item], third, tmp_path)["items"]["a"]
    assert entry["best"] is None
    assert entry["previous_best"]["price"] == 90
    assert entry["errors"][0]["reason"] == "blocked"


def test_partial_check_leaves_other_items(tmp_path):
    a, b = Item(id="a", name="A"), Item(id="b", name="B")
    store.save_latest([a, b], CheckRun("t1", [Offer("a", "S", 1, "u"), Offer("b", "S", 2, "u")]), tmp_path)
    latest = store.save_latest([a], CheckRun("t2", [Offer("a", "S", 3, "u")]), tmp_path)
    assert latest["items"]["b"]["best"]["price"] == 2
    assert latest["items"]["a"]["best"]["price"] == 3


def test_history_and_lowest_since(tmp_path):
    item = Item(id="a", name="A")
    store.append_history(CheckRun("2026-09-01T07:00:00+00:00", [Offer("a", "S", 50, "u")]), tmp_path)
    store.append_history(
        CheckRun("2026-10-20T07:00:00+00:00", [Offer("a", "S", 80, "u"), Offer("a", "S", 60, "u", in_stock=False)]),
        tmp_path,
    )
    history = store.load_history(tmp_path)
    now = datetime(2026, 10, 26, tzinfo=timezone.utc)
    assert len(history) == 3
    assert store.lowest_since(history, item, 30, now) == 80
    assert store.lowest_since(history, item, 90, now) == 50
