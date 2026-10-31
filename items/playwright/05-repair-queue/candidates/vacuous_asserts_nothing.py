# A candidate that asserts nothing at all. It clicks Finish and walks away,
# which is how a real vacuous test looks. It should land in the vacuous cell
# rather than the silent one, which is the whole reason two cells aren't
# enough.
from playwright.sync_api import Page


def test_finish_a_job(page: Page) -> None:
    page.goto("/")
    page.locator("li.job").filter(has_text="#103").get_by_role(
        "button", name="Finish"
    ).click()
