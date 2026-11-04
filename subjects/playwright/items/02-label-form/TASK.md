# Label desk: hold the form to its four rules

The Northgate Label Desk prints shipping labels for a small warehouse. You fill
in a recipient, a postcode, a weight in kilograms and a service, then press
Print label. The desk shows "Checking..." for a moment while it looks the label
over. When "Checking..." clears, the desk has answered: either the label is
printed, or a message shows up under each field that's wrong.

That wait is where the interesting behavior lives. Nothing is printed and no
message shows up until the answer is in, so "nothing printed" right after the
click doesn't tell you anything yet.

Write Playwright tests that hold the desk to the rules below.

## The fields

| field | it's fine when | the message under it otherwise |
|---|---|---|
| Recipient | it isn't blank. Spaces alone count as blank. | `Enter a recipient.` |
| Postcode | it's exactly five digits, no more and no fewer | `Postcode must be five digits.` |
| Weight | it's a number over 0 and at most 30 | `Weight must be over 0 and at most 30 kg.` |
| Service | see rule 3 | `Express takes 5 kg or less.` |

## The rules

1. A label with every field fine is printed. One row is added to the printed
   labels list, reading like `Ada Lovelace, 02139, 2.5 kg, Standard`. The
   recipient, postcode and weight boxes are emptied. The service stays where it
   was.
2. A label with mistakes is refused. Every field that's wrong gets its own
   message at once, not just the first one, and no row is added. A refused
   label keeps what you typed.
3. Express takes parcels up to and including 5 kg. A heavier parcel on Express
   is refused with the message under Service, and the weight gets no message.
   This only applies to a weight that's fine on its own. A weight that's wrong
   gets the weight message and nothing under Service.
4. Every message belongs to the latest press of Print label. Fix the mistakes,
   press it again, and every old message is gone.

## What you are given

- `app/` is the desk itself. Read it if you want to.
- Write your tests in TypeScript with `@playwright/test`, in a file ending
  `.spec.ts` under `subjects/playwright/workspace/mine/`.
- Each test gets a fresh `page`, and `await page.goto('/')` opens the desk.
  Nothing else is set up for you.
- Each test gets a fresh page, so the printed list starts empty every time.

## How this is graded

Your tests run against the real desk and against several broken copies of it.
Passing the real desk is not the bar, because a test that asserts nothing passes
the real desk. Each broken copy breaks exactly one rule, and your tests have to
notice.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, so nothing was established |

A cell says what happened, not whether it is good news. `silent` against the
real desk is correct. `silent` against a broken copy is the thing to go fix.
