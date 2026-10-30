# A candidate that passes the real app and catches nothing. The gate has to
# reject it, and watching that happen is how we know the gate measures.
from playwright.sync_api import Page, expect


def test_the_desk_loads(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#heading")).to_have_text("Dockside Seat Desk")
