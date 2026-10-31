# Repair queue: hold the queue to its four rules

The Spoke and Chain bike shop keeps its waiting jobs in a queue. Each row shows
a ticket number, a title, a customer, a Priority menu and a Finish button. Three
of the five jobs are titled "Brake pads", for three different customers, so the
title alone won't pick out one row. The ticket number will.

The queue starts with these jobs.

| ticket | title | customer | priority |
|---|---|---|---|
| #101 | Brake pads | Ruiz | Normal |
| #102 | Flat tire | Okafor | High |
| #103 | Brake pads | Chen | Low |
| #104 | Chain tune | Patel | Normal |
| #105 | Brake pads | Ito | Normal |

Write Playwright tests that hold the queue to the rules below.

## The rules

1. The queue lists every High job, then every Normal job, then every Low job.
   Inside one priority, the lower ticket number comes first.
2. Picking a new priority in a row's Priority menu moves that row to the place
   rule 1 gives it, with no reload.
3. Clicking Finish on a row opens the browser's own `confirm()` dialog, not
   anything drawn on the page. Its message names that row's ticket, title and
   customer, in this form: `Finish #103 Brake pads for Chen?`
4. Accepting the dialog removes that job, and only that job, from the queue,
   and adds a line in the form `#103 Brake pads (Chen)` to the end of the Done
   list. Dismissing it leaves the queue as it was and adds nothing to Done.

## What you are given

- `app/` is the queue itself. Read it if you want to.
- Write your tests in TypeScript with `@playwright/test`, in a file ending
  `.spec.ts` under `learner/mine/`.
- Each test gets a fresh `page`, and `await page.goto('/')` opens the queue.
  Nothing else is set up for you.
- Every test starts from a fresh page, so the queue is back to the table above.

## How this is graded

Your tests run against the real queue and against seven broken copies of it.
Passing the real queue isn't the bar, because a test that asserts nothing passes
the real queue. Each broken copy has one bug a developer could plausibly ship,
and your tests have to notice.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, so nothing was established |

A cell says what happened, not whether it's good news. `silent` against the
real queue is correct. `silent` against a broken copy is the thing to go fix.
