"""A mutation has to change the app wherever the copy lands."""

import pathlib
import shutil

from orbis.environment import materialize

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEM = ROOT / "subjects" / "playwright" / "items" / "01-seat-desk"


def test_a_patch_applies_inside_the_checkout():
    """gate attempt keeps its runs under run/, which is inside the repo.

    git apply skipped every path there and still exited 0, so the learner's
    file was graded against four copies of the real app.
    """
    dest = ROOT / "run" / "test-materialize" / "app"
    shutil.rmtree(dest.parent, ignore_errors=True)
    try:
        patch = min((ITEM / "mutations").glob("*.patch"))
        materialize(ITEM / "app", patch, dest)
        changed = [
            p for p in dest.rglob("*")
            if p.is_file()
            and p.read_bytes() != (ITEM / "app" / p.relative_to(dest)).read_bytes()
        ]
        assert changed, f"{patch.name} changed nothing in {dest}"
    finally:
        shutil.rmtree(dest.parent, ignore_errors=True)
