"""The gate: does this item's reference actually discriminate?

Three conditions, and the third is the one that checks the other two. A
reference that passes the real app and fails every mutation could still be
resting on a single assertion that happens to break three ways, in which case
two of the mutations are teaching the same thing. Comparing the per-test
vectors is what catches that.
"""

import argparse
import pathlib
import os
import subprocess
import sys

from . import runner, verdict

GATE_PASS = "OK"
GATE_FAIL = "FAIL"


class Item:
    """One authored item: a real app, its mutations, and its reference."""

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.app = self.root / "app"
        self.mutations = sorted((self.root / "mutations").glob("*.patch"))
        self.reference = self._one_file(self.root / "reference")

    def _one_file(self, directory):
        found = sorted(directory.glob("*.py"))
        if len(found) != 1:
            raise SystemExit(
                f"{directory} should hold exactly one candidate, found {len(found)}"
            )
        return found[0]

    def candidates(self):
        return sorted((self.root / "candidates").glob("*.py"))

    def check(self):
        if not self.app.is_dir():
            raise SystemExit(f"no app directory at {self.app}")
        if not self.mutations:
            raise SystemExit(f"no mutations under {self.root / 'mutations'}")


def browsers_path():
    """Where Playwright's browsers live, which on NixOS is a store path.

    The binaries Playwright downloads for itself are not linked for NixOS, so
    the ones nixpkgs builds are the only ones that run here.
    """
    from_env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if from_env:
        return from_env
    built = subprocess.run(
        ["nix", "build", "--no-link", "--print-out-paths",
         "nixpkgs#playwright-driver.browsers"],
        capture_output=True, text=True,
    )
    if built.returncode != 0:
        raise SystemExit(
            "PLAYWRIGHT_BROWSERS_PATH is unset and nix could not build the "
            "browsers. Run: source env.sh"
        )
    return built.stdout.strip().splitlines()[-1]


def grade(item, candidate, browsers):
    """Run one candidate across every environment and return the runs."""
    runs = [
        runner.run(candidate, item.app, None, runner.REAL, browsers)
    ]
    for patch in item.mutations:
        runs.append(
            runner.run(candidate, item.app, patch, patch.stem, browsers)
        )
    return runs


def report(item, candidate, runs):
    print(f"ITEM  {item.root}")
    print(f"CAND  {candidate.relative_to(item.root)}")
    print()
    print(f"  {'environment':<28}{'cell':<13}{'vector':<26}note")
    for run in runs:
        print(
            f"  {run.environment:<28}{run.cell:<13}"
            f"{run.vector_text:<26}{run.note}"
        )
    print()
    names = [outcome.name for outcome in runs[0].tests]
    if names:
        print("  vector order: " + ", ".join(names))
        print()


def conditions(runs, check_vectors):
    """Return a list of (label, ok) for each gate condition."""
    real, mutants = runs[0], runs[1:]
    results = [
        ("G1 the candidate does not object to the real app",
         real.cell == verdict.SILENT),
        ("G2 the candidate catches every mutation",
         bool(mutants) and all(m.cell == verdict.CATCHES for m in mutants)),
    ]
    if check_vectors:
        vectors = [m.vector for m in mutants]
        results.append(
            ("G3 no two mutations share a per-test vector",
             len(set(vectors)) == len(vectors)),
        )
    return results


def run_gate(item, candidate, browsers, check_vectors):
    runs = grade(item, candidate, browsers)
    report(item, candidate, runs)
    results = conditions(runs, check_vectors)
    for label, ok in results:
        print(f"  {label:<52}{GATE_PASS if ok else GATE_FAIL}")
    print()
    accepted = all(ok for _, ok in results)
    return accepted, runs


def command_gate(args):
    item = Item(args.item)
    item.check()
    candidate = (
        pathlib.Path(args.candidate).resolve() if args.candidate
        else item.reference
    )
    is_reference = candidate == item.reference
    accepted, _ = run_gate(item, candidate, browsers_path(), is_reference)
    print(f"GATE {GATE_PASS if accepted else GATE_FAIL}")
    return 0 if accepted else 1


def command_selfcheck(args):
    """Watch the gate fail before believing it.

    A gate that accepts everything measures nothing, so the item ships two
    candidates it must reject and this command asserts that it does.
    """
    item = Item(args.item)
    item.check()
    browsers = browsers_path()

    expectations = [(item.reference, True)]
    expectations += [(candidate, False) for candidate in item.candidates()]
    if len(expectations) < 2:
        raise SystemExit("selfcheck needs at least one candidate to reject")

    failures = []
    for candidate, should_accept in expectations:
        accepted, _ = run_gate(
            item, candidate, browsers, candidate == item.reference
        )
        verdict_word = "accepted" if accepted else "rejected"
        wanted = "accepted" if should_accept else "rejected"
        ok = accepted == should_accept
        print(
            f"SELFCHECK {candidate.name:<34}{verdict_word:<10}"
            f"wanted {wanted:<10}{GATE_PASS if ok else GATE_FAIL}"
        )
        print()
        if not ok:
            failures.append(candidate.name)

    if failures:
        print("SELFCHECK FAIL: " + ", ".join(failures))
        return 1
    print("SELFCHECK OK")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orbis.gate")
    parser.add_argument(
        "command", choices=["gate", "selfcheck"],
        help="gate grades one candidate, selfcheck proves the gate can fail",
    )
    parser.add_argument("item", help="path to an item directory")
    parser.add_argument(
        "--candidate", help="grade this file instead of the item's reference"
    )
    args = parser.parse_args(argv)
    if args.command == "gate":
        return command_gate(args)
    return command_selfcheck(args)


if __name__ == "__main__":
    sys.exit(main())
