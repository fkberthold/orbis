# A candidate that pins each answer to the string the bot sent once. It
# catches every break, and it also objects to a real bot that reorders its
# keys or spaces its JSON out, which the rules allow. So G1 rejects it.
import pytest
from deepeval import assert_test
from deepeval.metrics import ExactMatchMetric
from deepeval.test_case import LLMTestCase
from order_status import answer

RECORDED_ONCE = {
    "Where is order A-1042?":
        '{"order_id": "A-1042", "status": "shipped", "eta": "2026-11-12"}',
    "When will order A-1077 arrive?":
        '{"order_id": "A-1077", "status": "processing", "eta": "2026-11-19"}',
    "Has order A-1103 been delivered yet?":
        '{"order_id": "A-1103", "status": "delivered", "eta": "2026-11-03"}',
    "Where is order A-2000?":
        '{"order_id": "A-2000", "status": "not_found", "eta": null}',
}


@pytest.mark.parametrize("question", RECORDED_ONCE)
def test_answer_is_the_recording(question):
    case = LLMTestCase(
        input=question,
        actual_output=answer(question),
        expected_output=RECORDED_ONCE[question],
    )
    assert_test(case, [ExactMatchMetric()])
