from playwright.sync_api import Page, expect


def open_desk(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#heading")).to_have_text("Dockside Seat Desk")


def test_reserve_succeeds(page: Page) -> None:
    open_desk(page)
    page.fill("#name", "Ada")
    page.select_option("#seat", "A1")
    page.click("#reserve")

    expect(page.locator("#banner")).to_have_text("Reserved A1 for Ada.")
    expect(page.locator("li.reservation")).to_have_count(1)
    # The spinner has to come back down once the desk answers.
    expect(page.locator("#status")).to_have_text("")
    expect(page.locator("#reserve")).to_be_enabled()


def test_taken_seat_is_rejected(page: Page) -> None:
    open_desk(page)
    page.fill("#name", "Ada")
    page.select_option("#seat", "A2")
    page.click("#reserve")

    expect(page.locator("#error")).to_have_text("Seat A2 is already taken.")
    expect(page.locator("li.reservation")).to_have_count(0)


def test_reserved_seat_is_refused_next_time(page: Page) -> None:
    open_desk(page)
    page.fill("#name", "Ada")
    page.select_option("#seat", "A1")
    page.click("#reserve")
    expect(page.locator("#banner")).to_have_text("Reserved A1 for Ada.")

    # A1 was free when the page loaded, so only the first reservation can be
    # what makes it taken.
    page.fill("#name", "Bo")
    page.select_option("#seat", "A1")
    page.click("#reserve")

    expect(page.locator("#error")).to_have_text("Seat A1 is already taken.")
    expect(page.locator("li.reservation")).to_have_count(1)


def test_double_click_reserves_once(page: Page) -> None:
    open_desk(page)
    page.fill("#name", "Ada")
    page.select_option("#seat", "A1")

    # force, because the button is meant to be down for the second click.
    page.dblclick("#reserve", force=True)

    expect(page.locator("li.reservation")).to_have_count(1)
    expect(page.locator("#error")).to_have_text("")
