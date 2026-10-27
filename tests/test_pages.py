import json

from price_checker.sources.pages import extract_offers, site_name


def page(*blocks, extra=""):
    scripts = "".join(
        f'<script type="application/ld+json">{json.dumps(b)}</script>' for b in blocks
    )
    return f"<html><head>{scripts}{extra}</head><body></body></html>"


def test_pricerunner_style_single_offer():
    url = "https://www.pricerunner.com/pl/119-1/Lawn-Mowers/Einhell"
    html = page(
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Einhell GC-HM 300",
            "offers": {
                "@type": "Offer",
                "price": "84.00",
                "priceCurrency": "GBP",
                "availability": "https://schema.org/InStock",
                "seller": {"@type": "Organization", "name": "OnBuy"},
                "url": url,
            },
        },
        {"@type": "BreadcrumbList", "itemListElement": []},
    )
    [offer] = extract_offers(html, url, "mower")
    assert offer.price == 84.0
    assert offer.source == "PriceRunner"
    assert offer.seller == "OnBuy"
    assert offer.in_stock is True
    assert offer.item_id == "mower"
    assert offer.where() == "OnBuy (via PriceRunner)"


def test_pricespy_style_product_group_with_variants():
    group = {
        "@type": "ProductGroup",
        "name": "Sony WF-1000XM5",
        "hasVariant": [
            {
                "@type": "Product",
                "name": "Sony WF-1000XM5 - Black",
                "url": "https://pricespy.co.uk/product.php?p=1&a-1=Black",
                "offers": {"@type": "AggregateOffer", "lowPrice": 139.98, "highPrice": 399, "offerCount": 11, "priceCurrency": "GBP"},
            },
            {
                "@type": "Product",
                "name": "Sony WF-1000XM5 - Silver",
                "url": "https://pricespy.co.uk/product.php?p=1&a-1=Silver",
                "offers": {"@type": "AggregateOffer", "lowPrice": 120.99, "offerCount": 4, "priceCurrency": "GBP"},
            },
        ],
    }
    offers = extract_offers(page(group), "https://pricespy.co.uk/product.php?p=1", "x")
    assert sorted(o.price for o in offers) == [120.99, 139.98]
    assert {o.seller for o in offers} == {"cheapest of 11 shops", "cheapest of 4 shops"}

    # A link to one colour only reports that colour.
    [black] = extract_offers(page(group), "https://pricespy.co.uk/product.php?p=1&a-1=Black", "x")
    assert black.price == 139.98


def test_graph_and_price_specification():
    html = page(
        {
            "@graph": [
                {"@type": "WebPage", "name": "x"},
                {
                    "@type": ["Product", "Thing"],
                    "name": "Kettle",
                    "offers": [
                        {"@type": "Offer", "priceSpecification": {"price": "£1,299.50", "priceCurrency": "GBP"},
                         "availability": "http://schema.org/OutOfStock"},
                    ],
                },
            ]
        }
    )
    [offer] = extract_offers(html, "https://www.currys.co.uk/products/kettle", "k")
    assert offer.price == 1299.5
    assert offer.in_stock is False
    assert offer.source == "Currys"


def test_aggregate_offer_with_listed_shops_expands():
    html = page(
        {
            "@type": "Product",
            "name": "Thing",
            "offers": {
                "@type": "AggregateOffer",
                "lowPrice": 10,
                "offers": [
                    {"@type": "Offer", "price": 10, "priceCurrency": "GBP", "seller": {"name": "Argos"}},
                    {"@type": "Offer", "price": 12, "priceCurrency": "GBP", "seller": "AO"},
                ],
            },
        }
    )
    offers = extract_offers(html, "https://example.co.uk/p", "t")
    assert [(o.seller, o.price) for o in offers] == [("Argos", 10.0), ("AO", 12.0)]


def test_related_products_and_other_currencies_are_ignored():
    html = page(
        {
            "@type": "Product",
            "name": "Main",
            "offers": {"@type": "Offer", "price": 50, "priceCurrency": "GBP",
                       "itemCondition": "https://schema.org/RefurbishedCondition"},
            "isSimilarTo": {"@type": "Product", "name": "Cheap", "offers": {"price": 1, "priceCurrency": "GBP"}},
        },
        {"@type": "Product", "name": "Euro", "offers": {"price": 40, "priceCurrency": "EUR"}},
    )
    offers = extract_offers(html, "https://example.co.uk/p")
    assert [(o.title, o.price, o.condition) for o in offers] == [("Main", 50.0, "refurbished")]


def test_meta_tag_fallback():
    html = page(
        extra='<meta property="product:price:amount" content="19.99">'
        '<meta property="product:price:currency" content="GBP">'
        '<meta property="og:title" content="Mug &amp; Saucer">'
    )
    [offer] = extract_offers(html, "https://shop.example/mug")
    assert (offer.price, offer.title) == (19.99, "Mug & Saucer")


def test_broken_json_is_skipped():
    html = '<script type="application/ld+json">{not json</script>'
    assert extract_offers(html, "https://example.co.uk/p") == []


def test_site_names():
    assert site_name("https://www.johnlewis.com/x") == "John Lewis"
    assert site_name("https://uk.example-shop.com/x") == "Uk"
    assert site_name("https://www.richersounds.com/a") == "Richer Sounds"
