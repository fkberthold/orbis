# A candidate that can't be collected, because the name it imports isn't in
# the bot. No test reaches a verdict, so every cell reads did-not-run.
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from order_status import ask


def test_known_order():
    question = "Where is order A-1042?"
    case = LLMTestCase(input=question, actual_output=ask(question))
    assert_test(case, [PatternMatchMetric(pattern=r"(?s).*A-1042.*")])
