"""The Playwright runner: a .spec.ts against one environment, and its cell.

Everything here is about Playwright and its node workspace: staging a spec
where `@playwright/test` resolves, the config each run gets, the npx call, the
junit report, the trace the vacuous cell is read from, the browsers nixpkgs
builds, and the commands the page shows beside the app. The gate and the page
reach all of it through the runner registry.

The question is never whether the candidate passes. A passing test proves
nothing, because a test that asserts a constant passes. The question is whether
the candidate discriminates, so every run here is one half of a comparison: the
candidate against the real app, and the candidate against each deliberate
break.
"""

import contextlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from .. import verdict
from ..environment import MutationError, Site, materialize
from . import Run, TestOutcome
from . import playwright_trace as tracing

RUN_TIMEOUT_S = 300
SOURCE_GLOB = "*.spec.ts"


def sources(directory):
    """The spec files in a directory, sorted, which is how candidates are found."""
    return sorted(pathlib.Path(directory).glob(SOURCE_GLOB))


def prepare():
    """Where Playwright's browsers live, which on NixOS is a store path.

    The binaries Playwright downloads for itself are not linked for NixOS, so
    the ones nixpkgs builds are the only ones that run here.
    """
    from_env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if from_env:
        return from_env
    built = subprocess.run(
        ["nix", "build", "--no-link", "--print-out-paths",
         "nixpkgs#playwright-driver.browsers"],
        capture_output=True, text=True, check=False,
    )
    if built.returncode != 0:
        raise SystemExit(
            "PLAYWRIGHT_BROWSERS_PATH is unset and nix could not build the "
            "browsers. Run: source env.sh"
        )
    return built.stdout.strip().splitlines()[-1]


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


def _first_error(output):
    """The first line of a test run's output that says Error, without colors."""
    for line in re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output).splitlines():
        if "Error" in line:
            return line.strip()[:200]
    return ""


def _classify(returncode, outcomes, expects, asserted_in_source):
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


@contextlib.contextmanager
def _staged(candidate, workspace, base_url, output, report):
    """Copy candidate into the workspace beside a config written for this run.

    The workspace is the subject's node workspace, where the learner's
    TypeScript runs. A spec has to sit inside it, or `import ... from
    '@playwright/test'` can't be resolved, so every run copies the candidate
    in rather than running it where it lies.

    The config pins everything the verdict depends on: the app's address, a
    trace for every test, one worker so runs don't race each other, no
    retries, and a junit report to read the outcomes from.
    """
    stage = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=_runs_dir(workspace)))
    try:
        shutil.copy(candidate, stage / candidate.name)
        config = stage / "playwright.config.ts"
        config.write_text(
            "import { defineConfig } from '@playwright/test';\n"
            "export default defineConfig({\n"
            f"  testDir: {json.dumps(str(stage))},\n"
            f"  testMatch: {json.dumps(candidate.name)},\n"
            f"  outputDir: {json.dumps(str(output))},\n"
            "  workers: 1,\n"
            "  retries: 0,\n"
            f"  reporter: [['junit', {{ outputFile: {json.dumps(str(report))} }}]],\n"
            f"  use: {{ baseURL: {json.dumps(base_url)}, trace: 'on', browserName: 'chromium' }},\n"
            "});\n"
        )
        yield config
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _runs_dir(workspace):
    runs = pathlib.Path(workspace) / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    return runs


def run(candidate, app_dir, patch, environment_name, workspace, prepared,
        keep_dir=None, timeout=RUN_TIMEOUT_S):
    """Execute candidate against one environment and return a Run.

    prepared is what prepare() returned, the browsers path.
    """
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
        environment["PLAYWRIGHT_BROWSERS_PATH"] = str(prepared)
        environment["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

        with Site(served) as site, _staged(candidate, workspace, site.base_url, output, report) as config:
            command = ["npx", "playwright", "test", "--config", str(config)]
            try:
                finished = subprocess.run(
                    command,
                    cwd=workspace,
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
                    f"the test run did not finish inside {timeout}s",
                )

        outcomes = _parse_junit(report)
        expects = tracing.expect_calls_under(output)
        asserted = tracing.has_assert_statement(candidate)
        cell, note = _classify(returncode, outcomes, expects, asserted)
        if cell == verdict.DID_NOT_RUN and not outcomes:
            # Name the cause. A file that won't load is the commonest way to
            # get here, and the bare exit code says nothing about which line.
            cause = _first_error(finished.stdout + finished.stderr)
            if cause:
                note = f"{note}: {cause}"
        return Run(environment_name, cell, outcomes or [], expects, note)
    finally:
        if keep_dir is None:
            shutil.rmtree(work, ignore_errors=True)


def kept_traces(directory):
    """Every trace a kept run left under directory, for the page to list."""
    return sorted(pathlib.Path(directory).rglob("trace.zip"))


def mine_name(item_name):
    """Where the learner's own spec for an item goes, inside the workspace."""
    return f"mine/{item_name.rsplit('/', 1)[-1]}.spec.ts"


def _words(name):
    """'reserveSucceeds' or 'reserve_succeeds' as 'reserve succeeds'."""
    name = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", name)
    return name.replace("_", " ").strip().lower()


def margin_for(text):
    """Say roughly what kind of line this is, without saying what it does."""
    line = text.strip()
    test = re.match(r"test(?:\.\w+)?\(\s*['\"`](.+?)['\"`]", line)
    if test:
        return "a test: " + test.group(1)
    helper = re.match(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
    if helper:
        return "a helper: " + _words(helper.group(1))
    if line.startswith("import "):
        return "imports"
    if line.startswith(("//", "/*", "*")):
        return "a note on why"
    line = line.removeprefix("await ")
    if line.startswith("expect("):
        return "check the result"
    for call, note in (
        ("page.goto", "open the page"),
        ("page.fill", "fill a field"),
        ("page.selectOption", "pick an option"),
        ("page.dblclick", "double click"),
        ("page.click", "click"),
        ("page.route", "stub the network"),
        ("page.once", "handle a dialog"),
        ("page.on", "handle an event"),
        ("page.goBack", "go back"),
        ("page.waitFor", "wait"),
    ):
        if line.startswith(call):
            return note
    if re.match(r"\w+\(page", line):
        return "use the helper"
    return ""


def app_commands(url, mine):
    """What the learner runs against the live app, as (what it's for, command)."""
    run_mine = f"BASE_URL={url} npx playwright test {mine}"
    return [
        ("record clicks as test code, and pick up selectors",
         f"npx playwright codegen --target playwright-test {url}"),
        ("run your tests step by step, with the page beside them", f"{run_mine} --ui"),
        ("watch your tests run in a browser", f"{run_mine} --headed"),
        ("pause on each action with the inspector", f"{run_mine} --debug"),
    ]


def trace_command(trace):
    """The command that opens one kept trace in the trace viewer."""
    return f"npx playwright show-trace {trace}"
