"""The page records a reveal because the reveal is how the line arrives.

These run against the page server itself, not against an item's app. The item
is seat-desk because it's the one that exists, and nothing here depends on
what its reference says beyond reading the file.
"""

import json
import pathlib

import pytest
from playwright.sync_api import Page, expect

from orbis import page as orbis_page

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEM = "playwright/01-seat-desk"
REFERENCE = ROOT / "items" / ITEM / "reference" / "test_seat_desk.py"


@pytest.fixture
def server(tmp_path):
    log = tmp_path / "reveals.jsonl"
    with orbis_page.Server(ROOT / "items", log) as running:
        yield running


def records(log):
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines()]


def first_lines(count):
    """The first revealable lines of the reference, as (number, text)."""
    found = []
    for number, text in enumerate(REFERENCE.read_text().splitlines(), 1):
        if text.strip():
            found.append((number, text))
        if len(found) == count:
            break
    return found


def test_two_reveals_are_recorded_without_asking(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    expect(page.locator("#task")).to_contain_text("Seat desk")

    (one, one_text), (two, two_text) = first_lines(2)
    page.click(f"#line-{one} button")
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)
    page.click(f"#line-{two} button")
    expect(page.locator(f"#line-{two} code")).to_have_text(two_text)

    logged = records(server.log)
    assert [(r["item"], r["line"]) for r in logged] == [(ITEM, one), (ITEM, two)]
    assert all(r["at"] for r in logged)


def test_a_hidden_line_is_not_in_the_page(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    (_, _), (_, two_text) = first_lines(2)
    assert two_text.strip() not in page.content()
    expect(page.locator(".line.hidden").first).to_be_visible()


def test_a_reveal_survives_a_reload(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    (one, one_text), (two, _) = first_lines(2)
    page.click(f"#line-{one} button")
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)

    page.reload()
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)
    expect(page.locator(f"#line-{two}")).to_have_class("line hidden")
    assert len(records(server.log)) == 1


def test_margin_names_the_test_without_giving_the_answer(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    expect(page.locator(".margin", has_text="a test: reserve succeeds")).to_have_count(1)


def test_the_index_lists_the_item(page: Page, server) -> None:
    page.goto(server.base_url + "/")
    page.click(f"a[href='/item/{ITEM}']")
    expect(page.locator("#task")).to_contain_text("Seat desk")


def test_a_lesson_comes_before_its_task(page: Page, server) -> None:
    page.goto(server.base_url + "/item/playwright/02-label-form")
    expect(page.locator("#lesson h1")).to_be_visible()
    lesson_top = page.locator("#lesson").bounding_box()["y"]
    task_top = page.locator("#task").bounding_box()["y"]
    assert lesson_top < task_top


def test_an_item_without_a_lesson_has_no_lesson_section(page: Page, server) -> None:
    page.goto(server.base_url + "/item/playwright/04-ferry-booking")
    expect(page.locator("#lesson")).to_have_count(0)


def test_the_course_starts_with_lesson_one(page: Page, server) -> None:
    page.goto(server.base_url + "/")
    first = page.locator("#course li").first
    expect(first).to_contain_text("A first Playwright test")
    expect(first.locator("a")).to_have_attribute("href", "/item/" + ITEM)
    expect(page.locator("#waiting a[href='/item/playwright/04-ferry-booking']")).to_have_count(1)


def test_the_lesson_holds_the_only_h1(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    expect(page.locator("h1")).to_have_count(1)
    expect(page.locator("#lesson h1")).to_have_text(
        "A first Playwright test, and what makes it worth anything"
    )


def test_the_real_app_is_one_click_away(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    address = page.locator("#app a").first.get_attribute("href")
    expect(page.locator("#app")).to_contain_text("codegen --target python-pytest " + address)

    page.goto(address)
    expect(page.locator("#heading")).to_have_text("Dockside Seat Desk")
    expect(page.locator("#seat option")).to_have_count(4)
