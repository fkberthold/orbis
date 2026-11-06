"""A pytest plugin the grader loads into every judged run, to pin the judge.

It runs inside the learner's run, under the DeepEval workspace's Python, so it
imports nothing from Orbis. The grader starts the run with `-p orbis_judge`
and this directory on PYTHONPATH.

A real suite configures its judge once and lets every metric pick it up, and
this does the same. Every metric DeepEval builds a judge for gets this one,
so a metric written with no model= gets it, and so does one written with
model="gpt-4o" or a model object of the learner's own. The grade has to mean
the same thing for every candidate, and it only means anything for the judge
that was measured. Choosing a judge is step 8's practice, and that step is
ungraded for this reason.

The judge is reached over a Unix socket the grader holds open outside the
run's network namespace. The address and the key below are placeholders. The
grader's end of the socket sends the request to Poe with the real key.
"""

import os

import httpx2
from deepeval.metrics.utils import models as _models
from deepeval.models import LocalModel

SOCKET = os.environ["ORBIS_JUDGE_SOCKET"]
MODEL = os.environ["ORBIS_JUDGE_MODEL"]


class PinnedJudge(LocalModel):
    """DeepEval's OpenAI-compatible model, wired to the grader's socket."""

    def __init__(self):
        super().__init__(
            model=MODEL, base_url="http://judge/v1",
            api_key="held-by-the-grader", temperature=0,
        )

    def _build_client(self, cls):
        if cls.__name__.startswith("Async"):
            client = httpx2.AsyncClient(
                transport=httpx2.AsyncHTTPTransport(uds=SOCKET), timeout=180
            )
        else:
            client = httpx2.Client(
                transport=httpx2.HTTPTransport(uds=SOCKET), timeout=180
            )
        return cls(api_key="held-by-the-grader", base_url=self.base_url,
                   http_client=client, **self._client_kwargs())


def _pinned(model=None):
    # The (model, is native) pair initialize_model expects. Whatever the
    # metric was handed is ignored on purpose, as the docstring says.
    return PinnedJudge(), True


# initialize_model looks _build_model up in this module each time it's called,
# so replacing it here reaches every metric, including ones built later.
# A metric in eval_mode="system_one" never gets this far and stays judge-free.
_models._build_model = _pinned
