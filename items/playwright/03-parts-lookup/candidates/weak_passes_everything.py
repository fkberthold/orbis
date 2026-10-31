# A candidate that passes the real app and catches nothing. The gate has to
# reject it, and watching that happen is how we know the gate measures.
#
# It checks the heading, which no break touches. A pass-or-fail grader would
# call this test correct.
from playwright.sync_api import Page, expect


def test_the_lookup_loads(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#heading")).to_have_text("Northgate Parts Lookup")
