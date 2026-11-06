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


def judged(name, cell, scores, outcome=verdict.PASS):
    """A judged run with one test, scored once."""
    test = runners.TestOutcome("t: Follows The Policy", outcome, "", list(scores), 0.75)
    return runners.Run(name, cell, [test], 1, "passed")


def test_repeats_that_agree_keep_every_score():
    merged = gate.merge([judged(runners.REAL, verdict.SILENT, [s]) for s in (1.0, 0.9, 1.0)])
    assert merged.cell == verdict.SILENT
    assert merged.tests[0].scores == [1.0, 0.9, 1.0]


def test_repeats_that_disagree_are_did_not_run_and_name_the_flip():
    merged = gate.merge([
        judged("m2", verdict.CATCHES, [0.0], verdict.FAIL),
        judged("m2", verdict.SILENT, [0.8]),
        judged("m2", verdict.CATCHES, [0.0], verdict.FAIL),
    ])
    assert merged.cell == verdict.DID_NOT_RUN
    assert "Flipped: t: Follows The Policy" in merged.note
    assert "run 2 silent" in merged.note


def test_g4_wants_a_margin_on_both_sides_of_the_line():
    def g4(runs):
        return dict(gate.conditions(runs, check_vectors=True, judged=True))[
            f"G4 every judged score is {gate.MARGIN:.2f} clear of its threshold"]

    clear = [judged(runners.REAL, verdict.SILENT, [0.9, 1.0]),
             judged("m1", verdict.CATCHES, [0.0, 0.6], verdict.FAIL)]
    assert g4(clear)
    # 0.8 passes 0.75, and that's the trouble. It's one judge's mood away.
    assert not g4([judged(runners.REAL, verdict.SILENT, [1.0, 0.8]), clear[1]])
    assert not g4([clear[0], judged("m1", verdict.CATCHES, [0.0, 0.7], verdict.FAIL)])


def test_g4_fails_a_judged_reference_with_no_judged_score():
    runs = [run(runners.REAL, verdict.SILENT, [verdict.PASS]),
            run("m1", verdict.CATCHES, [verdict.FAIL])]
    results = dict(gate.conditions(runs, check_vectors=True, judged=True))
    assert not results[f"G4 every judged score is {gate.MARGIN:.2f} clear of its threshold"]
