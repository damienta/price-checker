"""Turn the latest check into the morning Discord message."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from price_checker.findings import Finding
from price_checker.matching import acceptable
from price_checker.models import CheckError, Item, Offer
from price_checker.store import lowest_since

UK = ZoneInfo("Europe/London")
# Prices this close to the best count as another source agreeing with it.
AGREE_WITHIN = 0.02


def money(value: float) -> str:
    return f"£{value:,.2f}"


def link(label: str, url: str) -> str:
    # <url> stops Discord from unfurling a preview for every link.
    return f"[{label}](<{url}>)" if url else label


@dataclass
class Sections:
    below_target: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    deals: list[str] = field(default_factory=list)
    claude: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def build_digest(
    items: list[Item],
    latest: dict[str, Any],
    history: list[dict[str, str]],
    findings: list[Finding],
    now: datetime,
) -> str:
    today = now.astimezone(UK)
    header = f"## ☀️ Price check · {today.strftime('%a')} {today.day} {today.strftime('%b')}"
    if not items:
        return f"{header}\nYour watchlist is empty. Ask Claude to track something to get started."

    s = Sections()
    entries = latest.get("items", {})
    for item in items:
        entry = entries.get(item.id)
        item_findings = [f for f in findings if f.item_id == item.id]
        if not entry:
            s.new.append(f"**{item.name}**: not checked yet")
        else:
            _place_item(s, item, entry, history, item_findings, now)
        for finding in item_findings:
            _place_finding(s, item, finding, entry)
    for finding in findings:
        if finding.kind == "note" and not finding.item_id:
            s.claude.append(f"💡 {finding.note}")

    parts = [header]
    for title, lines in (
        ("🔥 Below target", s.below_target),
        ("📉 Cheaper than last check", s.dropped),
        ("🆕 New deals posted", s.deals),
        ("🔍 Claude", s.claude),
        ("👀 Now tracking", s.new),
        ("➖ No change", s.unchanged),
        ("⚠️ Couldn't check", s.problems),
    ):
        if lines:
            parts.append(f"**{title}**\n" + "\n".join(lines))
    if len(parts) == 1:
        parts.append("Nothing to report.")
    return "\n\n".join(parts)


def _place_item(
    s: Sections,
    item: Item,
    entry: dict[str, Any],
    history: list[dict[str, str]],
    findings: list[Finding],
    now: datetime,
) -> None:
    best = Offer.from_dict(entry["best"]) if entry.get("best") else None
    previous = Offer.from_dict(entry["previous_best"]) if entry.get("previous_best") else None
    offers = [Offer.from_dict(o) for o in entry.get("offers", [])]
    errors = [CheckError.from_dict(e) for e in entry.get("errors", [])]

    for error in errors:
        target = link(error.source, error.url)
        s.problems.append(f"{item.name}: {target}: {error.reason}")

    _place_deals(s, item, offers, entry)

    if best is None:
        if not errors:
            s.problems.append(f"{item.name}: no prices found anywhere")
        return

    line = f"**{item.name}**: **{money(best.price)}** at {link(best.where(), best.url)}"
    notes = []
    if item.target_price:
        notes.append(f"target {money(item.target_price)}")
    if previous and abs(best.price - previous.price) >= 0.01:
        arrow = "↓" if best.price < previous.price else "↑"
        notes.append(f"{arrow}{money(abs(best.price - previous.price))}")
    agreeing = {
        o.source for o in offers if acceptable(item, o) and o.price <= best.price * (1 + AGREE_WITHIN)
    }
    if any(f.kind == "confirmed" for f in findings):
        agreeing.add("Claude")
    if len(agreeing) > 1:
        notes.append(f"✅ {len(agreeing)} sources agree")
    earlier = [r for r in history if r.get("checked_at") != entry.get("checked_at")]
    low = lowest_since(earlier, item, 30, now)
    if low is not None and best.price < low:
        notes.append("lowest in 30 days")
    if notes:
        line += " · " + " · ".join(notes)

    if item.target_price and best.price <= item.target_price:
        s.below_target.append(line)
    elif previous is None:
        s.new.append(line)
    elif best.price < previous.price - 0.005:
        s.dropped.append(line)
    else:
        s.unchanged.append(line)


def _place_deals(s: Sections, item: Item, offers: list[Offer], entry: dict[str, Any]) -> None:
    """Deal posts newer than the previous check, so each one is only announced once."""
    since = entry.get("previous_checked_at")
    for offer in offers:
        if offer.kind != "deal":
            continue
        if since and offer.posted_at and offer.posted_at <= since:
            continue
        where = f" at {offer.seller}" if offer.seller else ""
        s.deals.append(f"{item.name}: {money(offer.price)}{where} · {link(offer.title[:90], offer.url)}")


def _place_finding(s: Sections, item: Item, finding: Finding, entry: dict[str, Any] | None) -> None:
    best_price = ((entry or {}).get("best") or {}).get("price")
    where = link(finding.seller or "link", finding.url)
    note = f" · {finding.note}" if finding.note else ""
    if finding.kind == "cheaper" and finding.price is not None:
        if best_price is not None and finding.price >= best_price:
            return
        s.claude.append(f"**{item.name}**: {money(finding.price)} at {where}{note}")
    elif finding.kind == "mismatch":
        s.problems.append(f"{item.name}: Claude says {finding.note or 'price looks wrong'}")
    elif finding.kind == "note" and finding.note:
        s.claude.append(f"{item.name}: {finding.note}")
