# A DeepEval suite is a pytest suite

Read with the docs pages
[getting-started](https://deepeval.com/docs/getting-started),
[evaluation-introduction](https://deepeval.com/docs/evaluation-introduction) and
[evaluation-test-cases](https://deepeval.com/docs/evaluation-test-cases). Skip
every section about logging in or Confident AI. Nothing in this course uses it.

Everything you know about pytest holds. Test files are `test_*.py`, and
fixtures, `parametrize` and markers work as they always have. Three things are
new. The thing under test hands back text. A test checks that text through
`assert_test` and a list of metrics, rather than a bare `assert`. And
`deepeval test run` wraps pytest and writes a results file you can read.

## A whole suite

Here's a small one for a library's hold-desk bot. In a real suite the bot
would be your app. In this course it's a module with its answers recorded, so
a run never calls a model to produce them.

```text
workspace/
├── pyproject.toml          pins deepeval==4.3.2, as requirements.txt would
├── uv.lock
└── mine/
    ├── holds.py            the app under test, beside the test for this example
    └── test_holds.py
```

```python
# mine/holds.py
"""A library's hold-desk bot. It answers in JSON, and its answers are recorded."""

RECORDED = {
    "Is my hold on Dune ready?":
        '{"title": "Dune", "status": "ready", "pickup_by": "2026-11-20"}',
    "Is my hold on Emma ready?":
        '{"title": "Emma", "status": "waiting", "pickup_by": null}',
}


def answer(question: str) -> str:
    return RECORDED[question]
```

```python
# mine/test_holds.py
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from holds import answer

DATED = r'(?s).*"pickup_by"\s*:\s*"\d{4}-\d{2}-\d{2}".*'


def test_a_ready_hold_has_a_pickup_date():
    question = "Is my hold on Dune ready?"
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [PatternMatchMetric(pattern=DATED)])


def test_a_waiting_hold_has_no_pickup_date():
    question = "Is my hold on Emma ready?"
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [PatternMatchMetric(pattern=r'(?s).*"pickup_by"\s*:\s*null.*')])
```

Run it from the workspace:

```bash
uv run deepeval test run mine/test_holds.py
```

The app sits beside the test here, so pytest's default import mode finds it.
A practice item keeps its app in its own folder, and the item's page gives the
`PYTHONPATH` that puts it in reach.

## The parts that are new

| part | what it is | the pytest idea it replaces |
|---|---|---|
| `LLMTestCase(input=..., actual_output=...)` | one exchange with the app, plus whatever a metric needs to judge it | the values you'd pass to `assert` |
| a metric | something that scores a test case from 0 to 1 against its `threshold` | the comparison inside `assert` |
| `assert_test(case, [metrics])` | runs every metric and raises `AssertionError` naming each one that fell short | `assert` itself |
| `deepeval test run` | pytest with DeepEval's plugin loaded, plus a results table and file | `pytest` |

A test case carries more fields than these two. `expected_output`,
`retrieval_context` and `context` are there for metrics that need them, and
steps 3 and 5 use them. A metric reads only the fields it was built to read.
So a test case can carry the right answer and still have nothing check it.

Put every metric for one case in one `assert_test`. It reads the same either
way, but DeepEval's cache keys on the test case and keeps one list of metrics
per case. Split them across tests and the cache never hits. That matters once
a judge is in the loop and every metric costs a call.

## `deepeval test run` against plain `pytest`

Plain `pytest` runs these tests too, and they pass or fail the same way. What
`deepeval test run` adds is the table of scores at the end and the run file,
`.deepeval/.latest_run_full.json`, rewritten on every run. Its flags are
pytest's plus a few of its own:

| flag | what it does |
|---|---|
| `-c` | reuse cached metric results for test cases that haven't changed |
| `-r N` | run every test case N times, which step 4 uses to watch a judge's scores move |
| `-n N` | run in N processes, through pytest-xdist |
| `-x` | stop at the first failure |
| `-i` | carry on past a metric that errors, rather than failing the test |

The run file is the record of what each metric decided:

```text
testCases[]
  name, input, actualOutput, success
  metricsData[]
    name, score, threshold, success, reason
    evaluationModel             only when a judge scored it
```

`reason` is the one to read when a test fails. For a deterministic metric it's
a line of plain text. For a judged one, from step 3 on, it's the judge's own
account of its score. A test that raises before `assert_test`, or never calls
it, doesn't appear in `testCases` at all, so the file alone can't tell you a
test ran.

## Practice

None graded. Run the suite above, then open the run file and find each
metric's score and reason. Then change the Dune answer's date to `20 Nov` and
run it again, before you open the file, say which test fails and what its
reason will say.
