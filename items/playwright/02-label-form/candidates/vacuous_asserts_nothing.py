# A candidate that asserts nothing at all. It should land in the vacuous cell
# rather than the silent one, which is the whole reason two cells are not
# enough. It even presses the button, so doing things isn't mistaken for
# checking them.
from playwright.sync_api import Page


def test_the_desk_answers(page: Page) -> None:
    page.goto("/")
    page.fill("#recipient", "Ada Lovelace")
    page.fill("#postcode", "02139")
    page.fill("#weight", "2.5")
    page.click("#print")
