"""A runner is what one subject's tooling needs, kept out of the engine.

The gate, the verdict and the page don't know how a candidate gets run. They
know it lands in one of four cells against each environment, and that the
page has a few commands to show beside the app. A runner supplies those for
its subject, and subject.toml names which one a subject uses.

What a runner module provides, as the gate and page call it today:

    sources(directory)             the candidate files in a directory, sorted
    prepare()                      what every run needs set up first, resolved once
    run(candidate, app_dir, patch, environment_name, workspace, prepared,
        keep_dir=None, judged=False)
                                   one candidate against one environment, as a Run.
                                   judged is only passed to a runner whose item
                                   says it's judged, so only DeepEval takes it
    kept_traces(directory)         the traces a kept run left, for the page to list
    mine_name(item_name)           where the learner's own file goes in the workspace
    margin_for(text)               what kind of line one line of the answer is
    app_lead()                     the words either side of the app's link
    app_commands(url, mine, app, workspace)
                                   (what it's for, command) rows for the app panel
    trace_command(trace)           the command that opens one kept trace
"""

import dataclasses
import importlib

from .. import verdict

# The real app's environment name, beside each mutation's patch stem. A real
# variant is named after it, as real+<the variant's patch stem>.
REAL = "real"


def is_real(environment_name):
    """Whether a run was against the real app or one of its real variants."""
    return environment_name == REAL or environment_name.startswith(REAL + "+")

# Keyed by the runner name subject.toml gives. Imported on first use, so a
# subject's tooling is only loaded when that subject is.
_RUNNERS = {
    "playwright": "orbis.runners.playwright",
    "deepeval": "orbis.runners.deepeval",
}


def get(name):
    """The runner module subject.toml names."""
    try:
        return importlib.import_module(_RUNNERS[name])
    except KeyError:
        raise SystemExit(
            f"no runner called {name!r}. Known: {', '.join(sorted(_RUNNERS))}"
        ) from None


@dataclasses.dataclass
class TestOutcome:
    name: str
    outcome: str
    message: str = ""
    # A judged metric's score, one per repeat, and the line it had to clear.
    # Both stay empty for a check decided in code, which has no score worth
    # a margin.
    scores: list = dataclasses.field(default_factory=list)
    threshold: float | None = None


@dataclasses.dataclass
class Run:
    environment: str
    cell: str
    tests: list
    expects: int
    note: str = ""

    @property
    def vector(self):
        return tuple(test.outcome for test in self.tests)

    @property
    def vector_text(self):
        return " ".join(self.vector) if self.tests else "(none)"


def classify(returncode, outcomes, expects, asserted_in_source):
    """The cell one run lands in, and a note saying why.

    expects is how many assertions the run was seen to execute, by whatever
    channel the runner reads. asserted_in_source is the second channel, a scan
    of the file for an assertion the first can't see. Either one keeps a pass
    out of vacuous.
    """
    if outcomes is None or not outcomes:
        return verdict.DID_NOT_RUN, f"the test run exited {returncode} with no usable report"
    if any(outcome.outcome == verdict.ERROR for outcome in outcomes):
        return verdict.DID_NOT_RUN, "a test errored rather than reaching a verdict"
    if any(outcome.outcome == verdict.FAIL for outcome in outcomes):
        failed = [o.name for o in outcomes if o.outcome == verdict.FAIL]
        return verdict.CATCHES, "failed: " + ", ".join(failed)
    if expects == 0 and not asserted_in_source:
        return verdict.VACUOUS, "passed without asserting anything"
    return verdict.SILENT, f"passed, {expects} assertion(s) executed"
