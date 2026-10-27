import httpx
import pytest

from price_checker.http import USER_AGENT, Fetcher, FetchError, new_client


def fetcher_for(routes):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        status, body = routes.get(str(request.url), (404, ""))
        return httpx.Response(status, text=body)

    return Fetcher(new_client(transport=httpx.MockTransport(handler)), delay=0), seen


def test_respects_robots_and_sends_honest_agent():
    fetcher, seen = fetcher_for(
        {
            "https://shop.test/robots.txt": (200, "User-agent: *\nDisallow: /*search=\n"),
            "https://shop.test/p/1": (200, "ok"),
        }
    )
    assert fetcher.get_text("https://shop.test/p/1") == "ok"
    with pytest.raises(FetchError, match="robots.txt"):
        fetcher.get_text("https://shop.test/list?search=tv")
    assert seen[-1].headers["user-agent"] == USER_AGENT
    # robots.txt is fetched once per site
    assert [r.url.path for r in seen].count("/robots.txt") == 1


def test_missing_robots_allows_and_blocks_are_reported():
    fetcher, _ = fetcher_for({"https://shop.test/p/1": (403, "no bots")})
    with pytest.raises(FetchError, match="HTTP 403"):
        fetcher.get_text("https://shop.test/p/1")


def test_robots_server_error_stays_away():
    fetcher, _ = fetcher_for({"https://shop.test/robots.txt": (503, "")})
    with pytest.raises(FetchError, match="robots.txt"):
        fetcher.get_text("https://shop.test/p/1")
