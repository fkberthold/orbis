"""Count the assertions a run actually executed.

Playwright writes a trace per test, and every assertion shows up in it as a
Frame.expect call. Reading that back is how the vacuous cell gets filled
without changing the interface a candidate writes against, which matters
because the environment supplying the interface is the thing that makes this
subject a workable first target.

A candidate can also assert with a plain assert statement, which never reaches
the trace. So the source gets a static look as well, and a candidate counts as
having asserted something if either channel says so. That errs toward calling
a run non-vacuous, which is the safe direction: the gate still rejects a
candidate that asserts a constant, because such a candidate stays silent
against every mutation.
"""

import ast
import json
import pathlib
import zipfile

EXPECT_CALL = ("Frame", "expect")


def expect_calls_in_trace(trace_zip):
    """Count Frame.expect calls recorded in one trace.zip."""
    total = 0
    with zipfile.ZipFile(trace_zip) as archive:
        for name in archive.namelist():
            if not name.endswith(".trace"):
                continue
            for line in archive.read(name).decode("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "before":
                    continue
                if (event.get("class"), event.get("method")) == EXPECT_CALL:
                    total += 1
    return total


def expect_calls_under(output_dir):
    """Count Frame.expect calls across every trace below output_dir."""
    output_dir = pathlib.Path(output_dir)
    if not output_dir.is_dir():
        return 0
    return sum(
        expect_calls_in_trace(trace)
        for trace in sorted(output_dir.rglob("trace.zip"))
    )


def has_assert_statement(source_path):
    """True when the candidate's own source contains an assert statement."""
    try:
        tree = ast.parse(pathlib.Path(source_path).read_text())
    except (OSError, SyntaxError):
        return False
    return any(isinstance(node, ast.Assert) for node in ast.walk(tree))
