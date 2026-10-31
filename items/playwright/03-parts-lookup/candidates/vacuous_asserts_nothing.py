# A candidate that asserts nothing at all. It should land in the vacuous cell
# rather than the silent one, which is the whole reason two cells are not
# enough.
from playwright.sync_api import Page


def test_the_lookup_answers(page: Page) -> None:
    page.goto("/")
