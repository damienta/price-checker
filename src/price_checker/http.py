"""A polite HTTP client: honest user agent, robots.txt respected, gaps between hits."""

from __future__ import annotations

import time
from urllib.parse import urlsplit

import httpx

from price_checker.robots import Robots

# The token sites can name in robots.txt to opt out of this tool.
AGENT_TOKEN = "price-checker"
USER_AGENT = f"Mozilla/5.0 (compatible; {AGENT_TOKEN}/0.1; +https://github.com/damienta/price-checker)"

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


class FetchError(Exception):
    """The page could not be read. The message is shown in the digest."""


def new_client(timeout: float = 20.0, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout, transport=transport
    )


class Fetcher:
    def __init__(self, client: httpx.Client | None = None, delay: float = 2.0) -> None:
        self.client = client or new_client()
        self.delay = delay
        self._robots: dict[str, Robots | None] = {}
        self._last_hit: dict[str, float] = {}

    def get_text(self, url: str) -> str:
        parts = urlsplit(url)
        if not self.allowed(url):
            raise FetchError("robots.txt asks bots not to read this page")
        self._wait(parts.netloc)
        try:
            response = self.client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(f"network error ({type(exc).__name__})") from exc
        if response.status_code in (401, 403, 429, 503):
            raise FetchError(f"blocked by site (HTTP {response.status_code})")
        if response.status_code >= 400:
            raise FetchError(f"HTTP {response.status_code}")
        return response.text

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            self._robots[origin] = self._load_robots(origin)
        robots = self._robots[origin]
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        return robots is None or robots.can_fetch(AGENT_TOKEN, path)

    def _load_robots(self, origin: str) -> Robots | None:
        try:
            response = self.client.get(f"{origin}/robots.txt")
        except httpx.HTTPError as exc:
            raise FetchError(f"couldn't read robots.txt ({type(exc).__name__})") from exc
        # Same convention as Google: a missing robots.txt allows everything,
        # a server error means stay away for now.
        if response.status_code >= 500:
            raise FetchError(f"couldn't read robots.txt (HTTP {response.status_code})")
        if response.status_code >= 400:
            return None
        return Robots(response.text)

    def _wait(self, host: str) -> None:
        last = self._last_hit.get(host)
        if last is not None:
            gap = time.monotonic() - last
            if gap < self.delay:
                time.sleep(self.delay - gap)
        self._last_hit[host] = time.monotonic()
