"""Run one candidate against one environment and say which cell it landed in.

The question is never whether the candidate passes. A passing test proves
nothing, because a test that asserts a constant passes. The question is whether
the candidate discriminates, so every run here is one half of a comparison: the
candidate against the real app, and the candidate against each deliberate
break.
"""

import dataclasses
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from . import tracing, verdict
from .environment import MutationError, Site, materialize

REAL = "real"
RUN_TIMEOUT_S = 300


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


def _short_name(raw):
    """Drop the browser parameter pytest appends, keeping the test's own name."""
    return raw.split("[", 1)[0]


def _parse_junit(report):
    """Read per-test outcomes, or None when the report is unusable."""
    if not report.is_file():
        return None
    try:
        tree = ET.parse(report)
    except ET.ParseError:
        return None

    outcomes = []
    for case in tree.iter("testcase"):
        kind = verdict.PASS
        message = ""
        for child in case:
            if child.tag == "failure":
                kind = verdict.FAIL
                message = (child.get("message") or "").strip()
                break
            if child.tag == "error":
                kind = verdict.ERROR
                message = (child.get("message") or "").strip()
                break
            if child.tag == "skipped":
                kind = verdict.ERROR
                message = "skipped"
                break
        outcomes.append(
            TestOutcome(_short_name(case.get("name") or "?"), kind, message)
        )
    outcomes.sort(key=lambda outcome: outcome.name)
    return outcomes


def _classify(returncode, outcomes, expects, asserted_in_source):
    if outcomes is None or not outcomes:
        return verdict.DID_NOT_RUN, f"pytest exit {returncode}, no usable report"
    if any(outcome.outcome == verdict.ERROR for outcome in outcomes):
        return verdict.DID_NOT_RUN, "a test errored rather than reaching a verdict"
    if any(outcome.outcome == verdict.FAIL for outcome in outcomes):
        failed = [o.name for o in outcomes if o.outcome == verdict.FAIL]
        return verdict.CATCHES, "failed: " + ", ".join(failed)
    if expects == 0 and not asserted_in_source:
        return verdict.VACUOUS, "passed without asserting anything"
    return verdict.SILENT, f"passed, {expects} assertion(s) executed"


def run(candidate, app_dir, patch, environment_name, browsers_path,
        keep_dir=None, timeout=RUN_TIMEOUT_S):
    """Execute candidate against one environment and return a Run."""
    candidate = pathlib.Path(candidate).resolve()
    work = pathlib.Path(
        keep_dir if keep_dir else tempfile.mkdtemp(prefix="orbis-run-")
    )
    work.mkdir(parents=True, exist_ok=True)
    served = work / "app"
    output = work / "artifacts"
    report = work / "report.xml"

    try:
        try:
            materialize(app_dir, patch, served)
        except MutationError as problem:
            return Run(environment_name, verdict.DID_NOT_RUN, [], 0, str(problem))

        environment = dict(os.environ)
        environment["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
        environment["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

        with Site(served) as site:
            command = [
                sys.executable, "-m", "pytest", str(candidate),
                "-p", "no:cacheprovider",
                "--base-url", site.base_url,
                "--browser", "chromium",
                "--tracing", "on",
                "--output", str(output),
                "--junit-xml", str(report),
                "-q",
            ]
            try:
                finished = subprocess.run(
                    command,
                    cwd=work,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                returncode = finished.returncode
            except subprocess.TimeoutExpired:
                return Run(
                    environment_name, verdict.DID_NOT_RUN, [], 0,
                    f"pytest did not finish inside {timeout}s",
                )

        outcomes = _parse_junit(report)
        expects = tracing.expect_calls_under(output)
        asserted = tracing.has_assert_statement(candidate)
        cell, note = _classify(returncode, outcomes, expects, asserted)
        return Run(environment_name, cell, outcomes or [], expects, note)
    finally:
        if keep_dir is None:
            shutil.rmtree(work, ignore_errors=True)
