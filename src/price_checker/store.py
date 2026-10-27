"""Everything lives in plain files under data/ so it can be committed by GitHub Actions
and read later by a frontend without a database.

- watchlist.json  what to track (edited by you or Claude)
- latest.json     the most recent check: best price per item plus the previous best
- history.csv     one row per offer per check, for "lowest in 30 days" and charts
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from price_checker.matching import acceptable, best_offer
from price_checker.models import CheckRun, Item, Offer

HISTORY_FIELDS = [
    "checked_at",
    "item_id",
    "source",
    "seller",
    "price",
    "currency",
    "condition",
    "in_stock",
    "kind",
    "url",
    "title",
]


def data_dir() -> Path:
    return Path(os.environ.get("PRICE_CHECKER_DATA", "data"))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --- watchlist ---------------------------------------------------------------


def load_watchlist(base: Path | None = None) -> list[Item]:
    raw = _read_json((base or data_dir()) / "watchlist.json", {"items": []})
    return [Item.from_dict(entry) for entry in raw.get("items", [])]


def save_watchlist(items: list[Item], base: Path | None = None) -> None:
    _write_json((base or data_dir()) / "watchlist.json", {"items": [i.to_dict() for i in items]})


def upsert_item(items: list[Item], new: Item) -> tuple[list[Item], bool]:
    """Add `new`, or merge its links and tags into an existing item with the same id.

    Returns the updated list and whether the item was newly created.
    """
    for existing in items:
        if existing.id != new.id:
            continue
        for attr in ("urls", "hotukdeals_tags", "keywords", "exclude"):
            merged = getattr(existing, attr)
            merged.extend(v for v in getattr(new, attr) if v not in merged)
        for attr in ("target_price", "min_price"):
            if getattr(new, attr) is not None:
                setattr(existing, attr, getattr(new, attr))
        if new.notes:
            existing.notes = new.notes
        return items, False
    return [*items, new], True


# --- latest.json -------------------------------------------------------------


def load_latest(base: Path | None = None) -> dict[str, Any]:
    return _read_json((base or data_dir()) / "latest.json", {"checked_at": None, "items": {}})


def save_latest(items: list[Item], run: CheckRun, base: Path | None = None) -> dict[str, Any]:
    """Record this run as the latest, keeping each item's previous best for comparison.

    Items not covered by the run (e.g. `check --item x`) are left as they were.
    """
    base = base or data_dir()
    latest = load_latest(base)
    checked_ids = {i.id for i in items}
    entries: dict[str, Any] = {
        k: v for k, v in latest.get("items", {}).items() if k not in checked_ids
    }
    for item in items:
        old = latest.get("items", {}).get(item.id, {})
        offers = [o for o in run.offers if o.item_id == item.id]
        best = best_offer(item, offers)
        entries[item.id] = {
            "name": item.name,
            "target_price": item.target_price,
            "checked_at": run.checked_at,
            "best": best.to_dict() if best else None,
            "previous_best": old.get("best") or old.get("previous_best"),
            "previous_checked_at": old.get("checked_at"),
            "offers": [o.to_dict() for o in sorted(offers, key=lambda o: o.price)],
            "errors": [e.to_dict() for e in run.errors if e.item_id == item.id],
        }
    latest = {"checked_at": run.checked_at, "items": entries}
    _write_json(base / "latest.json", latest)
    return latest


# --- history.csv -------------------------------------------------------------


def append_history(run: CheckRun, base: Path | None = None) -> None:
    path = (base or data_dir()) / "history.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        for offer in run.offers:
            row = offer.to_dict()
            row["checked_at"] = run.checked_at
            row["in_stock"] = "" if offer.in_stock is None else str(offer.in_stock).lower()
            writer.writerow(row)


def load_history(base: Path | None = None) -> list[dict[str, str]]:
    path = (base or data_dir()) / "history.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def lowest_since(
    history: list[dict[str, str]], item: Item, days: int, now: datetime
) -> float | None:
    """Lowest acceptable price recorded for the item in the last `days` days."""
    cutoff = now - timedelta(days=days)
    prices = []
    for row in history:
        if row.get("item_id") != item.id:
            continue
        try:
            when = datetime.fromisoformat(row["checked_at"])
            offer = Offer.from_dict(
                {
                    **row,
                    "price": float(row["price"]),
                    "in_stock": {"true": True, "false": False}.get(row.get("in_stock", "")),
                }
            )
        except (KeyError, ValueError):
            continue
        if when >= cutoff and acceptable(item, offer):
            prices.append(offer.price)
    return min(prices, default=None)
