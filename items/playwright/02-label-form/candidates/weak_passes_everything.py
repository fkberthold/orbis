# A candidate that passes the real app and catches nothing. The gate has to
# reject it, and watching that happen is how we know the gate measures.
#
# This one is the timing trap the task warns about. It checks that nothing was
# printed right after the click, before the desk has answered, so it passes
# against a desk that goes on to print a refused label.
from playwright.sync_api import Page, expect


def test_a_blank_label_prints_nothing(page: Page) -> None:
    page.goto("/")
    page.click("#print")
    expect(page.locator("li.label")).to_have_count(0)
