import re

from playwright.sync_api import Page, expect


def step_title(page: Page):
    return page.locator("#step-title")


def pick_crossing(page: Page, label: str) -> None:
    page.get_by_label(label).check()
    page.get_by_role("button", name="Next").click()
    expect(step_title(page)).to_have_text("2. Passengers")


def enter_passengers(page: Page, lead: str, count: str) -> None:
    page.get_by_label("Lead passenger").fill(lead)
    page.get_by_label("Passengers", exact=True).select_option(count)
    page.get_by_role("button", name="Next").click()
    expect(step_title(page)).to_have_text("3. Review and confirm")


def test_back_keeps_entries(page: Page) -> None:
    page.goto("/")
    pick_crossing(page, "07:30 Harbor to Gull Isle")
    enter_passengers(page, "Ada", "2")

    page.go_back()
    expect(step_title(page)).to_have_text("2. Passengers")
    expect(page.get_by_label("Lead passenger")).to_have_value("Ada")
    expect(page.get_by_label("Passengers", exact=True)).to_have_value("2")

    page.go_back()
    expect(step_title(page)).to_have_text("1. Pick a crossing")
    expect(page.get_by_label("07:30 Harbor to Gull Isle")).to_be_checked()


def test_review_shows_changes(page: Page) -> None:
    page.goto("/")
    pick_crossing(page, "07:30 Harbor to Gull Isle")
    enter_passengers(page, "Ada", "2")
    expect(page.locator("#review-fare")).to_have_text("$24")

    page.go_back()
    page.go_back()
    expect(step_title(page)).to_have_text("1. Pick a crossing")
    pick_crossing(page, "18:45 Harbor to Gull Isle")
    # Filled in again rather than trusted, so this test stays about the review
    # and doesn't also lean on Back keeping the fields.
    enter_passengers(page, "Grace", "3")

    expect(page.locator("#review-crossing")).to_have_text("18:45 Harbor to Gull Isle")
    expect(page.locator("#review-lead")).to_have_text("Grace")
    expect(page.locator("#review-count")).to_have_text("3")
    expect(page.locator("#review-fare")).to_have_text("$54")


def test_confirm_twice_books_once(page: Page) -> None:
    page.goto("/")
    pick_crossing(page, "12:15 Harbor to Gull Isle")
    enter_passengers(page, "Ada", "1")
    page.get_by_role("button", name="Confirm").click()

    reference = page.locator("#reference")
    expect(reference).to_have_text(re.compile(r"Booking FB-\d+"))
    first = reference.inner_text()

    page.go_back()
    expect(step_title(page)).to_have_text("3. Review and confirm")
    page.get_by_role("button", name="Confirm").click()

    expect(reference).to_have_text(first)
    expect(page.locator("li.booking")).to_have_count(1)


def test_deep_link_starts_over(page: Page) -> None:
    for address in ("/#/review", "/#/passengers"):
        page.goto(address)
        # The address first, because the second goto only changes the hash
        # and the crossing step is still on screen from the first one.
        expect(page).to_have_url(re.compile(r"#/crossing$"))
        expect(step_title(page)).to_have_text("1. Pick a crossing")
