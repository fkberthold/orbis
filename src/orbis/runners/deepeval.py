"""The DeepEval runner: a test_*.py against one environment, and its cell.

Everything here is about DeepEval and its uv workspace: staging a test file
where `deepeval` resolves, putting the environment's app on the import path,
the `deepeval test run` call, the junit report and the run file DeepEval
writes, and the commands the page shows beside the app.

The app is a Python module rather than a page, so an environment is a copy of
its directory on PYTHONPATH. Nothing is served, and nothing a run starts may
reach a model or Confident AI. The keys are blanked, telemetry and dotenv are
switched off, and where the box allows it the run gets a network namespace of
its own with no network in it.

A judged run is the one exception, and it's a narrow one. It keeps the empty
network namespace and gets a Unix socket to the judge bridge in judge.py,
which forwards chat completions to Poe and nothing else. The pytest plugin in
judge_plugin/ pins every metric's judge to that socket.
"""

import ast
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from .. import verdict
from ..environment import MutationError, materialize
from . import Run, TestOutcome, classify, judge

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent / "judge_plugin"

RUN_TIMEOUT_S = 300
SOURCE_GLOB = "test_*.py"
RUN_FILE = pathlib.Path(".deepeval") / ".latest_run_full.json"
KEPT_RUN = "latest_run_full.json"

# Set on every run, so a key in the shell or a .env file can't reach a model.
QUIET = {
    "DEEPEVAL_TELEMETRY_OPT_OUT": "YES",
    "DEEPEVAL_DISABLE_DOTENV": "1",
    "OPENAI_API_KEY": "",
    "CONFIDENT_API_KEY": "",
    # The judge's key stays with the bridge outside the run, so a test that
    # prints its environment prints no key.
    judge.KEY_VARIABLE: "",
}


def sources(directory):
    """The test files in a directory, sorted, which is how candidates are found."""
    return sorted(pathlib.Path(directory).glob(SOURCE_GLOB))


def prepare():
    """The command a run starts under, which cuts it off from the network.

    `unshare -rn` gives the run a namespace with only a loopback in it, so a
    metric that tries to call out fails where it stands. A box without it
    still has the blanked keys, and that's the weaker of the two.
    """
    if shutil.which("unshare"):
        probe = subprocess.run(
            ["unshare", "-rn", "true"], capture_output=True, check=False
        )
        if probe.returncode == 0:
            return ["unshare", "-rn"]
    return []


def _parse_junit(report):
    """Each pytest test as (name, outcome, message), or None when unusable."""
    if not report.is_file():
        return None
    try:
        tree = ET.parse(report)
    except ET.ParseError:
        return None
    found = []
    for case in tree.iter("testcase"):
        kind, message = verdict.PASS, ""
        for child in case:
            if child.tag == "failure":
                kind, message = verdict.FAIL, child.get("message") or ""
                break
            if child.tag in ("error", "skipped"):
                kind, message = verdict.ERROR, child.get("message") or child.tag
                break
        found.append((case.get("name") or "?", kind, message.strip()))
    return found


def _read_run(path):
    """DeepEval's test cases by name, each with the metrics it measured."""
    try:
        data = json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return {
        case.get("name", "?"): case.get("metricsData") or []
        for case in data.get("testCases") or []
    }


def _outcomes(tests, cases):
    """One outcome per metric a test measured, and one per test that measured none.

    A test that raised before assert_test never reaches DeepEval's run file,
    so pytest's report is the list of tests and the run file fills in what
    each one measured. A metric's own verdict is what tells two breaks of the
    same test case apart.
    """
    outcomes = []
    for name, kind, message in tests:
        measured = [
            TestOutcome(
                f"{name}: {metric.get('name', '?')}",
                verdict.PASS if metric.get("success") and not metric.get("error")
                else verdict.FAIL,
                metric.get("error") or metric.get("reason") or "",
                **_judged_score(metric),
            )
            for metric in cases.get(name, [])
        ]
        outcomes += measured
        # A test that measured nothing is its own outcome. So is one that
        # failed with every metric passing, which a plain assert after
        # assert_test does, or the failure would vanish from the vector.
        if not measured or (
            kind != verdict.PASS and all(o.outcome == verdict.PASS for o in measured)
        ):
            outcomes.append(TestOutcome(name, kind, message))
    outcomes.sort(key=lambda outcome: outcome.name)
    return outcomes


def _judged_score(metric):
    """A judged metric's score and threshold, as TestOutcome takes them.

    The run file names an evaluationModel only for a metric a judge scored. A
    metric decided in code gets nothing here, since its 0 or 1 isn't a
    measurement that can drift.
    """
    if not metric.get("evaluationModel") or metric.get("score") is None:
        return {}
    return {"scores": [float(metric["score"])],
            "threshold": float(metric.get("threshold") or 0)}


def has_assert_statement(source):
    """Whether the file holds a plain assert, the channel the run file can't see.

    DeepEval only records metrics, so `assert answer(q) != ""` checks something
    and leaves no trace of it. A file that won't parse counts as asserting
    nothing, and it won't have reached a verdict anyway.
    """
    try:
        tree = ast.parse(pathlib.Path(source).read_text())
    except (OSError, SyntaxError, ValueError):
        return False
    return any(isinstance(node, ast.Assert) for node in ast.walk(tree))


def _first_error(output):
    """The first line of pytest's output that names an exception, without colors."""
    lines = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output).splitlines()
    for line in lines:
        if re.match(r"E\s+\w+(Error|Exception)\b", line):
            return line[1:].strip()[:200]
    for line in lines:
        if "Error" in line:
            return line.strip()[:200]
    return ""


def run(candidate, app_dir, patch, environment_name, workspace, prepared,
        keep_dir=None, timeout=RUN_TIMEOUT_S, judged=False):
    """Execute candidate against one environment and return a Run.

    prepared is what prepare() returned, the command a run starts under. A
    judged run loads the plugin that pins the judge and gets the socket to it.
    """
    candidate = pathlib.Path(candidate).resolve()
    workspace = pathlib.Path(workspace).resolve()
    work = pathlib.Path(
        keep_dir if keep_dir else tempfile.mkdtemp(prefix="orbis-run-")
    )
    work.mkdir(parents=True, exist_ok=True)
    app = work / "app"
    report = work / "report.xml"

    runs = workspace / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    # The stage is the run's working directory too, because DeepEval writes
    # its run file under the directory it starts in. A stage per run means a
    # run file left by another run can't be read as this one's.
    stage = pathlib.Path(tempfile.mkdtemp(prefix="run-", dir=runs))
    try:
        try:
            materialize(app_dir, patch, app)
        except MutationError as problem:
            return Run(environment_name, verdict.DID_NOT_RUN, [], 0, str(problem))

        shutil.copy(candidate, stage / candidate.name)
        environment = {
            key: value for key, value in os.environ.items()
            # Set when the gate itself runs under uv, and it names Orbis's
            # environment rather than the workspace's.
            if key != "VIRTUAL_ENV"
        }
        environment.update(QUIET)
        environment["PYTHONPATH"] = str(app)
        environment["UV_OFFLINE"] = "1"
        plugin = []
        if judged:
            bridge = judge.bridge()
            environment["PYTHONPATH"] += os.pathsep + str(PLUGIN_DIR)
            environment["ORBIS_JUDGE_SOCKET"] = bridge.socket
            environment["ORBIS_JUDGE_MODEL"] = bridge.model
            plugin = ["-p", "orbis_judge"]
        # No -c. DeepEval's cache keys on the test case alone, not the judge or
        # its version, so a cached run would repeat a verdict rather than
        # measure it again, and the repeats are what show a verdict holds.
        command = [
            *prepared, "uv", "run", "--project", str(workspace), "--frozen",
            "--quiet", "deepeval", "test", "run", candidate.name,
            f"--junitxml={report}", "-p", "no:cacheprovider", *plugin,
        ]
        try:
            finished = subprocess.run(
                command, cwd=stage, env=environment, capture_output=True,
                text=True, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired:
            return Run(
                environment_name, verdict.DID_NOT_RUN, [], 0,
                f"the test run did not finish inside {timeout}s",
            )

        tests = _parse_junit(report)
        cases = _read_run(stage / RUN_FILE)
        if keep_dir and (stage / RUN_FILE).is_file():
            shutil.copy(stage / RUN_FILE, work / KEPT_RUN)
        outcomes = _outcomes(tests, cases) if tests else None
        measured = sum(len(metrics) for metrics in cases.values())
        cell, note = classify(
            finished.returncode, outcomes, measured, has_assert_statement(candidate)
        )
        if cell == verdict.SILENT:
            note = f"passed, {measured} metric(s) measured"
        if cell == verdict.DID_NOT_RUN:
            cause = _first_error(finished.stdout + finished.stderr)
            if cause:
                note = f"{note}: {cause}"
        return Run(environment_name, cell, outcomes or [], measured, note)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        if keep_dir is None:
            shutil.rmtree(work, ignore_errors=True)


def judge_used():
    """What the judge was asked for so far in this process, or None."""
    return judge.used()


def kept_traces(directory):
    """The run file each kept run left, which is DeepEval's record of it."""
    return sorted(pathlib.Path(directory).rglob(KEPT_RUN))


def mine_name(item_name):
    """Where the learner's own test file goes, named so pytest collects it."""
    slug = item_name.rsplit("/", 1)[-1].replace("-", "_")
    return f"mine/test_{slug}.py"


def _words(name):
    """'test_known_order' as 'known order', 'NamesTheOrder' as 'names the order'."""
    name = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", name.removeprefix("test_"))
    return name.replace("_", " ").strip().lower()


def margin_for(text):
    """Say roughly what kind of line this is, without saying what it does."""
    line = text.strip()
    test = re.match(r"def (test_\w+)", line)
    if test:
        return "a test: " + _words(test.group(1))
    helper = re.match(r"(?:async\s+)?def (\w+)", line)
    # A metric of your own has the same four methods every time, so they get
    # named for their job in it rather than read as helpers.
    for method, note in (
        ("__init__", "set the metric up"),
        ("measure", "score one test case"),
        ("a_measure", "the async form DeepEval calls"),
        ("__name__", "the name the report shows"),
    ):
        if helper and helper.group(1) == method:
            return note
    if helper:
        return "a helper: " + _words(helper.group(1))
    if re.match(r"class \w+\(BaseMetric\)", line):
        return "a metric of your own: " + _words(line[6:line.index("(")])
    if re.match(r"class \w+\(BaseModel\)", line):
        return "the shape the answer must have"
    if line.startswith(("import ", "from ")):
        return "imports"
    if line.startswith(("#", '"""')):
        return "a note on why"
    if line.startswith("@pytest.mark.parametrize"):
        return "one test per question"
    if line.startswith("assert_test("):
        return "check the result"
    if "LLMTestCase(" in line:
        return "build a test case"
    return ""


def app_lead():
    """The words either side of the app's link, at the top of the app panel."""
    return (
        "The real bot's source is at ",
        (", recordings and all. Print its answers, call it from a Python prompt,"
         " and write your tests against what it says."),
    )


def app_commands(url, mine, app, workspace):
    """What the learner runs against the real app, as (what it's for, command).

    The commands run from the workspace, and the real app's directory has to
    be on PYTHONPATH there for `from order_status import answer` to resolve.
    """
    shown = os.path.relpath(app, workspace)
    modules = sorted(p.name for p in pathlib.Path(app).glob("*.py"))
    show = f"uv run python {shown}/{modules[0]}" if modules else f"ls {shown}"
    return [
        ("print every recorded question and the answer it got", show),
        ("ask it questions from a Python prompt", f"PYTHONPATH={shown} uv run python"),
        ("run your tests against the real app",
         f"PYTHONPATH={shown} uv run deepeval test run {mine}"),
        ("read what the last run measured",
         "uv run python -m json.tool .deepeval/.latest_run_full.json"),
    ]


def trace_command(trace):
    """The command that prints one kept run file."""
    return f"uv run python -m json.tool {trace}"
