"""Command line entry point: `uv run price-checker <command>`."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from price_checker import store
from price_checker.checker import run_check
from price_checker.http import Fetcher, FetchError
from price_checker.models import Item
from price_checker.sources import build_sources
from price_checker.sources.pages import extract_offers


def _money(value: float | None) -> str:
    return "-" if value is None else f"£{value:,.2f}"


def cmd_add(args: argparse.Namespace) -> int:
    item = Item(
        id=args.id or store.slugify(args.name),
        name=args.name,
        target_price=args.target,
        condition="any" if args.any_condition else "new",
        keywords=args.keyword or [],
        exclude=args.exclude or [],
        min_price=args.min_price,
        urls=args.url or [],
        hotukdeals_tags=args.tag or [],
        search=not args.no_search,
        added=date.today().isoformat(),
        notes=args.notes or "",
    )
    items, created = store.upsert_item(store.load_watchlist(), item)
    store.save_watchlist(items)
    print(f"{'Added' if created else 'Updated'} {item.id}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    items = store.load_watchlist()
    kept = [i for i in items if i.id != args.id]
    if len(kept) == len(items):
        print(f"No item with id {args.id}", file=sys.stderr)
        return 1
    store.save_watchlist(kept)
    print(f"Removed {args.id}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    items = store.load_watchlist()
    latest = store.load_latest().get("items", {})
    if not items:
        print("Watchlist is empty. Add something with: price-checker add \"Product name\" --target 100")
        return 0
    for item in items:
        best = (latest.get(item.id) or {}).get("best")
        now = f"{_money(best['price'])} at {best.get('seller') or best['source']}" if best else "not checked yet"
        print(f"{item.id:32} target {_money(item.target_price):>10}   now {now}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    items = store.load_watchlist()
    if args.item:
        items = [i for i in items if i.id in args.item]
        if not items:
            print("No matching items", file=sys.stderr)
            return 1
    sources = build_sources(Fetcher())
    run = run_check(items, sources, on_item=lambda i: print(f"Checking {i.name}...", flush=True))
    if not args.dry_run:
        store.append_history(run)
        latest = store.save_latest(items, run)
    else:
        latest = None
    for item in items:
        offers = sorted((o for o in run.offers if o.item_id == item.id), key=lambda o: o.price)
        print(f"\n{item.name}")
        for offer in offers:
            flags = [] if offer.condition == "new" else [offer.condition]
            if offer.in_stock is False:
                flags.append("out of stock")
            extra = f" [{', '.join(flags)}]" if flags else ""
            print(f"  {_money(offer.price):>10}  {offer.where()}{extra}")
        for error in (e for e in run.errors if e.item_id == item.id):
            print(f"  {'!':>10}  {error.source}: {error.reason}")
        if latest:
            best = latest["items"][item.id]["best"]
            print(f"  best: {_money(best['price']) if best else 'none'}")
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    """Show what the script can read from a page, before adding it to an item."""
    try:
        page = Fetcher().get_text(args.url)
    except FetchError as exc:
        print(f"Can't read {args.url}: {exc}")
        return 1
    offers = extract_offers(page, args.url)
    if not offers:
        print("Page loaded but no GBP price was found in its structured data.")
        return 1
    for offer in sorted(offers, key=lambda o: o.price):
        stock = {True: "in stock", False: "out of stock", None: "stock unknown"}[offer.in_stock]
        print(f"{_money(offer.price):>10}  {offer.where()}  {offer.condition}, {stock}  {offer.title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="price-checker", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an item to the watchlist, or add links to an existing one")
    add.add_argument("name")
    add.add_argument("--id", help="defaults to a slug of the name")
    add.add_argument("--target", type=float, help="alert when the price is at or below this (£)")
    add.add_argument("--url", action="append", help="product page to check directly (repeatable)")
    add.add_argument("--keyword", action="append", help="word search results must contain (repeatable)")
    add.add_argument("--exclude", action="append", help="word that rules a search result out (repeatable)")
    add.add_argument("--min-price", type=float, help="ignore anything cheaper than this (£)")
    add.add_argument("--tag", action="append", help="HotUKDeals tag slug (repeatable)")
    add.add_argument("--any-condition", action="store_true", help="accept used and refurbished")
    add.add_argument("--no-search", action="store_true", help="only check the given links")
    add.add_argument("--notes")
    add.set_defaults(func=cmd_add)

    remove = sub.add_parser("remove", help="remove an item")
    remove.add_argument("id")
    remove.set_defaults(func=cmd_remove)

    sub.add_parser("list", help="show the watchlist with the latest prices").set_defaults(func=cmd_list)

    check = sub.add_parser("check", help="check prices now and record them")
    check.add_argument("--item", action="append", help="only check this item id (repeatable)")
    check.add_argument("--dry-run", action="store_true", help="don't write history or latest.json")
    check.set_defaults(func=cmd_check)

    probe = sub.add_parser("probe", help="show the prices the script can read from a URL")
    probe.add_argument("url")
    probe.set_defaults(func=cmd_probe)

    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    return args.func(args)
