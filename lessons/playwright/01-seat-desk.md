# A first Playwright test, and what makes it worth anything

A Playwright test here is a `test(...)` in a file whose name ends `.spec.ts`.
Playwright hands each test a fresh browser tab called `page`, already pointed at
the app. So `await page.goto('/')` opens the app's front page, whatever port it
happens to be on today.

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
| its role and name | `page.getByRole('button', { name: 'Check out' })` | restyling, new ids, moving it around | the label's wording changes |
| its label | `page.getByLabel('Borrower')` | the same | the label's wording changes |
| its text | `page.getByText('Check out')` | most markup changes | the wording changes, or two things share it |
| an id | `page.locator('#checkout')` | restyling, moving it around | someone renames the id |
| its place in the layout | `page.locator('form > div:nth-child(3) button')` | almost nothing | anything moves |

Playwright's own advice is to start at the top row and go down only when you
have to, and I'd follow it. A role and a name are what a person using the page
sees, so a test written that way breaks when the page changes for a user and
mostly holds when it changes only underneath. Some things on a page have no
role or name to find them by, a plain paragraph of text for one, and that's
what an id is for. The last row is the one to avoid, because it tests the
layout by accident.

You'll also see older tests written as `page.click('#checkout')`, with the
selector handed to the page. That still runs, and the docs mark it
discouraged. Find the thing first, then act on it.

## Doing things

`click`, `fill` and `selectOption` are called on a locator, and they don't fire
blindly. Before a click, Playwright waits until the element is attached, visible, holding still,
enabled, and not covered by something else. It waits up to 30 seconds for
that, and then fails. That wait is why most tests need no sleeps. It also means
a click on a button the app has disabled sits there until it times out.

When what you're testing is exactly what happens if someone clicks anyway, pass
`{ force: true }`. It skips the checks and fires the click as is.

```ts
await page.getByRole('button', { name: 'Save' }).click({ force: true });
```

## Checking things

`await expect(locator)` is how a test says what should be true. It doesn't
check once. It keeps checking until the page agrees or five seconds pass, so
you can assert on something that's about to appear without timing it yourself.
Lesson 2 digs into where that helps and where it quietly doesn't.

A test that never calls `expect` checks nothing, however much it clicks. And,
from lesson 0, an `expect` without its `await` can check nothing too.

## Look before you write

You can't write a good test for a page you haven't watched. Each practice item
runs its real app on a port of its own, linked from the item, and I'd spend the
first few minutes there. Click through it, see what changes, and see when.

Your tests go in `learner/mine/`. Run these from `learner/`, after
`source env.sh`, with the app's address from the item page:

| to | run |
|---|---|
| record your clicks as test code, and pick up selectors | `npx playwright codegen --target playwright-test <address>` |
| run your tests one step at a time, with the page beside them | `BASE_URL=<address> npx playwright test mine/<file> --ui` |
| watch your tests run in a real browser window | `BASE_URL=<address> npx playwright test mine/<file> --headed` |

The `--ui` one is worth learning early. It shows every step of a test with a
snapshot of the page at that moment, which is the plainest way I know to see a
timing problem.

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
