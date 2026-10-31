# A candidate that asserts nothing at all. It walks the whole booking, so it
# looks busy, and it should still land in the vacuous cell rather than the
# silent one.
from playwright.sync_api import Page


def test_the_booking_goes_through(page: Page) -> None:
    page.goto("/")
    page.get_by_label("07:30 Harbor to Gull Isle").check()
    page.get_by_role("button", name="Next").click()
    page.get_by_label("Lead passenger").fill("Ada")
    page.get_by_role("button", name="Next").click()
    page.get_by_role("button", name="Confirm").click()
