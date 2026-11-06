import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from refund_policy import POLICY, QUESTIONS, answer

# The steps are pinned rather than left to the judge. With criteria alone,
# GEval asks the judge to write its own steps on every run, so the test
# changes under you between runs. Pinned, the judge only does the scoring.
#
# Each step says what a wrong answer scores, in plain numbers. A step that
# only says "check that the answer matches the policy" let a wrong time pass
# in a measurement on 2026-11-06, with the judge quoting the right one in its
# own reason.
CORRECT_STEPS = [
    ("Read the policy in the context and decide which of its rules apply to "
     "the customer's question."),
    ("Work out the outcome those rules require: a refund, no refund, or an "
     "escalation to a support specialist with no decision made in the answer."),
    ("If the actual output reaches a different outcome than the one required, "
     "the score is 0."),
    ("List every number in the actual output, such as days, amounts and "
     "business days. If any of them appears in neither the policy nor the "
     "question, the score is 0."),
    ("If the outcome is right and every number checks out, the score is 10. "
     "Don't take points off for wording, tone or extra polite sentences."),
]

COURTESY_STEPS = [
    "Read the actual output as the customer would.",
    ("If it is rude, curt, dismissive or sarcastic, or it lectures or blames "
     "the customer, the score is 0."),
    ("If it is polite and respectful, the score is 10, whether it gives good "
     "news or bad. Don't judge whether the facts are right."),
]


def follows_the_policy():
    # The policy goes in as context, and the judge reads it there. Without
    # it the judge has nothing to hold a 60-day window against.
    return GEval(
        name="Follows The Policy",
        evaluation_steps=CORRECT_STEPS,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.CONTEXT,
        ],
        threshold=0.75,
    )


def courteous():
    # Only the answer, since tone doesn't depend on the question or the policy.
    return GEval(
        name="Courteous",
        evaluation_steps=COURTESY_STEPS,
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
        threshold=0.75,
    )


@pytest.mark.parametrize("question", QUESTIONS, ids=["lamp", "blender", "sofa", "ebook"])
def test_answer(question):
    case = LLMTestCase(input=question, actual_output=answer(question), context=[POLICY])
    # Both metrics in one assert_test. DeepEval's cache, the -c flag, keeps
    # one list of metrics per test case, so splitting them across two calls
    # means they're never served from it.
    assert_test(case, [follows_the_policy(), courteous()])
