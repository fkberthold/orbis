"""Shared by the page tests: one site build per session, in a temp dir.

So the tests never touch the build/ the learner reads from, and mkdocs runs
once rather than once per test.
"""

import pytest


@pytest.fixture(scope="session")
def build_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("site")
