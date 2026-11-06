# A candidate that can't be collected, because the name it imports isn't in
# the bot. No test reaches a verdict, so every cell reads did-not-run.
from deepeval import assert_test
from deepeval.metrics import PatternMatchMetric
from deepeval.test_case import LLMTestCase
from refund_policy import QUESTIONS, reply


def test_first_question():
    question = QUESTIONS[0]
    case = LLMTestCase(input=question, actual_output=reply(question))
    assert_test(case, [PatternMatchMetric(pattern=r"(?s).*refund.*")])
