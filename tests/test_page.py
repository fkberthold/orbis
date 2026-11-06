"""The page records a reveal because the reveal is how the line arrives.

These run against the page server itself, not against an item's app. The item
is seat-desk because it's the one that exists, and nothing here depends on
what its reference says beyond reading the file.
"""

import json
import pathlib
import re
import shutil
import urllib.request

import pytest
from playwright.sync_api import Page, expect

from orbis import page as orbis_page
from orbis import progress

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEM = "playwright/01-seat-desk"
PRACTICE = "/playwright/02-writing-tests/01-seat-desk/"
GUIDE = "/playwright/02-writing-tests/guide/"
COURSE_PAGE = "/playwright/"
REFERENCE = (
    ROOT / "subjects" / "playwright" / "items" / "01-seat-desk" / "reference" / "seat-desk.spec.ts"
)


@pytest.fixture
def server(tmp_path, build_dir):
    log = tmp_path / "reveals.jsonl"
    with orbis_page.Server(ROOT / "subjects", log, build_dir=build_dir) as running:
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


def open_practice(page, server):
    page.goto(server.base_url + PRACTICE)
    expect(page.locator("#answer .lines li").first).to_be_attached()


def test_two_reveals_are_recorded_without_asking(page: Page, server) -> None:
    open_practice(page, server)
    expect(page.locator("article")).to_contain_text("Seat desk")

    (one, one_text), (two, two_text) = first_lines(2)
    page.click(f"#line-{one} button")
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)
    page.click(f"#line-{two} button")
    expect(page.locator(f"#line-{two} code")).to_have_text(two_text)

    logged = records(server.log)
    assert [(r["item"], r["line"]) for r in logged] == [(ITEM, one), (ITEM, two)]
    assert all(r["at"] for r in logged)


def test_a_hidden_line_is_not_in_the_page(page: Page, server) -> None:
    open_practice(page, server)
    (_, _), (_, two_text) = first_lines(2)
    assert two_text.strip() not in page.content()
    expect(page.locator(".line.hidden").first).to_be_visible()

    # Nor in what the server sends the page, nor in the built site.
    with urllib.request.urlopen(server.base_url + "/api/practice/" + ITEM) as reply:
        assert two_text.strip() not in reply.read().decode()
    built = "".join(p.read_text() for p in server.site_dir.rglob("*.html"))
    assert two_text.strip() not in built


def test_a_reveal_survives_a_reload(page: Page, server) -> None:
    open_practice(page, server)
    (one, one_text), (two, _) = first_lines(2)
    page.click(f"#line-{one} button")
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)

    page.reload()
    expect(page.locator(f"#line-{one} code")).to_have_text(one_text)
    expect(page.locator(f"#line-{two}")).to_have_class("line hidden")
    assert len(records(server.log)) == 1


def test_margin_names_the_test_without_giving_the_answer(page: Page, server) -> None:
    open_practice(page, server)
    expect(page.locator(".margin", has_text="a test: reserve succeeds")).to_have_count(1)


def test_the_course_lists_the_item(page: Page, server) -> None:
    page.goto(server.base_url + COURSE_PAGE)
    page.locator(".orbis-course a[href*='01-seat-desk']").click()
    expect(page.locator("article h1")).to_contain_text("Seat desk")
    expect(page.locator("#app a").first).to_be_visible()


def test_the_guide_page_is_just_the_guide(page: Page, server) -> None:
    page.goto(server.base_url + GUIDE)
    expect(page.locator("article h1")).to_have_text(
        re.compile("What Playwright does that Selenium leaves to you")
    )
    for part in ("#app", "#attempt", "#answer"):
        expect(page.locator(part)).to_have_count(0)


def test_the_practice_page_points_back_at_its_guide(page: Page, server) -> None:
    open_practice(page, server)
    expect(page.locator("article .admonition a[href$='guide/']")).to_have_count(1)
    expect(page.locator("article")).not_to_contain_text("How a suite is put together")


def test_the_guide_shows_highlighted_code_with_a_copy_button(page: Page, server) -> None:
    page.goto(server.base_url + GUIDE)
    block = page.locator("article .highlight").filter(has_text="defineConfig").first
    expect(block.locator("span.kd, span.k, span.nx").first).to_be_attached()
    expect(block.locator("button[data-md-type='copy']")).to_have_count(1)


COURSE = ".orbis-course > ol > li"
LABELS = [
    "Step 0, typescript", "Step 2, writing tests", "Step 3, locators",
    "Step 4, assertions", "Step 6, navigations", "Step 12, mocking",
]


def test_the_nav_has_an_entry_per_step(page: Page, server) -> None:
    page.goto(server.base_url + COURSE_PAGE)
    nav = page.locator(".md-sidebar--primary .md-nav--primary")
    for label in LABELS:
        expect(nav.get_by_text(label, exact=True).first).to_be_attached()


def test_lesson_one_is_the_second_step(page: Page, server) -> None:
    page.goto(server.base_url + COURSE_PAGE)
    second = page.locator(COURSE).nth(1)
    expect(second).to_contain_text("What Playwright does that Selenium")
    expect(second.locator("a").first).to_have_attribute("href", re.compile("/02-writing-tests/guide/$"))


def test_the_steps_follow_subject_toml(page: Page, server) -> None:
    """The order is the curriculum's, which puts item 05 before item 02.

    A directory listing would sort them the other way, so this is the check
    that the order came from subject.toml.
    """
    page.goto(server.base_url + COURSE_PAGE)
    steps = page.locator(COURSE)
    expect(steps).to_have_count(6)
    for index, (label, practice) in enumerate(zip(LABELS, [
        None, "01-seat-desk", "05-repair-queue", "02-label-form",
        "04-ferry-booking", "03-parts-lookup",
    ])):
        expect(steps.nth(index)).to_contain_text(label)
        links = steps.nth(index).locator("a[href*='/0'], a[href*='/1']").filter(
            has_not_text=re.compile("^Step ")
        )
        if practice:
            expect(links.first).to_have_attribute("href", re.compile(practice))
        else:
            expect(links).to_have_count(0)


def test_a_step_with_no_guide_keeps_its_item_on_the_path(page: Page, server) -> None:
    page.goto(server.base_url + COURSE_PAGE)
    step = page.locator(COURSE).nth(4)
    expect(step).to_contain_text("Step 6, navigations")
    expect(step).to_contain_text("waiting for a guide")
    expect(step.locator("a[href*='04-ferry-booking']")).to_have_count(1)

    step.locator("a[href*='04-ferry-booking']").click()
    expect(page.locator("article .admonition")).to_contain_text("waiting for a guide")
    expect(page.locator("article a[href$='guide/']")).to_have_count(0)
    expect(page.locator("#app a").first).to_be_visible()


def test_a_lesson_with_no_item_is_still_a_step(page: Page, server) -> None:
    page.goto(server.base_url + COURSE_PAGE)
    first = page.locator(COURSE).first
    expect(first).to_contain_text("The TypeScript you need")
    first.locator("a").first.click()
    expect(page.locator("article h1")).to_have_text(
        re.compile("The TypeScript you need, read against Python")
    )
    expect(page.locator("#app")).to_have_count(0)


def test_the_real_app_is_one_click_away(page: Page, server) -> None:
    open_practice(page, server)
    address = page.locator("#app a").first.get_attribute("href")
    expect(page.locator("#app")).to_contain_text("codegen --target playwright-test " + address)
    expect(page.locator("#app")).to_contain_text(
        "subjects/playwright/workspace/mine/01-seat-desk.spec.ts"
    )

    page.goto(address)
    expect(page.locator("#heading")).to_have_text("Dockside Seat Desk")
    expect(page.locator("#seat option")).to_have_count(4)


def test_no_broken_copy_gets_a_url(server) -> None:
    """Only the real app of each item is served, and it's the only address sent."""
    assert all(app.root == server.items[name] / "app" for name, app in server.apps.items())
    with urllib.request.urlopen(server.base_url + "/api/practice/" + ITEM) as reply:
        text = reply.read().decode()
    assert set(re.findall(r"http://[^ \"]+", text)) == {server.apps[ITEM].base_url}


def test_the_practice_page_comes_alive_after_instant_navigation(page: Page, server) -> None:
    """navigation.instant swaps the page in place, so the live parts must follow."""
    page.goto(server.base_url + GUIDE)
    page.locator(".md-sidebar--primary a", has_text="Practice: Seat desk").first.click()
    expect(page).to_have_url(re.compile("01-seat-desk/$"))
    expect(page.locator("#app a").first).to_be_visible()
    expect(page.locator("#answer .line.hidden").first).to_be_visible()


def test_the_last_verdict_shows_with_its_trace_commands(page: Page, server) -> None:
    progress.AttemptLog(server.log.parent / "attempts.jsonl").record(
        ITEM, "subjects/playwright/workspace/mine/01-seat-desk.spec.ts", False,
        [
            {"environment": "real", "cell": "silent", "traces": ["run/x/trace.zip"]},
            {"environment": "no-lock", "cell": "silent", "traces": []},
        ],
    )
    open_practice(page, server)
    expect(page.locator("#attempt .orbis-verdict")).to_have_text("rejected")
    expect(page.locator("#attempt")).to_contain_text("npx playwright show-trace run/x/trace.zip")
    expect(page.locator("#attempt")).to_contain_text("uv run python -m orbis.gate attempt")

    page.goto(server.base_url + COURSE_PAGE)
    expect(page.locator(".orbis-status.rejected")).to_have_text("rejected")


def test_a_subject_with_only_a_curriculum_gets_a_tab(page: Page, tmp_path) -> None:
    """A course being planned has its curriculum and no subject.toml yet."""
    subjects = tmp_path / "subjects"
    shutil.copytree(
        ROOT / "subjects", subjects,
        ignore=shutil.ignore_patterns("node_modules", ".venv", "runs", ".deepeval"),
    )
    (subjects / "deepeval" / "subject.toml").unlink()
    with orbis_page.Server(subjects, tmp_path / "reveals.jsonl", build_dir=tmp_path / "site") as running:
        page.goto(running.base_url + "/")
        page.locator(".md-tabs a", has_text="DeepEval").click()
        expect(page.locator("article h1")).to_have_text(re.compile("The DeepEval curriculum"))


DEEPEVAL_PRACTICE = "/deepeval/02-deterministic-metrics/01-order-status/"


def test_the_deepeval_tab_shows_its_steps(page: Page, server) -> None:
    page.goto(server.base_url + "/")
    page.locator(".md-tabs a", has_text="DeepEval").click()
    steps = page.locator(COURSE)
    expect(steps).to_have_count(12)
    expect(steps.nth(2)).to_contain_text("Step 2, deterministic metrics")
    steps.nth(2).locator("a[href*='01-order-status']").click()
    expect(page.locator("article h1")).to_contain_text("Order status")


def test_the_deepeval_practice_says_how_to_reach_the_bot(page: Page, server) -> None:
    page.goto(server.base_url + DEEPEVAL_PRACTICE)
    app = page.locator("#app")
    expect(app).to_contain_text("The real bot's source is at")
    expect(app).to_contain_text(
        "PYTHONPATH=../items/01-order-status/app uv run deepeval test run"
        " mine/test_01_order_status.py"
    )
    expect(page.locator(".margin", has_text="a test: known order")).to_have_count(1)
