# The TypeScript you need, read against Python

Most of a Playwright test reads like Python with braces. One thing doesn't, and
it's the reason this lesson exists: a TypeScript promise starts running the
moment you create it, and a Python coroutine doesn't.

```ts
import { test, expect } from '@playwright/test';

test('a tool can be checked out', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Borrower').fill('Sam');
  await page.getByRole('button', { name: 'Check out' }).click();
  await expect(page.getByRole('listitem')).toHaveCount(1);
});
```

## The syntax, by its Python equivalent

| TypeScript | closest Python | the difference |
|---|---|---|
| `import { test, expect } from '@playwright/test';` | `from playwright.sync_api import Page, expect` | none worth knowing |
| `test('title', async ({ page }) => { ... })` | `def test_title(page):` with a pytest fixture | the test is an argument to `test()`, not a named function the runner finds |
| `({ page })` | asking for the `page` fixture by parameter name | it's destructuring, pulling `page` out of one object of fixtures |
| `{ name: 'Check out' }` | `name="Check out"` | an object literal, which is how TypeScript passes options |
| `const x = 3;` and `let y = 3;` | `x = 3` | `const` can't be reassigned, `let` can. Use `const` unless you can't |
| `(page: Page)` | `(page: Page)` | the same idea, a hint the runtime ignores |
| `===` | `==` | plain `==` coerces types, so it's never the one you want |
| `route => route.fulfill(...)` | `lambda route: route.fulfill(...)` | an arrow function can also take a `{ }` body of many lines |

The type hints behave as Python's do at runtime. Playwright strips them
before it runs a test and doesn't check them, so a wrong type won't stop a run.
A misspelled method like `page.clik` will, but only when that line runs. Your
editor checks the types as you write, and that's the only place they're
checked.

## Promises start now, coroutines start when awaited

In Python, calling an `async def` builds a coroutine and runs none of it. Leave
off the `await` and the work never happens, and Python warns that a coroutine
was never awaited. Selenium's Python bindings, and Playwright's own sync API
for Python, block on every call, so the question never comes up.

TypeScript has no sync Playwright API, and its promises are eager. Calling
`locator.click()` sends the click to the browser right away and hands back a
promise for the result. `await` decides only whether your test waits for that
result. So a missing `await` doesn't skip the step, as it would in Python. It
detaches the step, and the test carries on while it's still running.

What that does to a test depends on what's left running. These were measured on
the practice apps, each against the real app and a copy with one thing broken.

| `await` missing on | what happened |
|---|---|
| a click or a fill | It worked anyway, because Playwright sends commands in the order you start them. That's luck, and you can't build on it. |
| an `expect` on the test's last line, that the page hasn't met yet | The test failed even against the working app. Playwright fails an assertion that's still pending when the test ends. |
| an `expect` in the middle of a test | It kept checking in the background while the next lines ran. On the booking app it happened to pass and to catch its broken copy. |
| an `expect` that's already true when it runs | The test passed against the working app **and** the broken one. It checked nothing. |

The last row is the one to fear. `expect(rows).toHaveCount(0)` with no `await`,
right after a click, passes the instant it looks, before the app has done
anything. Nothing goes red. I think it's the most expensive single word you can
leave out of a Playwright test.

The third row is the other quiet one. An assertion running in the background is
checking the page while your next lines change it, and I suspect what it ends
up checking is mostly luck.

A lint rule, `@typescript-eslint/no-floating-promises`, flags every one of
these by machine. It isn't set up in `learner/` yet, so for now the check is
reading your test back for a page call with no `await` in front of it.
