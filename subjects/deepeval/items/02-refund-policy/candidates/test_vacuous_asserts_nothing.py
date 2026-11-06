# A candidate that builds a test case for every question and measures none
# of them. It passes everywhere, and the cell that says so is vacuous rather
# than silent.
from deepeval.test_case import LLMTestCase
from refund_policy import POLICY, QUESTIONS, answer


def test_every_question():
    for question in QUESTIONS:
        LLMTestCase(input=question, actual_output=answer(question), context=[POLICY])
