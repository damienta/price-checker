from price_checker.matching import acceptable, best_offer, condition_from_title, parse_price, title_matches
from price_checker.models import Item, Offer


def test_parse_price():
    assert parse_price("£1,299.99") == 1299.99
    assert parse_price("From £12") == 12.0
    assert parse_price(84) == 84.0
    assert parse_price("FREE") is None
    assert parse_price(True) is None


def test_title_matching_ignores_punctuation():
    item = Item(id="x", name="Sony WH-1000XM5", keywords=["Sony", "WH-1000XM5"], exclude=["case"])
    assert title_matches(item, "SONY WH1000XM5 Wireless Headphones - Black")
    assert title_matches(item, "Sony wh 1000xm5 noise cancelling")
    assert not title_matches(item, "Sony WH-1000XM4 Wireless Headphones")
    assert not title_matches(item, "Hard case for Sony WH-1000XM5")


def test_keywords_default_to_name_words():
    item = Item(id="x", name="Ninja AF101 air fryer")
    assert title_matches(item, "Ninja Air Fryer AF101 3.8L")
    assert not title_matches(item, "Ninja AF300 air fryer")


def test_condition_from_title():
    assert condition_from_title("Sony XM5 - Refurbished") == "refurbished"
    assert condition_from_title("iPhone 15 Pre-owned Grade A") == "used"
    assert condition_from_title("Brand new kettle") == "new"


def test_acceptable_and_best():
    item = Item(id="x", name="Thing", target_price=100)
    offers = [
        Offer("x", "A", 90, "u"),
        Offer("x", "B", 80, "u", condition="refurbished"),
        Offer("x", "C", 70, "u", in_stock=False),
        Offer("x", "D", 10, "u"),  # under 25% of target: probably an accessory
        Offer("y", "E", 50, "u"),
    ]
    assert best_offer(item, offers).source == "A"
    item.condition = "any"
    assert best_offer(item, offers).source == "B"
    assert not acceptable(item, Offer("x", "F", 95, "u", currency="EUR"))
