# Just enough TypeScript to read a Playwright test

You don't need much TypeScript for this course. You need to read one shape of
file, and you need to understand one idea, `await`, well enough to never leave
it out. Here's the shape.

```ts
import { test, expect } from '@playwright/test';

test('a tool can be checked out', async ({ page }) => {
  await page.goto('/');
  await page.fill('#borrower', 'Sam');
  await page.click('#checkout');
  await expect(page.locator('#loans li')).toHaveCount(1);
});
```

## Reading it line by line

| piece | what it means |
|---|---|
| `import { test, expect } from '@playwright/test';` | Take two things, `test` and `expect`, from the Playwright library. The braces name the things you want. |
| `test('a tool can be checked out', ...)` | Declare a test. The first argument is its title, the second is the test itself. |
| `async ({ page }) => { ... }` | The test is a function. `=>` is how TypeScript writes a short function. `async` says it waits on things, and more on that below. |
| `({ page })` | Playwright hands the function a bundle of ready-made helpers. The braces pull out the one called `page`, a fresh browser tab. |
| `'#borrower'` | A string. Single and double quotes mean the same thing. |
| `;` | Ends a statement. TypeScript usually works without them, and the course uses them anyway. |

Two more you'll see. `const total = 3;` names a value that won't change, and
`let` names one that will. And a helper reads like this:

```ts
async function openDesk(page: Page) {
  await page.goto('/');
}
```

The `: Page` is a type. It tells you, and your editor, that `page` is a
Playwright page. Playwright strips types out before it runs your test and
doesn't check them, so a type mistake won't stop a run. A misspelled method
like `page.clik` will, but only when that line runs.

## The one idea: `await`

The browser runs in a separate process. When your test says
`page.click('#checkout')`, it sends the click off and gets back a promise, a
ticket for a result that isn't ready yet. `await` means "stop here until the
ticket comes back." Without it, the test moves straight on to the next line
while the click is still on its way.

So every Playwright call in a test gets `await` in front of it. Every `goto`,
every `fill`, every `click`, and every `expect` on a locator.

What a missing `await` does depends on where it's missing. These were measured
on the first practice app, against the real app and against a copy with one
thing broken:

| `await` missing on | what happened |
|---|---|
| a click or a fill | It worked anyway, because Playwright sends commands in the order you start them. That's luck, and you can't build on it. |
| an `expect` the page hasn't met yet | The test failed even against the working app. Playwright fails an assertion that's still waiting when the test ends. |
| an `expect` that's already true when it runs | The test passed against the working app **and** the broken one. It checked nothing. |

The last row is the one to fear. `expect(rows).toHaveCount(0)` with no `await`,
right after a click, passes the instant it looks, before the app has done
anything. Nothing goes red to tell you. I think it's the most expensive one
word you can leave out of a Playwright test.

## The habit

Type `await` before every line that talks to the page, and read your test back
looking for a line that doesn't have one. The only lines that don't need it are
the ones that don't touch the page at all, like `const total = 3;`.
