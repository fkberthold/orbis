"""A subject is one folder under subjects/, and its subject.toml is the course.

The toml holds the order, because the order is the one thing a directory
listing can't be trusted with. It names each step and the items that practice
it. Everything else is found on disk: a step's guide is steps/<dir>/guide.md,
and an item is a directory under items/ that holds an app.

A step can be listed before its guide is written. Its items still belong to
it, so they stay on the path, and the page says the guide is still owed.
"""

import dataclasses
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUBJECTS = ROOT / "subjects"


@dataclasses.dataclass
class Step:
    subject: str
    dir: str
    root: pathlib.Path
    items: list

    @property
    def name(self):
        return f"{self.subject}/{self.dir}"

    @property
    def guide(self):
        path = self.root / "guide.md"
        return path if path.is_file() else None


@dataclasses.dataclass
class Subject:
    root: pathlib.Path
    title: str
    runner: str
    workspace: pathlib.Path
    steps: list

    @property
    def name(self):
        return self.root.name

    def items(self):
        """Every item on disk, keyed subject/item, in directory order."""
        return {
            f"{self.name}/{app.parent.name}": app.parent
            for app in sorted((self.root / "items").glob("*/app"))
        }

    def step_of(self, item_dir_name):
        """The step an item practices, or None when no step lists it."""
        for step in self.steps:
            if item_dir_name in step.items:
                return step
        return None


def load(root):
    root = pathlib.Path(root).resolve()
    data = tomllib.loads((root / "subject.toml").read_text())
    steps = [
        Step(root.name, entry["dir"], root / "steps" / entry["dir"],
             list(entry.get("items", [])))
        for entry in data.get("step", [])
    ]
    return Subject(
        root=root,
        title=data["title"],
        runner=data["runner"],
        workspace=root / data.get("workspace", "workspace"),
        steps=steps,
    )


def find(subjects_root=SUBJECTS):
    """Every subject under subjects_root, in name order."""
    return [
        load(toml.parent)
        for toml in sorted(pathlib.Path(subjects_root).glob("*/subject.toml"))
    ]


def of_item(item_dir):
    """The subject an item belongs to, which is two levels up from it."""
    return load(pathlib.Path(item_dir).resolve().parents[1])
