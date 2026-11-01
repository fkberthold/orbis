# What Playwright does that Selenium leaves to you

Coming from Selenium and pytest, most of a Playwright test will look familiar.
The differences sit in four places: what a locator is, what an action waits
for, what an assertion does, and what each test starts with. Each one removes a
chore you'd write by hand in Selenium, and each one has an edge of its own.

```ts
import { test, expect } from '@playwright/test';

test('a tool can be checked out', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Borrower').fill('Sam');
  await page.getByLabel('Tool').selectOption('torque wrench');
  await page.getByRole('button', { name: 'Check out' }).click();
  await expect(page.getByRole('listitem')).toHaveCount(1);
});
```

If you've used Robot Framework's Browser library, you've already used
Playwright underneath, since that library is built on it. SeleniumLibrary is
the one this lesson contrasts with.

## Each test starts with a fresh context

`page` is a fixture, requested by name the way pytest fixtures are. Each test
gets a new browser context, which is one isolated session with its own cookies
and storage. A context is cheap to make, so isolation per test is the default
rather than a cost you weigh, as it is with a WebDriver session. The runner
also knows the app's base URL, so `page.goto('/')` opens the front page.

## A locator is a query, not a handle

`find_element` hands back a `WebElement`, a reference to one node, which goes
stale when the page re-renders it. A Playwright locator holds no node. It's a
query that runs again every time you act on it or assert with it, so there's
nothing to go stale, and a locator made before the page changes still works
after.

Locators are also strict. `find_element` quietly takes the first match. A
Playwright action on a locator that matches two elements throws instead, and
names both. That turns an ambiguous locator into a failure you see on the first
run, where Selenium would let it click the wrong thing.

The docs' advice is to locate by what a user sees, in this order:

| find it by | for example | breaks when |
|---|---|---|
| role and name | `page.getByRole('button', { name: 'Check out' })` | the wording changes for the user |
| label | `page.getByLabel('Borrower')` | the label's wording changes |
| text | `page.getByText('Check out')` | the wording changes, or two things share it |
| test id or CSS | `page.locator('#checkout')` | someone renames the id |

`getByRole` queries the accessibility tree, which has no direct equivalent in
WebDriver. I think it's the main reason to prefer it over an id: a test written
that way breaks when the page changes for a user, and holds when only the
markup underneath moves. Ids are for things with no role or name, like a bare
paragraph.

Older tests hand the selector to the page, as in `page.click('#checkout')`.
That still runs, and the docs mark it discouraged.

## Actions wait for the element to be usable

Selenium's implicit wait covers an element being present, and anything more is
an explicit `WebDriverWait`. Playwright folds that into every action. Before a
click it waits until the element is attached, visible, holding still, enabled
and not covered by something else. The docs call these actionability checks.

An action has no timeout of its own by default. What stops a click on a button
that never enables is the test's timeout, 30 seconds. When what you're testing
is what happens if someone clicks anyway, `{ force: true }` skips the checks.

```ts
await page.getByRole('button', { name: 'Save' }).click({ force: true });
```

## Assertions retry, and a snapshot doesn't

`await expect(locator).toHaveText('Saved')` checks, and if the page doesn't
agree yet, checks again, for up to five seconds. That's the explicit wait and
the assertion as one call. The docs call these web-first assertions.

The habit that undoes it comes straight from Selenium. Read the value, then
assert on it:

```ts
expect(await page.getByRole('status').textContent()).toBe('Saved');
```

That reads the text once and compares a string. Nothing retries, so it's back
to racing the page. Assert on the locator, and let Playwright do the reading.

## Look at the page before you write

Each practice item runs its real app on a port of its own, linked from the item
page. Your tests go in `learner/mine/`. Run these from `learner/`, after
`source env.sh`:

| to | run |
|---|---|
| record clicks as test code and pick up locators | `npx playwright codegen --target playwright-test <address>` |
| step through a test with the page beside it | `BASE_URL=<address> npx playwright test mine/<file> --ui` |
| watch it run in a real browser window | `BASE_URL=<address> npx playwright test mine/<file> --headed` |

The `--ui` runner is the one with no Selenium counterpart. It records a DOM
snapshot at every step, so you can scrub back through a run and see the page as
each action saw it. A trace from a CI failure opens the same way, and I'd expect
it to replace most screenshot-on-failure debugging.

## How this course grades

The grade is mutation testing with the roles swapped. The app is what gets
mutated, and your suite is what gets scored. Your tests run against the real
app and against copies with one rule broken each. A suite passes the grade when
it passes the real app and fails every broken copy.

So for every rule in a task, the question is what your test does if the app
gets that rule wrong.
