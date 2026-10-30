# Seat desk: hold the desk to its three rules

The Dockside Seat Desk has four seats and two of them are already booked. A
reservation takes a moment to confirm, and that moment is where the interesting
behavior lives.

Write Playwright tests that hold the desk to the rules below.

## The rules

1. A reservation on a free seat shows a banner naming the seat and the person,
   adds one row to the reservations list, and clears the "Reserving..." notice.
2. A reservation on a taken seat is refused with an error naming the seat, and
   adds no row.
3. Clicking Reserve twice in quick succession reserves once and reports no
   error.

## What you are given

- `app/` is the desk itself. Read it if you want to.
- Your tests run against a `--base-url`, so `page.goto("/")` reaches it.
- `page` is the pytest-playwright fixture. Nothing else is set up for you.

## How this is graded

Your tests run against the real desk and against three broken copies of it.
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
