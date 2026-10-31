# A candidate that passes the real app and catches nothing. It only walks
# forward, and every break in this item lives in going Back or in skipping
# ahead, so the gate has to reject it.
from playwright.sync_api import Page, expect


def test_a_booking_gets_a_reference(page: Page) -> None:
    page.goto("/")
    page.get_by_label("07:30 Harbor to Gull Isle").check()
    page.get_by_role("button", name="Next").click()
    page.get_by_label("Lead passenger").fill("Ada")
    page.get_by_role("button", name="Next").click()
    page.get_by_role("button", name="Confirm").click()

    expect(page.locator("#reference")).to_contain_text("FB-")
