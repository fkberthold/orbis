"""What the runtime remembers between sittings: the gate's verdict on an attempt.

The verdict is a fact about a run, so it's the one thing stored as one. Nothing
here turns it into a score.
"""

import json
import pathlib

import pytest
from playwright.sync_api import Page, expect

from orbis import gate, progress
from orbis import page as orbis_page

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEM = "playwright/01-seat-desk"
ITEM_DIR = ROOT / "items" / ITEM


@pytest.fixture
def run_dir(tmp_path):
    return tmp_path


@pytest.fixture
def server(run_dir):
    with orbis_page.Server(ROOT / "items", run_dir / "reveals.jsonl") as running:
        yield running


def cells(environments):
    return [{"environment": name, "cell": cell} for name, cell in environments]


def test_the_page_shows_the_last_attempt(page: Page, server, run_dir) -> None:
    attempts = progress.AttemptLog(run_dir / "attempts.jsonl")
    attempts.record(ITEM, "first.py", False, cells([("real", "silent"), ("m1", "silent")]))
    attempts.record(ITEM, "second.py", True, cells([("real", "silent"), ("m1", "catches")]))

    page.goto(server.base_url + "/item/" + ITEM)
    expect(page.locator("#attempt .verdict")).to_have_text("accepted")
    expect(page.locator("#attempt")).to_contain_text("second.py")
    expect(page.locator("#attempt tr", has_text="m1")).to_contain_text("catches")


def test_no_attempt_says_so(page: Page, server) -> None:
    page.goto(server.base_url + "/item/" + ITEM)
    expect(page.locator("#attempt")).to_contain_text("No attempt graded yet")
    expect(page.locator("#attempt code")).to_contain_text("orbis.gate attempt")


def test_the_index_shows_where_each_item_stands(page: Page, server, run_dir) -> None:
    attempts = progress.AttemptLog(run_dir / "attempts.jsonl")
    attempts.record(ITEM, "mine.py", False, cells([("real", "silent")]))
    page.goto(server.base_url + "/")
    step = page.locator("#course li", has=page.locator(f"a[href='/item/{ITEM}']"))
    expect(step).to_contain_text("rejected")


def test_the_attempt_command_records_the_gate_verdict(run_dir) -> None:
    weak = ITEM_DIR / "candidates" / "weak_passes_everything.py"
    log = run_dir / "attempts.jsonl"

    code = gate.main([
        "attempt", str(ITEM_DIR), "--candidate", str(weak), "--attempts", str(log),
    ])

    assert code == 1
    (record,) = [json.loads(line) for line in log.read_text().splitlines()]
    assert record["item"] == ITEM
    assert record["accepted"] is False
    assert {c["cell"] for c in record["cells"]} == {"silent"}
    assert record["cells"][0]["environment"] == "real"
    for cell in record["cells"]:
        assert cell["traces"], f"no trace kept for {cell['environment']}"
        assert all(pathlib.Path(t).is_file() for t in cell["traces"])
