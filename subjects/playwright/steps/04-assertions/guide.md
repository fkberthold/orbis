# Proving that nothing happened

A web-first assertion retries until its claim is true, and stops there. That
makes a claim that something appears hard to get wrong, and a claim that
something didn't appear easy to get wrong. `expect(error).toBeHidden()` passes
the first moment the error isn't showing, and right after a click, that's
usually before the page has done anything at all.

It's the same trap as a `WebDriverWait` on `invisibility_of_element_located`,
which also returns at once if the element was never there. The difference is
that Playwright puts the retry inside every assertion, so the trap is in
every absence check you write rather than the few where you reached for a wait.

Say a settings page saves in the background, then shows "Saved" or an error.

| time after the click | what's on the page | `toBeHidden()` on the error |
|---|---|---|
| 0 ms | nothing yet | passes here, and stops looking |
| 300 ms | the error appears | never sees it |

So a negative claim needs something to stand on. Wait first for a sign that the
page has finished, and only then check what's missing.

```ts
await page.getByRole('button', { name: 'Save' }).click();
await expect(page.getByRole('status')).toHaveText('Saved'); // the page has answered
await expect(page.getByRole('alert')).toBeHidden();         // so absence means something
```

The first assertion gives the second its meaning, and its `await` is doing the
work. Without it, the absence check runs at once, which is the already-true row
from lesson 0. With it, the absence check can't start until the save is over,
so nothing is left in flight to arrive late.

Pick the sign with some care. One the page shows when it's done either way,
like a busy notice going away, works for every path. One that only success
shows works for the success path, because a failure then fails the wait itself.
A sign that can show up before the answer does won't help.

I think the shape holds well beyond Playwright. A check that something didn't
happen is only as good as your evidence that it had the chance to.
