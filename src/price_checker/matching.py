"""Deciding whether a listing is the item we want, and reading prices out of text."""

from __future__ import annotations

import re

from price_checker.models import Item, Offer

_NOT_NEW = re.compile(
    r"\b(refurb\w*|renewed|re-?conditioned|used|pre-?owned|pre-?loved|open[- ]box|"
    r"second[- ]hand|ex[- ]display|grade [abc])\b",
    re.IGNORECASE,
)
_REFURB = re.compile(r"\b(refurb\w*|renewed|re-?conditioned)\b", re.IGNORECASE)
_PRICE = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


def parse_price(value: object) -> float | None:
    """Turn 84, "84.00", "£1,299.99" or "From £12" into a float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = _PRICE.search(value.replace(" ", " "))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def title_matches(item: Item, title: str) -> bool:
    """True when every search term appears in the title and no exclude word does.

    Terms are compared with punctuation and spaces ignored as well, so
    "WH-1000XM5" matches "WH1000XM5" and "wh 1000 xm5".
    """
    norm = f" {_normalise(title)} "
    squashed = norm.replace(" ", "")
    for term in item.search_terms():
        term_norm = _normalise(term)
        if not term_norm:
            continue
        if f" {term_norm} " not in norm and term_norm.replace(" ", "") not in squashed:
            return False
    for word in item.exclude:
        word_norm = _normalise(word)
        if word_norm and f" {word_norm} " in norm:
            return False
    return True


def condition_from_title(title: str) -> str:
    if _REFURB.search(title):
        return "refurbished"
    if _NOT_NEW.search(title):
        return "used"
    return "new"


def acceptable(item: Item, offer: Offer) -> bool:
    """Whether an offer can count as the item's best price."""
    if offer.currency != "GBP" or offer.in_stock is False:
        return False
    if item.condition == "new" and offer.condition not in ("new", "unknown"):
        return False
    floor = item.price_floor()
    return floor is None or offer.price >= floor


def best_offer(item: Item, offers: list[Offer]) -> Offer | None:
    candidates = [o for o in offers if o.item_id == item.id and acceptable(item, o)]
    return min(candidates, key=lambda o: o.price, default=None)
