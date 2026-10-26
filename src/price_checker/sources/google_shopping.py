"""Google Shopping UK through SerpApi (free plan: 250 searches a month).

Only runs when SERPAPI_KEY is set. The free plan can't cover every item every day, so each
run spends at most budget/31 searches on the items that were searched longest ago, and the
usage is kept in data/serpapi_usage.json so the monthly budget is never exceeded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from price_checker.matching import condition_from_title, parse_price, title_matches
from price_checker.models import CheckError, Item, Offer

SEARCH_URL = "https://serpapi.com/search.json"


class GoogleShoppingSource:
    name = "Google Shopping"

    def __init__(
        self,
        client: httpx.Client,
        api_key: str,
        usage_path: Path,
        items: list[Item],
        monthly_budget: int = 240,
        now: datetime | None = None,
    ) -> None:
        self.client = client
        self.api_key = api_key
        self.usage_path = usage_path
        self.now = now or datetime.now(timezone.utc)
        self.usage = self._load_usage()
        remaining = max(monthly_budget - self.usage["used"], 0)
        per_run = max(monthly_budget // 31, 1)
        self.selected = set(self._pick(items, min(per_run, remaining)))

    def check(self, item: Item) -> tuple[list[Offer], list[CheckError]]:
        if item.id not in self.selected:
            return [], []
        try:
            response = self.client.get(
                SEARCH_URL,
                params={
                    "engine": "google_shopping",
                    "q": " ".join(item.search_terms()),
                    "gl": "uk",
                    "hl": "en",
                    "location": "United Kingdom",
                    "api_key": self.api_key,
                },
            )
            self._record(item)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # Never put the request URL in the message: it contains the API key.
            return [], [CheckError(item.id, self.name, f"API error ({type(exc).__name__})")]
        if "error" in data:
            return [], [CheckError(item.id, self.name, str(data["error"]))]
        offers = [o for r in data.get("shopping_results", []) if (o := self._to_offer(item, r))]
        return sorted(offers, key=lambda o: o.price)[:5], []

    def _pick(self, items: list[Item], count: int) -> list[str]:
        searchable = [i for i in items if i.search]
        last = self.usage["last_searched"]
        searchable.sort(key=lambda i: last.get(i.id, ""))
        return [i.id for i in searchable[:count]]

    def _load_usage(self) -> dict:
        month = self.now.strftime("%Y-%m")
        usage = {"month": month, "used": 0, "last_searched": {}}
        if self.usage_path.exists():
            saved = json.loads(self.usage_path.read_text(encoding="utf-8"))
            usage["last_searched"] = saved.get("last_searched", {})
            if saved.get("month") == month:
                usage["used"] = saved.get("used", 0)
        return usage

    def _record(self, item: Item) -> None:
        self.usage["used"] += 1
        self.usage["last_searched"][item.id] = self.now.isoformat(timespec="seconds")
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        self.usage_path.write_text(json.dumps(self.usage, indent=2) + "\n", encoding="utf-8")

    def _to_offer(self, item: Item, result: dict) -> Offer | None:
        title = result.get("title", "")
        price = result.get("extracted_price")
        if not isinstance(price, (int, float)):
            price = parse_price(result.get("price"))
        if price is None or not title_matches(item, title):
            return None
        condition = "used" if result.get("second_hand_condition") else condition_from_title(title)
        return Offer(
            item_id=item.id,
            source=self.name,
            price=float(price),
            url=result.get("product_link") or result.get("link") or "",
            seller=result.get("source", ""),
            title=title,
            condition=condition,
        )
