# An assertion whose oracle is a model

Every assertion you've written in twenty years was decided by code. The same
input gave the same verdict, a failure meant something changed, and running a
test cost nothing worth counting. A judged DeepEval metric breaks all three.
Its verdict comes from a call to another LLM, the judge, which reads your app's
answer and scores it. This lesson is about what that does to a test, before
any of the API.

## A whole suite, one test of each kind

The library's bot from the later steps also answers questions in prose. Here
it is with one test decided in code and one decided by a judge.

```python
# mine/hours.py
"""The library bot's prose answers, recorded."""

POLICY = "The library is open 9 am to 8 pm Monday to Saturday, and noon to 5 pm on Sunday."

RECORDED = {
    "When do you close on Sunday?": "On Sundays we close at 5 pm.",
}


def answer(question: str) -> str:
    return RECORDED[question]
```

```python
# mine/test_hours.py
import os

from deepeval import assert_test
from deepeval.metrics import GEval, PatternMatchMetric
from deepeval.models import LocalModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from hours import POLICY, answer

# Step 8 covers choosing a judge. Until then, this one is named here. It's a
# cheap model reached through Poe, and the table below shows where it slips.
JUDGE = LocalModel(
    model="gpt-5.4-nano",
    base_url="https://api.poe.com/v1",
    api_key=os.environ["POE_API_KEY"],
    temperature=0,
)

QUESTION = "When do you close on Sunday?"


def test_the_answer_names_a_time():
    case = LLMTestCase(input=QUESTION, actual_output=answer(QUESTION))
    assert_test(case, [PatternMatchMetric(pattern=r"(?s).*\b\d{1,2} ?(am|pm)\b.*")])


def test_the_answer_agrees_with_the_policy():
    case = LLMTestCase(input=QUESTION, actual_output=answer(QUESTION), context=[POLICY])
    correct = GEval(
        name="Agrees With Policy",
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT,
                           SingleTurnParams.CONTEXT],
        evaluation_steps=[
            "Find the time in the context that answers the question.",
            "Find the time the actual output gives.",
            "If the two times differ, the score is 0.",
            "If they match and the output states no other time, the score is 10.",
        ],
        threshold=0.75,
        model=JUDGE,
        async_mode=False,
    )
    assert_test(case, [correct])
```

```bash
uv run deepeval test run mine/test_hours.py
```

The first test checks that a time is there. Only the second can say whether
it's the right one, and that's the job a judge is for. But look at what the
second test needed that the first didn't: a model, an API key, a network, a
threshold, and four sentences telling the judge how to decide.

Then try it against a wrong answer. Changing the recording to "we close at 6
pm" and running the judged test three times, on 2026-11-06, gave this:

| evaluation steps | 6 pm, the wrong answer | 5 pm, the right one |
|---|---|---|
| looser: "check that the output states those hours and no others" | passed 3 of 3, scoring 0.8 to 1.0 | passed 3 of 3 |
| the four above, which spell out the comparison | failed 2 of 3, passed once at 1.0 | passed 3 of 3 |

With the looser steps, the judge's own reason quoted the policy's "noon to 5
pm" and passed the 6 pm answer anyway. Spelling the comparison out helped, and
it still let the wrong time through once in three runs. A pytest assertion on
the same two strings would never do either.

## What changes when the oracle is a model

| | an assertion in code | a judged metric |
|---|---|---|
| the verdict | the same on every run | can move between runs on the same input |
| a run costs | nothing | one or more judge calls per metric per case |
| the pass line | equality, or a condition you wrote | a `threshold` between 0 and 1 that somebody picked |
| a failure means | the app changed | the app changed, or the judge read it differently this time |
| when it's wrong | the assertion has a bug you can find | the judge misjudged, and its reason may sound sure of itself |

These were measured before the course was written, on a returns-policy bot
with good, reworded, invented, incomplete and off-topic answers.

| what was measured | what happened |
|---|---|
| gpt-5.4-nano judging G-Eval, three runs | the same answer's score moved by up to 0.2 |
| the same, at the default threshold of 0.5 | two cases flipped between pass and fail |
| the same, at a threshold of 0.75 | no flips, good answers at 0.9 or better, broken ones at 0.6 or worse |
| a local 7B model as the judge | perfectly repeatable, and it scored a correct rewording the same as an invented fact |
| answer relevancy, with either judge | passed answers with an invented fact, because they stayed on topic |

The last two rows are the ones I'd keep in mind. A judge that gives the same
score every time can still be wrong every time, so repeatable isn't the same as
right. And a metric only sees what it's built to look for. Relevancy asks
whether the answer is on topic, so an on-topic lie passes it.

So a judged test needs things a pytest assertion never did: a threshold with
room on both sides, a check that it passes the same way more than once, and a
metric whose question is the one the break would fail. Step 4 measures the
first two on purpose, and step 5 is about the third.

## How this course grades it

As in the Playwright course, your suite runs against the real app and against
copies with one thing broken each, and it should pass the first and fail every
one of the others. Because a judge's verdict can move, the gate runs a judged
suite three times against every copy and needs the same result all three
times. A suite that catches a break on one run in three hasn't caught it.

## Practice, predict then check

There's no item for this step. Say which of these four tests could pass on one
run and fail on the next with the app unchanged, then open the answer.

1. The pattern test above.
2. The G-Eval test above.
3. The G-Eval test above, run a second time with `deepeval test run -c`.
4. A custom metric whose `measure` runs `json.loads` on the answer and checks a
   key.

??? note "Answer"

    Only 2. Tests 1 and 4 are decided in code, so the same recorded answer
    gets the same verdict. Test 3 reuses the first run's cached verdict,
    because neither the test case nor the metric changed, so it can't move
    either. The cache hides the noise, it doesn't remove it: change the
    answer or the metric and the next run asks the judge again.
