import json
from datetime import datetime, timezone

import httpx

from price_checker import discord
from price_checker.digest import build_digest
from price_checker.findings import Finding, load_findings
from price_checker.models import Item

NOW = datetime(2026, 10, 26, 8, 0, tzinfo=timezone.utc)


def offer(item_id, source, price, **kw):
    return {"item_id": item_id, "source": source, "price": price, "url": f"https://{source.lower()}.test/p", **kw}


def entry(best, previous=None, offers=None, errors=None, previous_checked_at=None):
    return {
        "checked_at": NOW.isoformat(),
        "best": best,
        "previous_best": previous,
        "previous_checked_at": previous_checked_at,
        "offers": offers if offers is not None else ([best] if best else []),
        "errors": errors or [],
    }


def test_sections():
    items = [
        Item(id="xm5", name="Sony WH-1000XM5", target_price=250),
        Item(id="fryer", name="Air fryer", target_price=60),
        Item(id="kettle", name="Kettle"),
        Item(id="mower", name="Mower"),
        Item(id="tv", name="TV"),
    ]
    xm5_best = offer("xm5", "Currys", 229.0)
    latest = {
        "items": {
            "xm5": entry(xm5_best, offer("xm5", "Currys", 269.0),
                         offers=[xm5_best, offer("xm5", "PriceSpy", 230.0, seller="cheapest of 9 shops")]),
            "fryer": entry(offer("fryer", "AO", 79.0), offer("fryer", "AO", 89.0)),
            "kettle": entry(offer("kettle", "Argos", 30.0), offer("kettle", "Argos", 30.0)),
            "mower": entry(offer("mower", "PriceRunner", 84.0, seller="OnBuy")),
            "tv": entry(None, errors=[{"item_id": "tv", "source": "John Lewis", "reason": "blocked by site (HTTP 403)",
                                       "url": "https://jl.test/tv"}]),
        }
    }
    findings = [
        Finding("fryer", "cheaper", 55.0, "Amazon", "https://amazon.test/f", "Prime only"),
        Finding("xm5", "confirmed", 229.0, "Currys"),
        Finding("", "note", note="Currys Black Friday starts Thursday"),
    ]
    text = build_digest(items, latest, [], findings, NOW)

    below = text.split("**🔥 Below target**")[1].split("\n\n")[0]
    assert "Sony WH-1000XM5" in below and "£229.00" in below and "↓£40.00" in below
    assert "✅ 3 sources agree" in below  # Currys, PriceSpy, Claude
    assert "[Currys](<https://currys.test/p>)" in below
    dropped = text.split("**📉 Cheaper than last check**")[1].split("\n\n")[0]
    assert "Air fryer" in dropped and "↓£10.00" in dropped
    assert "**Air fryer**: £55.00 at [Amazon](<https://amazon.test/f>) · Prime only" in text
    assert "💡 Currys Black Friday starts Thursday" in text
    assert "**Mower**: **£84.00** at [OnBuy (via PriceRunner)]" in text.split("**👀 Now tracking**")[1]
    assert "**Kettle**: **£30.00**" in text.split("**➖ No change**")[1]
    assert "TV: [John Lewis](<https://jl.test/tv>): blocked by site (HTTP 403)" in text
    assert text.startswith("## ☀️ Price check · Mon 26 Oct")


def test_deals_only_announced_once():
    item = Item(id="x", name="Thing")
    deal_old = offer("x", "HotUKDeals", 50.0, kind="deal", posted_at="2026-10-25T06:00:00+00:00", title="Old deal")
    deal_new = offer("x", "HotUKDeals", 45.0, kind="deal", posted_at="2026-10-25T20:00:00+00:00", title="New deal",
                     seller="Argos")
    latest = {"items": {"x": entry(deal_new, offers=[deal_old, deal_new], previous_checked_at="2026-10-25T07:00:00+00:00")}}
    text = build_digest([item], latest, [], [], NOW)
    deals = text.split("**🆕 New deals posted**")[1].split("\n\n")[0]
    assert "New deal" in deals and "at Argos" in deals
    assert "Old deal" not in deals


def test_lowest_in_30_days_uses_earlier_checks_only():
    item = Item(id="x", name="Thing")
    history = [
        {"checked_at": "2026-10-20T07:00:00+00:00", "item_id": "x", "source": "S", "price": "60", "url": "u",
         "currency": "GBP", "condition": "new", "in_stock": "", "kind": "price"},
        {"checked_at": NOW.isoformat(), "item_id": "x", "source": "S", "price": "50", "url": "u",
         "currency": "GBP", "condition": "new", "in_stock": "", "kind": "price"},
    ]
    latest = {"items": {"x": entry(offer("x", "S", 50.0), offer("x", "S", 60.0))}}
    assert "lowest in 30 days" in build_digest([item], latest, history, [], NOW)


def test_empty_watchlist():
    assert "watchlist is empty" in build_digest([], {"items": {}}, [], [], NOW)


def test_findings_must_be_recent(tmp_path):
    main = tmp_path / "main.json"
    branch = tmp_path / "branch.json"
    main.write_text(json.dumps({"generated_at": "2026-10-24T07:00:00+00:00", "findings": [{"item_id": "a", "kind": "note", "note": "old"}]}))
    assert load_findings([main], NOW) == []
    branch.write_text(json.dumps({"generated_at": "2026-10-26T07:10:00+00:00", "findings": [
        {"item_id": "a", "kind": "cheaper", "price": "£10", "seller": "X"}, {"kind": "nonsense"}]}))
    [finding] = load_findings([main, branch, tmp_path / "missing.json"], NOW)
    assert (finding.kind, finding.price) == ("cheaper", 10.0)


def test_split_message():
    text = "\n".join(f"line {i} " + "x" * 50 for i in range(100))
    chunks = discord.split_message(text, limit=500)
    assert all(len(c) <= 500 for c in chunks)
    assert "\n".join(chunks) == text


def test_post_retries_rate_limit():
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(429, json={"retry_after": 0})
        return httpx.Response(204)

    discord.post("https://discord.test/hook", "hello", httpx.Client(transport=httpx.MockTransport(handler)))
    assert len(calls) == 2
    assert calls[-1]["content"] == "hello"
    assert calls[-1]["allowed_mentions"] == {"parse": []}
