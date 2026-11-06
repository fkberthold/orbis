import json
import re
from typing import Literal

import pytest
from deepeval import assert_test
from deepeval.metrics import BaseMetric, JsonCorrectnessMetric, PatternMatchMetric
from deepeval.test_case import LLMTestCase
from order_status import answer
from pydantic import BaseModel

KNOWN = [
    "Where is order A-1042?",
    "When will order A-1077 arrive?",
    "Has order A-1103 been delivered yet?",
]
UNKNOWN = "Where is order A-2000?"


class OrderStatus(BaseModel):
    order_id: str
    status: Literal["processing", "shipped", "delivered", "not_found"]
    eta: str | None


def parsed(output):
    """The answer as a dict, or an empty one when it isn't a JSON object."""
    try:
        value = json.loads(output)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


class NamesTheOrder(BaseMetric):
    """The answer's order_id is the order the question asked about."""

    def __init__(self):
        self.threshold = 1.0

    def measure(self, test_case, *args, **kwargs):
        asked = re.search(r"A-\d+", test_case.input).group()
        said = parsed(test_case.actual_output).get("order_id")
        self.score = 1.0 if said == asked else 0.0
        self.reason = f"asked about {asked}, the answer names {said}"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    @property
    def __name__(self):
        return "Names The Order"


class NothingInvented(BaseMetric):
    """An order that doesn't exist gets not_found and no date."""

    def __init__(self):
        self.threshold = 1.0

    def measure(self, test_case, *args, **kwargs):
        said = parsed(test_case.actual_output)
        honest = said.get("status") == "not_found" and said.get("eta", "") is None
        self.score = 1.0 if honest else 0.0
        self.reason = f"status {said.get('status')!r}, eta {said.get('eta')!r}"
        self.success = self.score >= self.threshold
        return self.score

    async def a_measure(self, test_case, *args, **kwargs):
        return self.measure(test_case)

    @property
    def __name__(self):
        return "Nothing Invented"


def fits_the_schema():
    # system_one decides this metric in code, so it builds no judge and
    # needs no API key. The schema ignores key order, spacing and extra keys.
    return JsonCorrectnessMetric(
        expected_schema=OrderStatus, include_reason=False, eval_mode="system_one"
    )


# The eta is matched where it sits in the JSON text, so key order and spacing
# don't move it. PatternMatchMetric matches the whole output, hence the .*
ISO_ETA = r'(?s).*"eta"\s*:\s*"\d{4}-\d{2}-\d{2}".*'


@pytest.mark.parametrize("question", KNOWN, ids=["A-1042", "A-1077", "A-1103"])
def test_known_order(question):
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [fits_the_schema(), NamesTheOrder(), PatternMatchMetric(pattern=ISO_ETA)])


def test_unknown_order():
    case = LLMTestCase(input=UNKNOWN, actual_output=answer(UNKNOWN))
    assert_test(case, [fits_the_schema(), NamesTheOrder(), NothingInvented()])
