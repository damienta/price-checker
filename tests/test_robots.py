from price_checker.robots import Robots

PRICERUNNER_STYLE = """
User-agent: BLEXBot
User-agent: YandexBot
Disallow: /

User-agent: *
Disallow: /*search=
Disallow: /results
Disallow: /pl/*p=*
Disallow: /public/search/pricehistory/
Sitemap: https://example.com/sitemap.xml
"""


def test_wildcard_rules_apply():
    robots = Robots(PRICERUNNER_STYLE)
    assert robots.can_fetch("price-checker", "/pl/119-123/Lawn-Mowers/Thing")
    assert not robots.can_fetch("price-checker", "/pl/119-123/Thing?p=2")
    assert not robots.can_fetch("price-checker", "/cl/1/Headphones?search=sony")
    assert not robots.can_fetch("price-checker", "/results?q=sony")


def test_named_groups_only_apply_to_that_bot():
    robots = Robots(PRICERUNNER_STYLE)
    assert not robots.can_fetch("YandexBot", "/pl/1")
    assert robots.can_fetch("price-checker", "/pl/1")


def test_longest_match_wins_and_allow_wins_ties():
    robots = Robots("User-agent: *\nDisallow: /shop\nAllow: /shop/product\nDisallow: /a\nAllow: /a\n")
    assert not robots.can_fetch("price-checker", "/shop/basket")
    assert robots.can_fetch("price-checker", "/shop/product/1")
    assert robots.can_fetch("price-checker", "/a")


def test_end_anchor():
    robots = Robots("User-agent: *\nDisallow: /*.pdf$\n")
    assert not robots.can_fetch("price-checker", "/files/manual.pdf")
    assert robots.can_fetch("price-checker", "/files/manual.pdf?download=1")


def test_empty_disallow_allows_everything():
    assert Robots("User-agent: *\nDisallow:\n").can_fetch("price-checker", "/anything")
