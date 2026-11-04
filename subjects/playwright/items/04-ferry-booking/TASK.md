# Ferry booking: hold the browser's Back button to four rules

The Gull Isle Ferry books a crossing in three steps: pick a crossing, enter the
passengers, then review and confirm. Each step has its own address, `#/crossing`,
`#/passengers` and `#/review`, and the confirmation lives at `#/done`. Walking
forward is easy. The interesting behavior is what happens when you go back, or
skip ahead.

Write Playwright tests that hold the booking to the rules below. "Back" always
means the browser's Back button, which is `page.goBack()`. The app has no Back
button of its own.

## The rules

1. Going Back keeps what was entered. Back from the review step shows the
   passengers step with the lead passenger's name and the number of passengers
   as they were. Back again shows the crossing step with the same crossing
   picked.
2. The review step shows the trip as it stands now. If you go Back, change the
   crossing, the name and the number of passengers, and come forward again,
   review shows the new crossing, the new name, the new number and the new
   fare. The fare is the crossing's price a person times the number of
   passengers.
3. Confirming the same trip twice books it once. Back from the confirmation
   returns to the review step. Confirming again from there, with nothing
   changed, shows the same booking reference as the first time, and the list
   of bookings on the confirmation has one row.
4. A later step can't be opened before a crossing is picked. Opening
   `#/passengers` or `#/review` by its address, before anything has been
   entered, shows the crossing step, and the address changes to `#/crossing`.

## What you are given

- The booking itself, running live. Its address is on this page, under The app.
- Write your tests in TypeScript with `@playwright/test`, in a file ending
  `.spec.ts` under `subjects/playwright/workspace/mine/`.
- Each test gets a fresh `page`, and `await page.goto('/')` opens the booking.
  `await page.goto('/#/review')` opens the review step by its address. Nothing
  else is set up for you, and nothing entered in one test carries into the next.

## How this is graded

Your tests run against the real booking and against four broken copies of it.
Passing the real booking is not the bar, because a test that asserts nothing
passes it. Each broken copy breaks exactly one rule, and your tests have to
notice.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, so nothing was established |

A cell says what happened, not whether it's good news. `silent` against the
real booking is correct. `silent` against a broken copy is the thing to go fix.
