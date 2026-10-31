# Orbis: project instructions for AI agents

## What this is

A self-teaching system that has to know whether the learner is right, without
the learner saying so and without a human having written the answer.

The name comes from Comenius's *Orbis Pictus*, the first textbook to pair text
with pictures on purpose.

**Frank is the sole audience.** That is a decision, not a stage, and it buys
something specific: no novelty screen, no comment gate, no freeze digest, and
items may churn or be cut after one attempt. Take the license deliberately
rather than drifting into quality apparatus. In the predecessor project that
single decision was the measured difference between a corpus of 10 items and
one of 64.

## The core problem, and do not re-derive it

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
the way over.

### The way through

**A passing test proves nothing.** `expect(true).toBe(true)` passes. So the
question is never whether the learner's work passes. It is whether the work
**discriminates**.

Run the artifact against the real environment and against copies that are
deliberately broken. Correct work passes the real one and fails each break.
Breaks are cheap to write and mechanically checkable, which is what makes this
affordable at all.

An item is four things.

1. A task statement.
2. One reference solution.
3. A set of mutations of the environment.
4. A gate asserting the reference passes the real environment, fails every
   mutation, and that no two mutations look the same.

**Item four is what checks the other three.** A reference that fails three
mutations could still rest on one assertion that breaks three ways, in which
case two of those mutations teach the same thing. Comparing the per-test
outcome vectors is what catches that.

### The second axis, and it is the harder one

Beyond "does an oracle exist" there is a second question: **who supplies the
interface the learner's artifact talks through?**

| subject | oracle | interface |
|---|---|---|
| Playwright | yes | the ENVIRONMENT. The app defines the DOM and the test addresses it |
| TLA+ | yes | the LEARNER. He invents the variables |

That second column cost the predecessor project two days. Its refutation
instrument bound by name, so it needed the learner's variable names to match
the reference's, 28 of 235 cells were unreachable by any naming, and the
resolution was to stop pairing the modules at all.

**Playwright is the easy corner on both axes.** That makes it a good first
target and a poor stress test for generality. Know which one you are looking at
while building.

## THE GATE DISCIPLINE, and it is not negotiable

**Watch the gate fail before believing it.** Every item ships candidates whose
only job is to be rejected, and `selfcheck` asserts that they are. A gate that
accepts everything measures nothing.

The reason this is a rule rather than a preference: in the predecessor project
a specification asserting nothing scored `count=MATCH run=CLEAN`, and a
tautological test assertion got written and shipped twice, once by the agent
that wrote the rule against it. The check that caught both was watching the
thing fail first.

**The four cells**, copied from the predecessor's refutation instrument rather
than reinvented, because two cells were measured as not enough:

    catches       the candidate failed against this environment
    silent        the candidate passed, with real assertions
    vacuous       the candidate passed, having asserted nothing
    did-not-run   no verdict was reached, so nothing was established

**A cell names what the run established, not whether that is good news.**
`silent` against the real app is correct. `silent` against a break is the
defect. The gate is what says which belongs where.

**Every cell must be driven by something.** `did-not-run` was going to be a
name in a table until a candidate that cannot be imported was added on purpose.
A vocabulary with undriven entries is decoration.

## Build and test

```bash
source env.sh                  # resolves the nixpkgs Playwright browsers
uv sync                        # install, uv and never pip
scripts/test                   # the real gate over every item
scripts/test --fast            # the tier that starts no browser
scripts/lint                   # ruff over src/ and items/
```

`scripts/test` runs `selfcheck` on every item, which grades the reference AND
every candidate the item ships to be rejected. That is the gate, and it is the
command to gate on.

**A canonical command that does not exist yet stays EMPTY in the constitution
rather than naming something that fails by design.** The predecessor recorded
every verb as empty on purpose for a week for exactly this reason. An empty
verb means no honest command exists, never that nobody got round to it.

## This is NixOS, and Playwright needs one thing

**The browsers Playwright downloads for itself are not linked for NixOS and
will not start.** The ones nixpkgs builds do. `env.sh` resolves the store path
through nix rather than hardcoding it, since a channel bump moves it.

    nix build --no-link --print-out-paths nixpkgs#playwright-driver.browsers
    export PLAYWRIGHT_BROWSERS_PATH=<that path>
    export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

**Versions line up by minor.** nixpkgs `playwright-driver` is 1.59.1 and its
bundle carries chromium-1217. PyPI has no playwright 1.59.1, so the pin is
`playwright==1.59.0` and it drives that bundle. Measured 2026-10-30, reported
chromium 147.0.7727.15.

**Two things that bite and are not the linking problem.** `uv sync` will pick a
CPython with no playwright wheel unless `requires-python` caps it, and the error
reads as a missing release rather than a missing wheel. And a `nix build` can
die with "Nix daemon disconnected unexpectedly" while `curl` to the same host
returns 200, so retry one before believing it.

`pip install` into the system is not how this box works. `uv` for Orbis's own
Python, a flake or devbox per learning environment, docker for a disposable
target. **`podman` is ABSENT, so do not reach for it.**

## Conventions

### Prose a human reads goes through `frank-writing`

Never an em dash. Never a semicolon. American spelling. That covers READMEs,
task statements, commit messages, PR text and error messages. **Code comments
count**, and in this repo they carry the argument for why a thing is shaped the
way it is, so they are held to the same standard.

Beads, MemPalace drawers and conversation are governed by the `sr-opus-5` output
style instead, and `frank-writing` should not fire on them.

### A claim of absence or completeness names its search

Before writing that something does not exist, is not used, or is the whole set,
say which surfaces you looked at. Then ask the question that actually catches
it: **which surface would I expect this in that I did not check?**

This is a procedure, not a disposition, because the general instruction to be
careful has failed repeatedly in the predecessor project. Ask it of a GATE too:
which surface would I expect this gate to read that it does not?

### An instrument's stated reach can be conditional on something nothing establishes

Ask of any instrument: **what must be true of the input for my stated reach to
hold, and what establishes it?** A reach measured over references, where the
author controlled both sides, tells you nothing about reach over learner work.

### Read the output file, never a compound command's exit code

Run a long gate as `scripts/test > file 2>&1` with no trailing command, then
read the file's verdict line. A trailing `echo` inside a backgrounded compound
command reports the echo's status, and the harness repeats that number back with
authority. This caught the predecessor project four times in one session.

### Enrichment that costs minutes per item will be skipped forever

Assume the default is off and build for that from the first day. The
predecessor-of-the-predecessor spent 17 percent of its source and 16 percent of
its commits on text-to-speech that ran zero times.

## What killed the last attempt, and it will be the default outcome here too

Chiron, at `~/repos/Chiron`, is the direct predecessor and is worth reading
rather than inheriting. It built a real generator and died in the runtime
plumbing: **490 lines of prompt against 4,561 lines of CLI, storage,
orchestration and media**, with a final audit listing 13 open items of which
every single one was plumbing and none was pedagogy.

Its grader is the specific trap. The assessment prompt instructs the model to
"Provide encouraging feedback regardless of correctness" and "Never make the
learner feel bad about gaps", and `evaluate_response` is a pure passthrough. So
its mastery numbers ran off the model's claim about its own dialogue.

**An LLM self-report converted to a number is worse than no number, because it
looks quantitative.**

That is why this project starts from the runtime rather than the generator, and
why the verdict is built before anything else.

## One thing an LLM cannot do here

**An LLM cannot judge prose register.** Measured: kappa near 0 against human
annotators and 0.08 span precision. Three of the five dimensions that predict a
human slop judgment, tone among them, have no automatic measure. So a
critique-and-revise loop with a model critic revises against noise.

Verbosity, Gunning-Fog and Repetition were NOT significant predictors, so
readability indices and word counts are the wrong gate. Exact-count constraints
score 0 percent, so a density cap cannot go in a prompt and has to be a
post-generation gate. Negated instructions are a documented weak spot, so
specify the register positively with exemplars.

**Lesson prose is therefore written in small batches and shown to Frank.** Do
not generate a corpus of lessons and ask him to review it. Write a few, get the
reaction, and let the reaction become the exemplar set.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:46cd31e7 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

## The nine locked decisions

Locked by Frank 2026-10-29 and 10-30. Full reasoning in the MemPalace `orbis`
wing, `decisions` room.

    D1  a fresh repo, Chiron stays as it is
    D2  Python
    D3  Frank is the sole audience
    D4  SIZE IS A DESCRIPTION, NOT A NUMBER
    D5  infrastructure is in scope, and the LEARNING ENVIRONMENT is the hard half
    D6  lessons need a prose spec, and must carry charts, diagrams or tables
    D7  the name is ORBIS
    D8  a website, not PDFs
    D9  start from the RUNTIME, not the generator

**D4 is the one most often got wrong.** Frank's words were "what would too big
LOOK LIKE", and an agent turned both bounds into thresholds. A correct answer
can always carry redundant state, so there is no principled numeric ceiling,
and what too-big proxies for is representation-dependent. The FLOOR survives
being numeric better than the ceiling does.

**D8 follows from the pedagogy and is not a presentation preference.** Per-line
spoiler reveal cannot be done on paper, and a page can record that the click
happened. That click is the commitment step the design needs, because the
benefit of a reveal is the attempt that preceded it rather than its accuracy,
and because three capture surfaces in the predecessor project were specified and
left empty when they asked the learner to record something. A page records as a
side effect of reading.

**MKDOCS IS NOT INSTALLED on this box.** That is why the predecessor carries a
`--skip-docs` flag. Prefer plain Python emitting HTML.

## What this does not solve, stated so nobody rediscovers it

**Equivalent mutations.** A break that changes nothing observable teaches
nothing, and detecting that in general is undecidable. The gate catches the
pairs the reference cannot tell apart, which is a floor rather than a solution.

**Mutations worth making.** A break nobody would write is a contrived exercise
wearing a verdict. Generatable is not the same as worth generating.

**The ill-structured skill.** An item with an oracle is well-structured by
construction, and well-structured and ill-structured problem solving load on
different predictors. Noticing that a task is underdetermined and going to ask
somebody is not gradeable by a mutation set, and it is the thing Frank does
best.

**Lesson sequencing.** Untouched, and probably the weakest link in the whole
design. For an arbitrary subject the system must produce an organized curriculum
from research, and the predecessor's evidence is that generating from a
construct inventory produces contrived artifacts. A curriculum generated from an
inventory is the same failure one level up.

**Whether the instrument mix should change as the learner progresses.** Nothing
does this. Completion problems measure d = +0.505 at low prior knowledge and
d = -0.428 at HIGH, so the thing that helps early hurts later.

## Session completion

Work is not complete until it is pushed.

1. File beads for anything that needs follow-up.
2. Run `scripts/test` and read the output FILE.
3. Close finished beads, update in-progress ones.
4. `git fetch` then `git merge --ff-only origin/main`, then `git push`.
   **Never `git pull --rebase` after a `--no-ff` merge**, which rewrites every
   SHA after it and leaves close reasons citing commits that no longer exist.
5. `git status` must show up to date with origin.
6. Hand off: capture the decision in a drawer in the `orbis` wing, and say what
   is owed.

`.beads/` is in the global gitignore, so the export needs `git add -f
.beads/issues.jsonl`, and `git add` and `git commit` must be SEPARATE calls
because the ignored-path warning exits non-zero and short-circuits a `&&`.

**Diff the beads export BY ID before overwriting**, never by line count. Parse
both files, key on id, print added, removed and changed.

**No commit trailers.** Neither `Co-Authored-By` nor `Claude-Session`.
