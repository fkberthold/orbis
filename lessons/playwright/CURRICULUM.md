# The Playwright curriculum, a draft for review

**The goal** is to own a real suite: write and maintain the Playwright and
TypeScript tests for a real app at work. That decides what counts as
fundamental. Config, fixtures, page objects, sign-in reuse, API calls in tests,
flaky-test diagnosis and CI all have to be in the course, not left as extras.

**The learner** has twenty years of QA and isn't a TypeScript expert. The
research on expertise reversal says to guide heavily where he's new (TypeScript,
the Playwright API) and lightly where he isn't (what a test should prove).

## Where the lessons come from

The rule is to use a good existing course before writing one. So three
candidates were read against the goal on 2026-10-31.

| candidate | progressive? | current? | exercises? | reaches the goal? |
|---|---|---|---|---|
| playwright.dev docs | the 7 Getting Started pages are, the rest is reference sorted A to Z | yes, 1.64 | none | every topic |
| Microsoft Learn | one 64-minute module | yes | follow-along only | stops before fixtures |
| Test Automation University | yes, intro then advanced | no, pinned to 1.3x | open questions, no grader | yes, mostly video |

None of them is a good progressive course all the way to the goal. So the docs
pages are the chapters, read in the order below, and Orbis supplies the order,
a short guide per step, every graded exercise, and the few lessons nothing
covers. This is the reverse of the TLA+ setup, where learntla supplied the
order too.

## How a step works

1. **Read** the docs pages for the step, after the Orbis guide that says what
   TypeScript you need first and which trap to watch for.
2. **Practice** on an item: a small app, rules to hold it to, and the gate that
   runs your test against the real app and broken copies.
3. **Reveal** the worked answer one line at a time, after you've tried.

Practice comes in three formats, as it did in tla-puzzles. **Complete the
skeleton** gives you a test with the hard part left out. **Write from a prompt**
starts from an empty file. **Predict, then check** asks what a test or a trace
will show before you run it. Skeletons lead in the early steps, while the
TypeScript is new, and give way to blank files as the steps go on.

## The steps

| step | read | Orbis writes | practice |
|---|---|---|---|
| 0 | | **Just enough TypeScript** (exists) | predict, then check: which missing `await` passes quietly |
| 1 | intro | guide | none graded. Install, run the example, open the report |
| 2 | writing-tests | guide, with a note on `{ page }` ahead of fixtures | **item 01, seat desk** (exists) |
| 3 | locators, dialogs | guide: role first, then filtering a list | **item 05, repair queue** (exists, moved up) |
| 4 | test-assertions, actionability | guide from lesson 02 (proving nothing happened) | **item 02, label form** (exists) |
| 5 | running-tests, codegen-intro, test-ui-mode, trace-viewer-intro, debug | guide | new: read a trace of a failing test and say why it failed |
| 6 | navigations | guide | **item 04, ferry booking** (exists) |
| 7 | test-configuration, test-use-options, test-projects | guide | new, and the instrument is open (see below) |
| 8 | test-fixtures, test-global-setup-teardown | guide, plus the TypeScript for `test.extend<...>` | new: a fixture that sets the app up |
| 9 | pom | guide, plus TypeScript classes | new: refactor a test into a page object, and the gate checks it still discriminates |
| 10 | auth | guide | new: sign in once and reuse it |
| 11 | api-testing | guide | new: set up data through the API, then check the page |
| 12 | mock, network | guide from lesson 03 (what a stub can't see) | **item 03, parts lookup** (exists, moved down) |
| 13 | test-timeouts, test-retries, trace-viewer | **Diagnosing a flaky test**, which nothing covers | new: tell an app bug from a test bug with a trace |
| 14 | test-parallel, test-sharding | guide | new, and the instrument is open |
| 15 | ci-intro, ci | guide | new, and the instrument is open |
| 16 | best-practices | **Keeping a suite healthy**: layout, test data, tags, reviewing tests | capstone: a small suite for a bigger app |

Every page name in the read column is under `https://playwright.dev/docs/`.

Two of the existing items move. Mocking comes after structure, because owning a
suite needs fixtures and sign-in reuse before it needs stubs. Locators come
before assertions, because the docs' best practices make the choice of locator
the first thing to get right.

## What Orbis has to write

- **Lesson 0, just enough TypeScript.** It exists, and it gains classes,
  `type` and generics only as far as steps 8 and 9 need them.
- **A guide per step,** short, pointing at the docs rather than repeating them.
- **Diagnosing a flaky test** (step 13). I think this is where twenty years of
  QA pays off most, and the broken copies are made for it: a mutation can be a
  race on purpose.
- **Keeping a suite healthy** (step 16).
- **Every graded exercise.** None of the candidates has a grader.

## Drills

Drills run alongside the course, not after it, as they did in tla-puzzles. Each
is a short prose prompt and a small app, answered from an empty `.spec.ts` in
about ten minutes and graded by the gate. They come in families that interleave
(locators, waiting and assertions, navigation, network, structure, sign-in and
API, flaky diagnosis), and a drill only enters the queue once the step that
teaches it is done. Every drill names the step that teaches it, by path. In
tla-puzzles a drill with no pointer to its lesson took three hours against a
ten-minute budget.

## Open questions

1. **Does the order look right?** In particular, locators before assertions,
   and mocking moved after structure.
2. **Steps 7, 14 and 15 have no instrument yet.** A broken copy of an app can't
   tell whether a config, a sharding setup or a CI file is right. They might
   need a different check, or be guide-only with no graded practice.
3. **The existing lessons 01 to 03** become the guides for steps 2, 4 and 12.
   They use the discouraged `page.click(selector)` style and say ids first,
   both of which get fixed (bead orb-eei.17) whatever the order turns out to
   be.
