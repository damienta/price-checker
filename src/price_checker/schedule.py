"""When the morning digest is due.

GitHub starts scheduled workflows late, sometimes by many hours, so instead of
"run at exactly 8am" the rule is "post once per UK day, on the first run after 8am".
The date of the last post is kept in data/digest_state.json.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
DIGEST_HOUR = 8


def uk_today(now: datetime) -> date:
    return now.astimezone(UK).date()


def last_posted(path: Path) -> date | None:
    try:
        return date.fromisoformat(json.loads(path.read_text(encoding="utf-8"))["last_posted"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def record_posted(path: Path, now: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_posted": uk_today(now).isoformat()}) + "\n", encoding="utf-8")


def is_due(now: datetime, posted: date | None, hour: int = DIGEST_HOUR) -> tuple[bool, str]:
    local = now.astimezone(UK)
    if local.hour < hour:
        return False, f"it's {local:%H:%M} in the UK, before {hour}:00"
    if posted == local.date():
        return False, "today's digest has already been posted"
    return True, f"due: it's {local:%H:%M} in the UK and nothing has been posted today"
