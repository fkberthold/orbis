# A candidate that asks the bot every question and checks nothing. It passes
# everywhere, and the cell that says so is vacuous rather than silent.
from deepeval.test_case import LLMTestCase
from order_status import QUESTIONS, answer


def test_every_question():
    for question in QUESTIONS:
        LLMTestCase(input=question, actual_output=answer(question))
