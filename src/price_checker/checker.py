"""Run every source against every item."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from price_checker.models import CheckError, CheckRun, Item
from price_checker.sources import Source


def run_check(
    items: list[Item],
    sources: list[Source],
    now: datetime | None = None,
    on_item: Callable[[Item], None] | None = None,
) -> CheckRun:
    now = now or datetime.now(timezone.utc)
    run = CheckRun(checked_at=now.isoformat(timespec="seconds"))
    for item in items:
        if on_item:
            on_item(item)
        for source in sources:
            try:
                offers, errors = source.check(item)
            except Exception as exc:  # one broken source must not stop the morning check
                run.errors.append(CheckError(item.id, source.name, f"source crashed: {exc!r}"))
                continue
            run.offers.extend(offers)
            run.errors.extend(errors)
    return run
