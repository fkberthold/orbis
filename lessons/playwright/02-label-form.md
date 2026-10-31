# Proving that nothing happened

An assertion in Playwright doesn't check once. `expect(locator).toHaveText('Saved')`
looks at the page, and if the text isn't there yet it looks again. It keeps
looking for up to five seconds and fails only when that deadline passes. That's
why most Playwright tests don't need a sleep. The assertion does the waiting,
and it stops the moment the page agrees.

The retry works the same way for a claim that something is absent.
`expect(rows).toHaveCount(0)` passes the first time it finds no rows, and
`expect(error).toBeHidden()` passes the first time the error isn't showing.
Each one stops at the first moment the claim is true, which suits a claim that
something appears and catches people out on a claim that something doesn't.

Say a settings page saves in the background. It shows "Saved" when the save
works, or an error when it doesn't. Click Save, and the page is quiet for a
moment before either one appears. Check for "no error" during that moment and
the check passes, because there's no error yet. It would pass the same way
against a page that's about to show one.

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
work. Without it, the absence check runs at once, which is the already-true
trap from lesson 0 all over again. It can only pass once the
save is over, so by the time the absence check runs, nothing is left in flight
to arrive late.

Pick the sign with some care. One the page shows when it's done either way,
like a busy notice going away, works for every path. One that only success
shows works for the success path, because a failure then fails the wait itself.
A sign that can show up before the answer does won't help.

A fixed sleep looks like a way out, and I'd avoid it. It works on most runs,
flakes on the slow ones, and makes every run pay for the slowest case. It also
hides the claim you're making, which is that the page has answered, behind a
number.

I think the shape holds well beyond Playwright. A check that something didn't
happen is only as good as your evidence that it had the chance to.
