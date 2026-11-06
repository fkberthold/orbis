# A candidate that pins each answer to the string the bot sent once. It
# catches every break, and it also objects to a real bot that words a correct
# answer differently, which the rules allow. So G1 rejects it.
import pytest
from deepeval import assert_test
from deepeval.metrics import ExactMatchMetric
from deepeval.test_case import LLMTestCase
from refund_policy import QUESTIONS, answer

RECORDED_ONCE = {
    QUESTIONS[0]:
        "Thanks for reaching out! Yes, you can. Since the lamp is unused, "
        "still in its original box, and was delivered within the last 30 "
        "days, it qualifies for a full refund. Once it reaches our warehouse, "
        "the refund goes back to your original payment method within 5 to 7 "
        "business days.",
    QUESTIONS[1]:
        "I'm sorry, but I can't offer a refund on the blender. Our policy "
        "allows refunds within 30 days of delivery, and it's been 45 days, "
        "so the return window has closed. Thank you for understanding, and "
        "let me know if there's anything else I can help with.",
    QUESTIONS[2]:
        "I'm really sorry the sofa arrived damaged. Because it arrived "
        "damaged and the purchase is over $200, I've passed your refund "
        "request to a support specialist rather than deciding it here. A "
        "specialist will review it within 2 business days and get back to "
        "you.",
    QUESTIONS[3]:
        "Thanks for asking, and I'm sorry the e-book wasn't what you hoped "
        "for. Unfortunately, digital downloads can't be refunded once "
        "they've been downloaded, so I'm not able to refund this one.",
}


@pytest.mark.parametrize("question", QUESTIONS)
def test_answer_is_the_recording(question):
    case = LLMTestCase(
        input=question,
        actual_output=answer(question),
        expected_output=RECORDED_ONCE[question],
    )
    assert_test(case, [ExactMatchMetric()])
