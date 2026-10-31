# Orbis

A self-teaching system that has to know whether the learner is right, without
the learner saying so and without a human having written the answer.

The name comes from Comenius's *Orbis Pictus*, the first textbook to pair text
with pictures on purpose.

## The problem this is built around

Most of a self-teaching system is bounded engineering. Researching a subject,
writing the lesson, emitting a page, provisioning something to practice on.
None of that is the hard part.

The hard part is the verdict, and three things are wanted at once.

| | arbitrary subject | trustworthy verdict | cheap authoring |
|---|---|---|---|
| a hand-built corpus | no | yes | no |
| a generated corpus | yes | no | yes |
| a written textbook | yes | yes | no |

A hand-built corpus buys its verdict with authored answers, and the authoring
is the wall. Generating everything gets over that wall and loses the verdict on
the way over. I have not seen an attempt that holds all three corners.

## The way through, as far as I can tell

A passing test proves nothing. `expect(true).toBe(true)` passes. So the question
is not whether the learner's work passes. It is whether the work
**discriminates**.

Run the learner's artifact against the real environment, and against copies of
that environment which are deliberately broken. Correct work passes the real one
and fails each break. Breaks are cheap to write and mechanically checkable,
which is what makes this affordable at all.

An item is four things.

1. A task statement.
2. One reference solution.
3. A set of mutations of the environment.
4. A gate asserting the reference passes the real environment, fails every
   mutation, and that no two mutations look the same.

Item four is what checks the other three. A reference that fails three
mutations could still be resting on one assertion that breaks three ways, in
which case two of those mutations are teaching the same thing. Comparing the
per-test outcome vectors is what catches that.

## What is here

One hand-made Playwright item, end to end, with its gate. That is all of it. No
generator, no lesson, no spoiler page, no progress store, no second subject.

The order is deliberate. The riskiest assumption in the whole design is that
mutations of a web app yield a usable oracle for a browser test, and nothing
else matters if that is false. So it gets tested first, with one item, by hand.

    items/playwright/01-seat-desk/
      TASK.md          the statement a learner reads
      app/             the real target, a static page with JS
      mutations/       three patches, one broken rule each
      reference/       the reference solution
      candidates/      three solutions the gate has to reject

    src/orbis/
      verdict.py       the four cells
      environment.py   copy the app, apply a patch, serve it
      tracing.py       count the assertions a run actually executed
      runner.py        one candidate against one environment
      gate.py          the three conditions, a selfcheck, and a filter

## Running it

This is a NixOS box, so the browsers come from nixpkgs. The ones Playwright
downloads for itself are not linked for NixOS and will not start.

```bash
source env.sh    # resolves nixpkgs#playwright-driver.browsers
uv sync

# grade the item's own reference
uv run python -m orbis.gate gate items/playwright/01-seat-desk

# prove the gate can fail, by running the candidates it must reject
uv run python -m orbis.gate selfcheck items/playwright/01-seat-desk

# sort a generated set of patches by what the reference makes of each one
uv run python -m orbis.gate filter items/playwright/01-seat-desk --mutations <dir>
```

`filter` reports rather than judging. It groups the caught patches by vector,
and you keep one per group. It lists the silent ones separately, since a silent
patch is either outside the rules or a hole in the reference.

## Measured, 2026-10-30

Playwright 1.59.0 against the nixpkgs driver at 1.59.1, chromium revision 1217,
reporting chromium 147.0.7727.15. The reference passes the real desk with 15
assertions executed, and each mutation produces a different failure vector.

| environment | cell | vector |
|---|---|---|
| real | silent | pass pass pass pass |
| m1-no-inflight-lock | catches | FAIL pass pass pass |
| m2-no-taken-check | catches | pass pass FAIL FAIL |
| m3-spinner-never-clears | catches | pass FAIL pass pass |
| m4-reserved-seat-not-recorded | catches | pass pass FAIL pass |

Vector order is `test_double_click_reserves_once`, `test_reserve_succeeds`,
`test_reserved_seat_is_refused_next_time`, `test_taken_seat_is_rejected`.

The fourth test and `m4` came from a generated mutation the original three
tests were silent on (orb-eei.1). Rule 2 already covered it, so it was a hole in
the reference rather than a break outside the rules.

All three rejected candidates behave as they should. The one that asserts
nothing reads `vacuous` against every copy. The one that only checks the page
heading reads `silent` against every copy, including the broken ones. The one
that cannot be imported reads `did-not-run`. Every cell in the vocabulary is
driven by something, which is the point of shipping them.

## What this does not solve

**Equivalent mutations.** A break that changes nothing observable teaches
nothing, and detecting that in general is undecidable. The gate catches the
pairs the reference cannot tell apart, which is a floor rather than a solution.

**Mutations worth making.** A break nobody would ever write is a contrived
exercise wearing a verdict. Generatable is not the same as worth generating.

**A candidate that asserts a constant.** The vacuous cell counts assertions
from the trace and looks for an assert statement in the source, so `assert True`
counts as having asserted. The gate still rejects such a candidate, because it
stays silent against every mutation. Different cell, same outcome, and worth
knowing which one did the work.

**A learner who invents the interface.** Playwright is the easy case, because
the app defines the DOM and the test addresses it. A subject where the learner
names the state is harder, and nothing here speaks to it.

**Lesson sequencing.** Untouched, and I suspect it is the weakest link in the
whole design.

## License

MIT. See `LICENSE`.
