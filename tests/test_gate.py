"""The gate's own bookkeeping, apart from running anything."""

import pathlib

from orbis import gate, runners, verdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEM = ROOT / "subjects" / "deepeval" / "items" / "01-order-status"


def run(name, cell, outcomes=()):
    tests = [runners.TestOutcome(str(i), o) for i, o in enumerate(outcomes)]
    return runners.Run(name, cell, tests, 1)


def test_the_learners_file_can_be_reported(capsys):
    """gate attempt grades a file in the workspace, which isn't under the item.

    Naming it relative to the item raised, so every attempt crashed before a
    single run was printed.
    """
    item = gate.Item(ITEM)
    mine = item.subject.workspace / "mine" / "test_01_order_status.py"
    gate.report(item, mine, [run(runners.REAL, verdict.SILENT)])
    assert "CAND  subjects/deepeval/workspace/mine/test_01_order_status.py" in capsys.readouterr().out


def test_g1_holds_the_candidate_to_every_real_variant():
    runs = [
        run(runners.REAL, verdict.SILENT),
        run(runners.REAL + "+v1-keys-reordered", verdict.CATCHES, [verdict.FAIL]),
        run("m1-wrong-order-id", verdict.CATCHES, [verdict.FAIL]),
    ]
    results = dict(gate.conditions(runs, check_vectors=True))
    assert not results["G1 the candidate does not object to the real app"]
    assert results["G2 the candidate catches every mutation"]


def test_a_variant_is_not_counted_as_a_mutation():
    runs = [
        run(runners.REAL, verdict.SILENT),
        run(runners.REAL + "+v2-spaced-out", verdict.SILENT),
        run("m1-wrong-order-id", verdict.CATCHES, [verdict.FAIL]),
    ]
    results = dict(gate.conditions(runs, check_vectors=True))
    assert all(results.values())
