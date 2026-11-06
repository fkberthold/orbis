# Checks that need no judge

Read with the docs pages
[metrics-introduction](https://deepeval.com/docs/metrics-introduction),
[metrics-exact-match](https://deepeval.com/docs/metrics-exact-match),
[metrics-pattern-match](https://deepeval.com/docs/metrics-pattern-match) and
[metrics-json-correctness](https://deepeval.com/docs/metrics-json-correctness).

Most of DeepEval's metrics ask a model for their score. A few don't, and I'd
reach for those first. They're free, they're exact, and they give the same
answer on every run, so a failure means the app changed. Much of what an LLM
app sends back has structure a page depends on: JSON, a label, an id, a date.
A check in code covers that, and the judge is for what code can't see.

## A whole suite

Here's the hold-desk bot from step 1 with a third question, about a book the
library doesn't hold, and a suite that checks every answer in code.

```python
# mine/holds.py
"""A library's hold-desk bot. It answers in JSON, and its answers are recorded."""

RECORDED = {
    "Is my hold on Dune ready?":
        '{"title": "Dune", "status": "ready", "pickup_by": "2026-11-20"}',
    "Is my hold on Emma ready?":
        '{"title": "Emma", "status": "waiting", "pickup_by": null}',
    "Is my hold on Zorba ready?":
        '{"title": "Zorba", "status": "no_hold", "pickup_by": null}',
}


def answer(question: str) -> str:
    return RECORDED[question]
```

```python
# mine/test_holds.py
import json
import re
from typing import Literal

import pytest
from deepeval import assert_test
from deepeval.metrics import BaseMetric, JsonCorrectnessMetric, PatternMatchMetric
from deepeval.test_case import LLMTestCase
from holds import answer
from pydantic import BaseModel


class Hold(BaseModel):
    title: str
    status: Literal["ready", "waiting", "no_hold"]
    pickup_by: str | None


class NamesTheBook(BaseMetric):
    """The answer is about the book the question asked about."""

    def __init__(self):
        self.threshold = 1.0

    def measure(self, test_case, *args, **kwargs):
        asked = re.search(r"hold on (\w+)", test_case.input).group(1)
        said = json.loads(test_case.actual_output).get("title")
        self.score = 1.0 if said == asked else 0.0
        self.reason = f"asked about {asked}, the answer is about {said}"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    @property
    def __name__(self):
        return "Names The Book"


def fits_the_schema():
    return JsonCorrectnessMetric(
        expected_schema=Hold, include_reason=False, eval_mode="system_one"
    )


DATED = r'(?s).*"pickup_by"\s*:\s*"\d{4}-\d{2}-\d{2}".*'
UNDATED = r'(?s).*"pickup_by"\s*:\s*null.*'


@pytest.mark.parametrize("question, date", [
    ("Is my hold on Dune ready?", DATED),
    ("Is my hold on Emma ready?", UNDATED),
    ("Is my hold on Zorba ready?", UNDATED),
])
def test_hold(question, date):
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [fits_the_schema(), NamesTheBook(), PatternMatchMetric(pattern=date)])
```

```bash
uv run deepeval test run mine/test_holds.py
```

Each case gets three checks in one `assert_test`: the answer fits the schema,
it's about the right book, and its date is there or absent as it should be.
Three cases times three metrics is nine verdicts, and each one can fail on its
own.

## Exact match, and the trap in it

`ExactMatchMetric` compares `actual_output` to `expected_output`, both
stripped, and passes only on equality. That's right for an output with one
correct form, like a label from a classifier. On text it's a trap, because an
LLM app phrases the same right answer more than one way, and a test pinned to
one phrasing fails the next run of a healthy app.

This course's real apps behave that way on purpose. Each one has several
versions that differ only in ways the rules allow, such as key order or
spacing in JSON, and your suite has to pass all of them. A test that hardcodes
one recorded string fails the real app, and the gate rejects it on G1.

## Pattern match

`PatternMatchMetric` uses `re.fullmatch`, so the pattern has to cover the
whole output. That's why the patterns above open with `(?s).*` and end with
`.*`. A pattern that only describes the part you care about never matches.
`ignore_case=True` is there when you need it.

## JSON correctness, and the judge it builds anyway

`JsonCorrectnessMetric` checks the output against a pydantic model, so it
holds however the JSON is spaced or ordered. A pydantic model ignores extra
keys by default, which suits an app that might add a field.

Its default mode builds an OpenAI judge when the metric is created, to write
the reason for a failure, even with `include_reason=False`. With no OpenAI key
that fails before any test runs. `eval_mode="system_one"` decides the score in
code and builds no judge, which is what you want here. Measured 2026-11-06 on
deepeval 4.3.2.

## A metric of your own

A rule with no ready-made metric gets a `BaseMetric` subclass. It sets
`threshold` when it's made, and `measure` sets `score`, `reason` and `success`
and returns the score. `a_measure` is the async form, and for a check in plain
Python it can just call `measure`. The `__name__` property is the name the
results table and run file show. Step 7 comes back to custom metrics, with a
judge inside.

I'd write the reason as carefully as the check. When a test fails at work, the
reason is what a teammate reads first, and "asked about Dune, the answer is
about Emma" says what broke without opening the code.

## Practice

**Item 01, the order-status bot.** Its rules are in its task, and its real app
runs in several versions, so a check pinned to one string won't pass.

Before you write it, predict, then check: in the suite above, change the Zorba
answer's status to `"waiting"`. Which of the nine verdicts fail? Run it and
see.
