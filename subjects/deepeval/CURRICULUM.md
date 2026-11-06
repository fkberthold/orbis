# The DeepEval curriculum

**The goal** is to own a real LLM-evaluation suite at work. That decides what
counts as fundamental. Choosing metrics, writing judge criteria, setting
thresholds, building datasets, paying for the judge and running it all in CI
have to be in the course, not left as extras.

**The learner** has twenty years as an SDET and a CS degree, and is fluent in
Python, pytest, Selenium, Robot Framework and Postman. So the guides skip
fixtures, parametrize and markers. They spend their words on what's new: an
assertion whose oracle is itself a model. That oracle is noisy, it costs money
per call, and its pass line is a number somebody picked.

## Where the lessons come from

The rule is to use a good existing course before writing one. So five
candidates were read against the goal on 2026-11-04.

| candidate | progressive? | current? | exercises? | reaches the goal? |
|---|---|---|---|---|
| deepeval.com docs | the quickstart is one page, the rest is reference | yes, 4.3.2 | none | every topic |
| deepeval.com tutorials | three use-case tracks | yes | follow-along only | leans on LangChain, OpenAI and Confident AI |
| theneuralbase.com | 147 lessons | unversioned | looks generated | can't tell |
| Udemy, Rahul Shetty | yes | not checked | not checked | paid |
| DeepLearning.AI | no DeepEval course | | | its agent-eval course uses Arize |

None of them is a good progressive course all the way to the goal. So the docs
pages are the chapters, read in the order below. Orbis supplies the order, a
short guide per step, every graded exercise, and the two lessons nothing
covers. The guides also say which sections to skip, since many pages route
results to Confident AI, the vendor's hosted platform.

## How a step works

1. **Read** the docs pages for the step, after the Orbis guide that says
   what's new and which trap to watch for.
2. **Practice** on an item: a small LLM app, rules to hold it to, and the gate
   that runs your suite against the real app and broken copies.
3. **Reveal** the worked answer one line at a time, after you've tried.

The app under test is a Python function with a fixed interface. Its outputs
are recorded, so a run doesn't call a model to produce them. The real app has
several paraphrased variants of each answer. A test that hardcodes one wording
fails the real app, and G1 rejects it. A mutation swaps one behavior: a wrong
retrieval, a dropped instruction, an invented fact, or format drift.

Practice leans on **write from a prompt** and **predict, then check**, since
the learner is an expert. Skeletons only appear where the API shape is the
hard part.

## The judge, measured

The gate's judge was measured on 2026-11-04, with a returns-policy bot, four
questions, and good, reworded, invented, dropped and off-topic answers.

| judge | repeats? | tells good from broken? | one run |
|---|---|---|---|
| qwen2.5:7b, local | yes, 0 flips in 5 runs | no, a correct rewording scored like an invented fact | ~16 min |
| dolphin3:8b, local | one run only | no, invented facts scored above good answers | |
| gpt-5.4-nano, Poe | scores move up to 0.2 | yes, on G-Eval with pinned steps at 0.75 | ~9 min, ~$0.03 |

So the judge is gpt-5.4-nano through Poe. Its scores move between runs, so the
gate runs each candidate several times and needs the same cell every time. The
reference also has to clear every break by a margin, not just the threshold.

The same run is step 5's lesson in advance. With both judges, answer relevancy
passed invented and dropped facts, because they stay on topic. Faithfulness
gave every off-topic answer full marks, because nothing in it contradicts the
context. Only G-Eval with pinned steps caught the breaks.

## The steps

| step | read | Orbis writes | practice |
|---|---|---|---|
| 0 | | **An assertion whose oracle is a model**, set against pytest | predict, then check: which of four tests can flip between runs |
| 1 | getting-started, evaluation-introduction, evaluation-test-cases | guide | none graded. Install, run `deepeval test run`, read `.latest_run_full.json` |
| 2 | metrics-introduction, metrics-exact-match, metrics-pattern-match, metrics-json-correctness | guide: what needs no judge, and why to check that first | **new: order-status bot**, breaks: wrong order id, dropped JSON field, date format drift |
| 3 | metrics-llm-evals, guides-g-eval-examples | guide: `criteria` against `evaluation_steps` | **new: refund-policy answerer**, breaks: drops the escalation rule, invents a 60-day window, turns curt |
| 4 | evaluation-flags-and-configs, command-line-interface | **Thresholds and judge noise**, which nothing covers | **new: near-miss answerer**, breaks sit just under the line, verdict must hold over repeats |
| 5 | getting-started-rag, metrics-faithfulness, metrics-answer-relevancy, metrics-contextual-precision, metrics-contextual-recall, metrics-contextual-relevancy, metrics-hallucination, guides-rag-triad | guide: which metric sees which stage of the pipeline | **new: equipment-manual RAG**, breaks: irrelevant chunk, right chunk ranked last, claim beyond context, answer dodges the question |
| 6 | evaluation-datasets, golden-synthesizer | guide: a golden against a test case | **new: the RAG app over a dataset**, breaks regress one category of goldens only |
| 7 | metrics-custom, metrics-dag, guides-building-custom-metrics | guide | **new: ticket-reply bot**, a `BaseMetric` for a house rule, breaks: no ticket number, wrong ticket number |
| 8 | metrics-introduction (judge section), integrations/models/ollama, integrations/models/anthropic, guides-using-custom-llms | guide: choosing a judge and counting its calls, with the measurement above | ungraded: point the suite at a different judge, then check against a worked one |
| 9 | evaluation-multiturn-test-cases, metrics-knowledge-retention, metrics-turn-relevancy, metrics-role-adherence, metrics-tool-correctness, metrics-task-completion | guide | **new, if kept: booking chatbot**, breaks: forgets the date by turn 3, calls the wrong tool |
| 10 | evaluation-unit-testing-in-ci-cd, guides-regression-testing-in-cicd | guide | ungraded: set up CI with the cache, then check against a worked one |
| 11 | evaluation-end-to-end-llm-evals | **Keeping an eval suite healthy**: goldens, re-baselining, reading the judge's reasons, a cost budget | capstone: a suite for a bigger RAG app with all the breaks mixed |

Page names in the read column sit under `https://deepeval.com/docs/`, except
`guides-*` under `https://deepeval.com/guides/` and `integrations/models/*`
under `https://deepeval.com/`. Each was checked against the site's sitemap on
2026-11-04.

Deterministic metrics come before G-Eval on purpose. I think an owner should
reach for a regex before a judge, and step 2 makes that a habit while the gate
is still cheap and exact. Datasets come after the RAG metrics, because a
dataset is only worth building once you know what each row gets scored on.

## What Orbis has to write

- **Lesson 0, an assertion whose oracle is a model.**
- **A guide per step,** short, pointing at the docs rather than repeating them.
- **Thresholds and judge noise** (step 4). I think this is the lesson that
  decides whether an eval suite at work gets trusted or muted.
- **Keeping an eval suite healthy** (step 11).
- **Every graded exercise.** None of the candidates has a grader.
- **The recorded apps.** Each needs paraphrased variants, and each break is a
  patch.

## Drills

Drills run alongside the course, not after it. Each is a short prose prompt
and a small recorded app, answered from an empty `test_*.py` in about ten
minutes and graded by the gate. Families interleave: deterministic checks,
G-Eval criteria, thresholds, RAG metrics, datasets and custom metrics. A drill
only enters the queue once the step that teaches it is done, and every drill
names that step by path.

## Settled with Frank, 2026-11-06

1. **Three repeats.** The gate runs each candidate three times against every
   environment and needs the same cell all three times.
2. **Step 9 stays.** Conversational and agent metrics are part of the course.
3. **Step 8 is ungraded.** It gets a worked judge config behind the
   line-by-line reveal, and the learner checks their own against it.
4. **No Confident AI.** It isn't used at work, so the guides say to skip every
   hosted-platform section, and nothing in the course logs in to it.
