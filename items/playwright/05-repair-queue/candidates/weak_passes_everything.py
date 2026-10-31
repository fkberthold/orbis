# A candidate that passes the real app and catches nothing. It checks that five
# rows are there, which every broken copy also gets right. The gate has to
# reject it, and watching that happen is how we know the gate measures.
from playwright.sync_api import Page, expect


def test_the_queue_loads(page: Page) -> None:
    page.goto("/")
    expect(page.locator("li.job")).to_have_count(5)
