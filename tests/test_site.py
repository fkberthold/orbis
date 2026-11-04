"""The site is rebuilt when what it's built from changes, and only then."""

import json
import pathlib
import shutil

from orbis import site

ROOT = pathlib.Path(__file__).resolve().parent.parent


def copy_subjects(dest):
    shutil.copytree(
        ROOT / "subjects", dest,
        ignore=shutil.ignore_patterns("node_modules", "runs", "test-results"),
    )
    return dest


def test_a_fresh_site_is_not_built_again(tmp_path):
    subjects = copy_subjects(tmp_path / "subjects")
    out = tmp_path / "build"
    built = site.build(subjects, out)
    marker = built / "marker"
    marker.write_text("mkdocs --clean would remove this")

    site.build(subjects, out)
    assert marker.exists()


def test_an_edited_guide_rebuilds_the_site(tmp_path):
    subjects = copy_subjects(tmp_path / "subjects")
    out = tmp_path / "build"
    site.build(subjects, out)
    before = json.loads((out / "inputs.json").read_text())["digest"]

    guide = subjects / "playwright" / "steps" / "02-writing-tests" / "guide.md"
    guide.write_text(guide.read_text() + "\nA line added by the test.\n")
    built = site.build(subjects, out)

    assert json.loads((out / "inputs.json").read_text())["digest"] != before
    page = built / "playwright" / "02-writing-tests" / "guide" / "index.html"
    assert "A line added by the test." in page.read_text()


def test_no_reference_reaches_the_docs_tree(tmp_path):
    out = tmp_path / "build"
    site.assemble(ROOT / "subjects", out)
    names = {p.name for p in (out / "docs").rglob("*")}
    assert not any(name.endswith(".spec.ts") for name in names)
