# A candidate that runs a real metric on every answer and catches nothing. Each
# break still answers with braces round it, so the pattern holds everywhere.
import pytest
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from order_status import QUESTIONS, answer


@pytest.mark.parametrize("question", QUESTIONS)
def test_answers_in_braces(question):
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [PatternMatchMetric(pattern=r"(?s)\{.*\}")])
