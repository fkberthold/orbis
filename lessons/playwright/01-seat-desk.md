# A first Playwright test, and what makes it worth anything

A Playwright test here is a pytest function that takes a `page`. The `page` is
a fresh browser tab that pytest-playwright hands you, and it's pointed at the
app through `--base-url`. So `page.goto("/")` opens the app's front page,
whatever port it happens to be on today.

```python
from playwright.sync_api import Page, expect


def test_a_tool_can_be_checked_out(page: Page) -> None:
    page.goto("/")
    page.fill("#borrower", "Sam")
    page.select_option("#tool", "torque wrench")
    page.click("#checkout")
    expect(page.locator("#loans li")).to_have_count(1)
```

That's the whole shape, and every test you write in this course is some
arrangement of three moves: find something on the page, do something to it,
and check what the page did back.

## Finding things

A locator is a description of where something is, not a grab of the thing
itself. Playwright looks it up again every time you use it, so a locator made
before the page changes still finds the element after. Which description you
pick decides what your test survives.

| you find it by | for example | survives | breaks when |
|---|---|---|---|
| an id | `#checkout` | restyling, moving it around | someone renames the id |
| its role and name | `page.get_by_role("button", name="Check out")` | restyling, new ids | the label's wording changes |
| its text | `page.get_by_text("Check out")` | most markup changes | the wording changes, or two things share it |
| its place in the layout | `form > div:nth-child(3) button` | almost nothing | anything moves |

I'd reach for ids and roles first. The apps in this course give the parts that
matter an id, so `#something` is usually the plain choice. The last row is the
one to avoid, because it tests the layout by accident.

## Doing things

`click`, `fill` and `select_option` don't fire blindly. Before a click,
Playwright waits until the element is attached, visible, holding still,
enabled, and not covered by something else. It waits up to 30 seconds for
that, and then fails. That wait is why most tests need no sleeps. It also means
a click on a button the app has disabled sits there until it times out.

When what you're testing is exactly what happens if someone clicks anyway, pass
`force=True`. It skips the checks and fires the click as is.

## Checking things

`expect(locator)` is how a test says what should be true. It doesn't check
once. It keeps checking until the page agrees or five seconds pass, so you can
assert on something that's about to appear without timing it yourself. The next
lesson digs into where that helps and where it quietly doesn't.

A test that never calls `expect`, or `assert`, checks nothing, however much it
clicks.

## Look before you write

You can't write a good test for a page you haven't watched. Each practice item
runs its real app on a port of its own, linked from the item, and I'd spend the
first few minutes there. Click through it, see what changes, and see when.
Three commands help, all run after `source env.sh`:

| to | run |
|---|---|
| record your clicks as test code, and pick up selectors | `uv run playwright codegen --target python-pytest <the app's address>` |
| watch your own tests run, slowed down | `uv run pytest my_test.py --base-url <the app's address> --headed --slowmo 500` |
| step through a test one action at a time | `PWDEBUG=1 uv run pytest my_test.py --base-url <the app's address>` |

Codegen's output is a starting point, not an answer. It writes down what you
did, and it has no idea what you meant to check.

## What makes a test worth anything

Here's the part that's particular to this course. Passing the real app isn't
the bar, because a test that checks nothing passes too. Your tests also run
against copies of the app with one thing deliberately broken, and a good test
fails on each of them. The grade tells you, for each copy, whether your tests
noticed.

So for every rule in a task, ask what your test would do if the app got that
rule wrong. If the answer is "pass anyway", the test isn't checking the rule
yet. I think that question is most of what separates a test suite from a
script that clicks around.
