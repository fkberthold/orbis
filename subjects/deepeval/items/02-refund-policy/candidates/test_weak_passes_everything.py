# A candidate that checks every answer is on topic, with no judge at all. Each
# break still talks about a refund or the customer's money, so the pattern
# holds everywhere and the run is silent against every break.
import pytest
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from refund_policy import QUESTIONS, answer


@pytest.mark.parametrize("question", QUESTIONS)
def test_answer_is_about_the_refund(question):
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [PatternMatchMetric(pattern=r"(?is).*\b(refund\w*|money)\b.*")])
