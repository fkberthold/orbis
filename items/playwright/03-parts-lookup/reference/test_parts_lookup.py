from playwright.sync_api import Page, Route, expect

CATALOG = [
    "BRK-1042 Front brake pad set",
    "BRK-1077 Rear brake rotor",
    "FLT-2010 Oil filter",
    "FLT-2033 Cabin air filter",
    "BLT-3105 Serpentine belt",
    "SPK-4001 Spark plug, iridium",
    "WPR-5020 Wiper blade, 22 inch",
    "BAT-6100 Battery, group 35",
]


def open_lookup(page: Page) -> None:
    page.goto("/")
    # Waiting for the box to come on is waiting for the catalog, so every test
    # after this sees the real parts.json and not an empty list.
    expect(page.locator("#search")).to_be_enabled()


def test_loading_notice_clears(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#status")).to_have_text("Loading parts...")
    expect(page.locator("#search")).to_be_disabled()

    expect(page.locator("#status")).to_have_text("")
    expect(page.locator("#search")).to_be_enabled()


def test_lists_every_part(page: Page) -> None:
    open_lookup(page)
    expect(page.locator("li.part")).to_have_text(CATALOG)


def test_search_by_name_ignores_case(page: Page) -> None:
    open_lookup(page)
    page.fill("#search", "BRAKE")
    expect(page.locator("li.part")).to_have_text(
        ["BRK-1042 Front brake pad set", "BRK-1077 Rear brake rotor"]
    )


def test_search_by_part_number(page: Page) -> None:
    open_lookup(page)
    page.fill("#search", "FLT-20")
    expect(page.locator("li.part")).to_have_text(
        ["FLT-2010 Oil filter", "FLT-2033 Cabin air filter"]
    )


def test_search_with_no_match(page: Page) -> None:
    open_lookup(page)
    page.fill("#search", "carburetor")
    expect(page.locator("li.part")).to_have_count(0)
    expect(page.locator("#empty")).to_have_text('No parts match "carburetor".')


def test_failed_catalog_is_reported(page: Page) -> None:
    # The real file never fails, so the failure has to be made here. The body
    # is JSON on purpose, since a lot of servers send their errors that way. A
    # body that won't parse would let an app that never checks the status get
    # the right message by accident.
    def fail(route: Route) -> None:
        route.fulfill(
            status=500,
            content_type="application/json",
            body='{"error": "catalog offline"}',
        )

    page.route("**/parts.json", fail)
    page.goto("/")
    expect(page.locator("#error")).to_have_text("Couldn't load the parts catalog.")
    expect(page.locator("#status")).to_have_text("")
    expect(page.locator("li.part")).to_have_count(0)


def test_empty_catalog_is_reported(page: Page) -> None:
    def answer_empty(route: Route) -> None:
        route.fulfill(status=200, content_type="application/json", body="[]")

    page.route("**/parts.json", answer_empty)
    page.goto("/")
    expect(page.locator("#error")).to_have_text("The parts catalog is empty.")
    expect(page.locator("#status")).to_have_text("")
    expect(page.locator("li.part")).to_have_count(0)
