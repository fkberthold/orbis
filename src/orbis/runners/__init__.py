"""A runner is what one subject's tooling needs, kept out of the engine.

The gate, the verdict and the page don't know how a candidate gets run. They
know it lands in one of four cells against each environment, and that the
page has a few commands to show beside the app. A runner supplies those for
its subject, and subject.toml names which one a subject uses.

What a runner module provides, as the gate and page call it today:

    sources(directory)             the candidate files in a directory, sorted
    prepare()                      what every run needs set up first, resolved once
    run(candidate, app_dir, patch, environment_name, workspace, prepared,
        keep_dir=None)             one candidate against one environment, as a Run
    kept_traces(directory)         the traces a kept run left, for the page to list
    mine_name(item_name)           where the learner's own file goes in the workspace
    margin_for(text)               what kind of line one line of the answer is
    app_commands(url, mine)        (what it's for, command) rows for the app panel
    trace_command(trace)           the command that opens one kept trace
"""

import dataclasses
import importlib

# The real app's environment name, beside each mutation's patch stem.
REAL = "real"

# Keyed by the runner name subject.toml gives. Imported on first use, so a
# subject's tooling is only loaded when that subject is.
_RUNNERS = {
    "playwright": "orbis.runners.playwright",
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
