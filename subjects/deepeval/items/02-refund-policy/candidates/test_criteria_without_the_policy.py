# A candidate that hands the judge a one-line criteria and never shows it the
# policy. It reads like a real check, and the judge does score every answer.
# But the judge can only weigh an answer against what it's given, so a
# 60-day window sounds as reasonable as a 30-day one, and so does approving
# a $650 refund. Measured 2026-11-06 on gpt-5.4-mini: the 60-day answer
# scored between 0.8 and 1.0 in every run. So G2 rejects it, silent on the
# invented window and on every other break.
#
# Without pinned steps it wobbles, too. In one selfcheck the real sofa answer
# scored 0.7 in one run of three, so that copy read did-not-run and G1
# rejected it as well. Pinned steps scored the same answers 1.0 every time.
import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from refund_policy import QUESTIONS, answer


def answers_well():
    return GEval(
        name="Answers Well",
        criteria=(
            "Determine whether the actual output correctly and helpfully "
            "answers the customer's refund question."
        ),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        threshold=0.75,
    )


@pytest.mark.parametrize("question", QUESTIONS)
def test_answer(question):
    case = LLMTestCase(input=question, actual_output=answer(question))
    assert_test(case, [answers_well()])
