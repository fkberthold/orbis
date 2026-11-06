# Order status: hold the bot to its four rules

A shop's support bot answers questions about orders in JSON, so the shop's
page can show the order without reading prose. Its answers were recorded, so
the same question always gets the same string back, and nothing here calls a
model. Every rule below can be checked without a judge.

Write DeepEval tests that hold the bot to the rules below.

## The bot

`answer(question)` in the `order_status` module takes a question and returns
the bot's answer as a JSON string. It was recorded on four questions, and
`QUESTIONS` holds them:

| question | the order |
|---|---|
| Where is order A-1042? | exists |
| When will order A-1077 arrive? | exists |
| Has order A-1103 been delivered yet? | exists |
| Where is order A-2000? | doesn't exist |

Any other question raises a `KeyError` that lists these four.

## The rules

1. Every answer is a JSON object that holds these three keys. `order_id` is a string,
   `status` is one of `processing`, `shipped`, `delivered` or `not_found`,
   and `eta` is a string or `null`.
2. `order_id` is the order the question names.
3. For an order that exists, `eta` is a date written `YYYY-MM-DD`.
4. For an order that doesn't exist, `status` is `not_found` and `eta` is
   `null`.

The keys can come in any order, and the spacing and line breaks can vary. An
answer can also carry other keys, such as `carrier`, and the rules say nothing
about them. A bot that does any of those things still follows the rules.

## What you are given

- The bot's source, on this page under The app. Its recorded answers are
  in it.
- Write your tests in Python with DeepEval, in a file whose name starts
  with `test_`, under `subjects/deepeval/workspace/mine/`.
- `from order_status import answer` imports the bot. The commands under
  The app put it on the import path.
- No judge is set up, and no API key reaches your tests. A metric that
  builds a judge fails when it's created. `JsonCorrectnessMetric` builds one
  unless you pass `eval_mode="system_one"`.

## How this is graded

Your tests run against the real bot and against four broken copies of it.
Passing the real bot is not the bar, because a test that asserts nothing
passes the real bot. Each broken copy breaks exactly one rule, and your tests
have to notice.

There's more than one real bot, too. Three more copies differ from it only
in ways the rules allow. Your tests have to pass all four real ones.

The grade says which of four things happened against each copy.

| cell | what it means |
|---|---|
| catches | your tests failed against this copy |
| silent | your tests passed against this copy |
| vacuous | your tests passed and asserted nothing |
| did-not-run | no verdict was reached, so nothing was established |

A cell says what happened, not whether it's good news. `silent` against a
real bot is correct. `silent` against a broken copy is the thing to go fix.
So is `catches` against a real one, since that's a test holding the bot to a
rule nobody wrote.
