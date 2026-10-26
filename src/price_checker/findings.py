"""What the Claude routine found, read from data/claude_findings.json.

The routine runs before the morning check, searches the web for each item (including
Amazon and Argos, which block scripts) and writes:

    {
      "generated_at": "2026-10-26T07:20:00+00:00",
      "findings": [
        {"item_id": "sony-wh-1000xm5", "kind": "cheaper", "price": 219.0,
         "seller": "Amazon", "url": "https://...", "note": "Prime only"},
        {"item_id": "sony-wh-1000xm5", "kind": "confirmed", "price": 229.0, "seller": "Currys"},
        {"item_id": "air-fryer", "kind": "mismatch", "note": "AO page now shows £99, not £79"},
        {"item_id": "", "kind": "note", "note": "Currys Black Friday sale starts Thursday"}
      ]
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from price_checker.matching import parse_price

KINDS = ("cheaper", "confirmed", "mismatch", "note")


@dataclass
class Finding:
    item_id: str
    kind: str
    price: float | None = None
    seller: str = ""
    url: str = ""
    note: str = ""


def load_findings(paths: list[Path], now: datetime, max_age_hours: int = 24) -> list[Finding]:
    """Findings from the newest of `paths`, if it was written in the last day.

    Several paths because the routine may push to a `claude/findings` branch
    instead of main; the workflow copies that branch's file next to main's.
    """
    newest: tuple[datetime, list] | None = None
    for path in paths:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            generated = datetime.fromisoformat(data["generated_at"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if generated.tzinfo is None:
            continue
        if newest is None or generated > newest[0]:
            newest = (generated, data.get("findings") or [])
    if newest is None or now - newest[0] > timedelta(hours=max_age_hours):
        return []
    findings = []
    for raw in newest[1]:
        if not isinstance(raw, dict) or raw.get("kind") not in KINDS:
            continue
        findings.append(
            Finding(
                item_id=str(raw.get("item_id") or ""),
                kind=raw["kind"],
                price=parse_price(raw.get("price")),
                seller=str(raw.get("seller") or ""),
                url=str(raw.get("url") or ""),
                note=str(raw.get("note") or ""),
            )
        )
    return findings
