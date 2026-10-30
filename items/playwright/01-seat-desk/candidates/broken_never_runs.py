# A candidate that cannot be collected. It exists so the did-not-run cell is
# driven by something, rather than being a name in a table nobody has reached.
from playwright.sync_api import Page

import orbis_helpers_that_do_not_exist  # noqa: F401


def test_the_desk_loads(page: Page) -> None:
    page.goto("/")
