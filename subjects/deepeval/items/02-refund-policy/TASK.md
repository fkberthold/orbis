# Refund policy: hold the bot to the policy and to its manners

A home-goods shop's support bot answers refund questions from the shop's
written policy. Its answers were recorded, so the same question always gets
the same string back. None of the rules below can be checked with a regex,
since a correct answer can be worded a dozen ways. So this is where a model
becomes the oracle.

Write DeepEval tests that hold the bot to the rules below.

## The bot

`answer(question)` in the `refund_policy` module takes a question and returns
the bot's answer as a string. `POLICY` is the policy the bot was given, word
for word, and `QUESTIONS` holds the four questions it was recorded on.

| question | what the policy says |
|---|---|
| an unopened desk lamp, delivered 10 days ago | refund |
| a sealed blender, delivered 45 days ago | no refund |
| a $650 sofa that arrived damaged | escalate to a specialist |
| an e-book that's been downloaded | no refund |

Any other question raises a `KeyError` that lists these four.

## The rules

1. Every answer reaches the outcome the policy requires for that question,
   whether that's a refund, no refund, or an escalation.
2. An answer that escalates says a specialist will review the request. It
   doesn't approve or deny the refund itself.
3. Every number an answer gives, such as a window in days, comes from the
   policy or from the question.
4. Every answer is courteous. Bad news is still delivered politely.

The rules say nothing about wording. An answer can thank the customer or
not, run long or short, and put the facts in any order. A bot that does any
of those things still follows the rules.

## What you are given

- The bot's source, on this page under The app. Its policy and recorded
  answers are in it.
- Write your tests in Python with DeepEval, in a file whose name starts with
  `test_`, under `subjects/deepeval/workspace/mine/`.
- `from refund_policy import POLICY, QUESTIONS, answer` imports the bot. The
  commands under The app put it on the import path.

## The judge

The grader runs your tests with one judge, gpt-5.4-mini on Poe, at
temperature 0. It sets that judge up the way a real suite does, once for
every metric, so leave `model=` off your metrics. If you pass one, the
grader replaces it with its own judge anyway, because a grade only means
something for the judge it was measured on.

To run your tests yourself against the same judge, set it up once from the
workspace. You'll need a Poe API key in `POE_API_KEY`.

    uv run deepeval set-local-model --model=gpt-5.4-mini --base-url=https://api.poe.com/v1
    export LOCAL_MODEL_API_KEY="$POE_API_KEY"

The first command writes the setting to `.deepeval/` in the workspace, which
git ignores. A run of the four questions with two judged metrics each cost
about half a cent when this was written.

## How this is graded

Your tests run against the real bot and against four broken copies of it.
Passing the real bot isn't the bar, because a test that asserts nothing
passes the real bot. Each broken copy breaks exactly one rule on one
question, and your tests have to notice.

There's more than one real bot, too. Three more copies word every answer
differently and still follow every rule. Your tests have to pass all four
real ones.

A judge's scores can move between runs, so the grader runs your file three
times against every copy. It has to land in the same cell all three times,
with the same tests passing and failing. If it doesn't, that copy reads
`did-not-run` and the note names the test that flipped. A test that passes
on Tuesday and fails on Wednesday established nothing either day.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, or the three runs disagreed |

A cell says what happened, not whether it's good news. `silent` against a
real bot is correct. `silent` against a broken copy is the thing to go fix.
So is `catches` against a real one, since that's a test holding the bot to a
rule nobody wrote.
