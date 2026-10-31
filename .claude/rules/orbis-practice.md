# How an Orbis item is authored, and what has already bitten

Read this before authoring an item or touching the runner. It is the recipe and
the hazard list. The argument for why the design is shaped this way is in
`CLAUDE.md` and is not repeated here.

---

## The recipe, in order, and the order matters

**1. Write the target app, or pick the environment.** It has to be MUTABLE BY
EDITING FILES, which is what makes a mutation cheap. A static page with JS is
enough for forms, waiting and async, which is where the interesting lessons
live. Docker exists for a disposable target and is usually overkill.

Write it fresh. Do not copy somebody's app or their exercise. The predecessor
project has an open bead about redistributing corpus material without a license,
and the pattern that avoids it is to write the prose fresh and fetch oracles
rather than commit them.

**2. Write the task statement, `TASK.md`.** State the rules the learner must
hold the app to. Then state how the grade works, including the four cells,
because a learner who does not know that `silent` against a break is the defect
cannot read their own grade.

**Do not state the readings you are not asking for.** The predecessor project
measured 29 of 64 of its prompts as underdetermined, and the failure was always
the same: a sentence that admits two readings where the reference silently
assumes one. Before you freeze a task statement, ask of every rule: **does this
leave the reader a choice I am resolving silently?** The classes that recur:

- **Mood mixing.** "A can IS VENDED when..." beside "a customer CAN insert"
  reads as forced beside permissive, and both readings reached the same state
  count. Keep the mood uniform or say which is which.
- **A guard's strength.** Whether a step is guarded on a condition is the single
  most common thing a reader must guess, and a table of what should be possible
  cannot reach it.
- **The setting the verdict depends on.** The predecessor shipped eight items
  whose published verdict was unreachable because a run setting was unstated.

**3. Write the reference solution.** Idiomatic for the subject. For Playwright
that is pytest-playwright with the `page` fixture and a `--base-url`, so
`page.goto("/")` reaches the app. **Do not invent an interface.** The whole
reason Playwright is the easy corner is that the environment supplies the
interface, and shimming it spends that advantage to measure it.

**4. Write the mutations, as PATCHES and not forks**, so the diff states what
broke. Generate them with `git diff` in a throwaway repo so `git apply` takes
them. One broken rule each.

**Each mutation must break a DIFFERENT test of the reference.** That is gate
condition G3 and it is what stops two mutations teaching the same thing. Work
out the intended per-test vector on paper before you run anything, then check
the run against it.

**5. Write the candidates the gate must REJECT.** At least these three, and the
item is not done without them:

- one that asserts nothing, which must read `vacuous` everywhere
- one that passes the real app with a real assertion and catches nothing, which
  must read `silent` everywhere
- one that cannot be collected, which must read `did-not-run` everywhere

The second is the one that matters. A pass-or-fail instrument calls it correct.

**6. Run `scripts/test` and read the output file.** Then make a mutation stop
applying on purpose and confirm tier 1 names it. A gate you have not watched
fail is not evidence.

---

## The four cells, and the one that needed a decision

    catches       the candidate failed against this environment
    silent        the candidate passed, with real assertions
    vacuous       the candidate passed, having asserted nothing
    did-not-run   no verdict was reached

**Vacuity is read off the Playwright TRACE, and that choice is load-bearing.**
Every assertion appears in `trace.zip`'s `trace.trace` as a `before` event with
`class: "Frame"` and `method: "expect"`, with `params.expression` carrying the
matcher name such as `to.have.text`. Counting those gives assertions actually
executed, without touching the API the learner writes against.

**There is no `apiName` field on this build**, which is the field the obvious
first attempt reaches for. Measured 2026-10-30.

**The known hole, and it is in the README rather than hidden.** A plain `assert`
statement never reaches the trace, so `tracing.has_assert_statement` scans the
source with `ast` as a second channel, and a candidate counts as asserting if
either channel says so. That errs toward calling a run non-vacuous. So
`assert True` reads as an assertion and the vacuous cell MISSES it. It is still
rejected, by G2, because it stays silent against every mutation. Different cell,
same outcome, and say which one did the work when you report.

---

## Hazards measured on this box

**Playwright and NixOS.** In `CLAUDE.md`. The short version is that the browsers
nixpkgs builds are the only ones that start, versions line up by minor, and
`env.sh` resolves the store path through nix.

**`uv sync` picks an interpreter with no playwright wheel** unless
`requires-python` caps it below 3.14, and the error reads as a missing
playwright release rather than a missing wheel.

**A `nix build` can die with "Nix daemon disconnected unexpectedly"** while
`curl` to the same host returns 200. Retry once before believing it.

**A double click needs `force=True` on a button the app disables**, since
Playwright waits for actionability and would otherwise time out. `page.dblclick`
with `force=True` fires two clicks tightly enough that the app's in-flight lock
is what decides the outcome, which is the behavior under test.

**A race in the app must be made deterministic or the test flakes.** In
`01-seat-desk` the second click's handler resolves AFTER the first because its
timer was set later, so the outcome is fixed rather than timing-dependent. If a
mutation's effect depends on which of two timers fires first, the item is not
authorable yet.

---

## Hazards of the agent harness, not of this project

These are about the Bash tool and they apply in any repo.

**`grep` is ugrep, not GNU, and it lies on some patterns.** The word-boundary
idiom `(^|[^class])TOKEN` returns 0 where GNU returns 6, in ERE, BRE and with
`-o`. `\b`, `-w`, `\<` and `[[:space:]]` agree with GNU. `find` is bfs and
rejects `-newermt` with a relative time. **When a count matters, use
`command grep` for GNU, or put the scan in a scratch script, and run it both
ways before writing the number down.**

**The isolation harness refuses command lines it cannot statically verify**, and
there are six known causes: too many clauses, an interpreter name anywhere
including inside a search pattern, a variable expanded into an argument, setting
`HOME=`, `/\` on a command line, and brace groups. **The workaround for all six
is a scratch script under `/tmp/claude-1000/`.**

**A `pgrep -f` wait loop matches its own command line and never exits.** Do not
poll for a process. A background call notifies on completion.

**A dispatched worker cannot write outside its worktree**, and asking it for a
report file is a coin flip that has been refused with "Subagents should return
findings as text, not write report files". **Ask for the return value and stop
there.**

**`~/.claude/hooks/edit-after-failure-guard.sh` blocks Edit and Write after a
failing test result** until a test file is edited, and it will not recognize
`scripts/test` as one. A RED run that is red by design trips it. The escape is
`touch .claude/no-edit-after-failure-guard`, and **that marker is not
gitignored, so remove it before any footprint check.**

---

## A note on where this project's memory lives

Decisions go in the MemPalace **`orbis`** wing, `decisions` room. Findings go in
`findings`. The predecessor's wing is `tla_puzzles` and it holds every
measurement this design rests on, so it is worth searching when a question feels
like it has been answered before. It usually has.

The drawer is the design source of truth and the repo is the implementation
source of truth. When they diverge, the drawer wins on intent and the repo wins
on what currently works.
