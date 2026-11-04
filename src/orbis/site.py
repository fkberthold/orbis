"""The reading pages, built with mkdocs-material from the subjects tree.

Every page a learner reads comes from a file that's already in a subject: the
course order from subject.toml, each step's guide, each item's TASK.md and the
subject's CURRICULUM.md. This module copies them into a docs tree in course
order, writes a mkdocs.yml with the nav spelled out, and runs mkdocs over it.

Nothing live goes into the build. The app's address, the last verdict and the
worked answer all come from orbis.page while it runs, through orbis.js. So the
built site holds no line of any reference, and no URL for a broken copy,
because neither one is known when the site is built.

The build is skipped when the assembled tree is the same as last time. The
tree is cheap to assemble, so it's assembled every time and hashed, and mkdocs
only runs when the hash moves. That covers an edited guide, a new step in
subject.toml, and a change to this file's own output, without a list of which
files to watch.
"""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

import yaml

from . import subject

WEB = pathlib.Path(__file__).resolve().parent / "web"
BUILD = subject.ROOT / "build"

# Copied from tla-puzzles' mkdocs.yml and cut down to what these pages use.
THEME = {
    "name": "material",
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "indigo",
            "accent": "indigo",
            "toggle": {"icon": "material/weather-sunny", "name": "Switch to dark mode"},
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "indigo",
            "accent": "indigo",
            "toggle": {"icon": "material/weather-night", "name": "Switch to light mode"},
        },
    ],
    "features": [
        "navigation.instant",
        "navigation.tracking",
        "navigation.tabs",
        "navigation.sections",
        "navigation.expand",
        "navigation.indexes",
        "navigation.top",
        "navigation.footer",
        "search.suggest",
        "search.highlight",
        "content.code.copy",
        "toc.follow",
    ],
}

MARKDOWN_EXTENSIONS = [
    "admonition",
    "pymdownx.details",
    "pymdownx.superfences",
    {"pymdownx.highlight": {"anchor_linenums": True, "pygments_lang_class": True}},
    "pymdownx.inlinehilite",
    {"pymdownx.tabbed": {"alternate_style": True}},
    "tables",
    "footnotes",
    "def_list",
    "attr_list",
    "md_in_html",
    {"toc": {"permalink": True}},
]


def step_label(step):
    """'03-locators' as 'Step 3, locators'."""
    number, _, slug = step.dir.partition("-")
    label = slug.replace("-", " ")
    return f"Step {int(number)}, {label}" if number.isdigit() else step.dir


def first_heading(path, fallback):
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def curriculum_title(root):
    """A subject's name, for a subject that has a curriculum and no toml yet.

    The curricula open with 'The X curriculum', so X is the name. Anything
    else falls back to the folder's name rather than guessing harder.
    """
    heading = first_heading(root / "CURRICULUM.md", "")
    found = re.match(r"The (.+?) curriculum", heading)
    return found.group(1) if found else root.name


def _live(item_name, part, waiting):
    """A box orbis.js fills in from the server, saying so until it does."""
    return (
        f'<div class="orbis-live" id="{part}" data-orbis-item="{item_name}"'
        f' data-orbis-part="{part}" markdown="0">'
        f'<p class="orbis-wait">{waiting}</p></div>'
    )


def practice_page(name, item, step):
    """An item's practice: the task, then the three parts the server supplies."""
    if step is None:
        intro = (
            '!!! warning "Not on the path yet"\n'
            "    No step lists this item, so there's no guide behind it.\n\n"
        )
    elif step.guide:
        intro = (
            f'!!! note "Practice for {step_label(step).lower()}"\n'
            "    Read [the guide](guide.md) first. Then write your tests against the"
            " real app below.\n\n"
        )
    else:
        intro = (
            f'!!! note "Practice for {step_label(step).lower()}"\n'
            "    This step is waiting for a guide, so the task below is all there"
            " is to go on for now.\n\n"
        )
    waiting = "This part comes from orbis.page, so open the page through it."
    return (
        intro
        + (item / "TASK.md").read_text().rstrip()
        + "\n\n## The app\n\n"
        + _live(name, "app", waiting)
        + "\n\n## Your attempt\n\n"
        + _live(name, "attempt", waiting)
        + "\n\n## The worked answer\n\n"
        + "Write your own attempt first. Each line opens on its own, and the"
        " margin says what kind of line it is.\n\n"
        + _live(name, "answer", waiting)
        + "\n"
    )


def _status(name):
    return f' <span class="orbis-status" data-orbis-item="{name}"></span>'


def _assemble_subject(course, docs):
    """One subject's pages and its nav, in the order subject.toml gives."""
    out = docs / course.name
    out.mkdir(parents=True)
    items = course.items()
    listed = set()
    nav = [f"{course.name}/index.md"]
    lines = []

    if (course.root / "CURRICULUM.md").is_file():
        shutil.copy(course.root / "CURRICULUM.md", out / "curriculum.md")
        nav.append({"Curriculum": f"{course.name}/curriculum.md"})

    for step in course.steps:
        label = step_label(step)
        (out / step.dir).mkdir()
        section = []
        practice = []
        for item_dir in step.items:
            name = f"{course.name}/{item_dir}"
            listed.add(name)
            if name not in items:
                continue
            item = items[name]
            title = first_heading(item / "TASK.md", item_dir)
            page = f"{step.dir}/{item_dir}.md"
            (out / page).write_text(practice_page(name, item, step))
            practice.append(f"[{title}]({page}){_status(name)}")
            short = title.split(":", 1)[0]
            section.append({f"Practice: {short}": f"{course.name}/{page}"})

        tail = "then practice " + ", ".join(practice) if practice else ""
        if step.guide:
            shutil.copy(step.guide, out / step.dir / "guide.md")
            section.insert(0, {"Guide": f"{course.name}/{step.dir}/guide.md"})
            title = first_heading(step.guide, step.dir)
            lines.append(
                f"1. **[{label}]({step.dir}/guide.md)**: {title}, "
                + (tail or "a guide to read, with nothing to practice yet") + "."
            )
        else:
            (out / step.dir / "waiting.md").write_text(
                f"# {label}\n\n"
                "This step is waiting for a guide. Its practice is already on the"
                " path, so it can be worked from the task alone.\n"
            )
            section.insert(0, {"Waiting for a guide": f"{course.name}/{step.dir}/waiting.md"})
            lines.append(
                f"1. **[{label}]({step.dir}/waiting.md)**: waiting for a guide, "
                + (tail or "with nothing to practice yet") + "."
            )
        nav.append({label: section})

    unlisted = [(n, i) for n, i in items.items() if n not in listed]
    if unlisted:
        (out / "unlisted").mkdir()
        section = []
        for name, item in unlisted:
            title = first_heading(item / "TASK.md", item.name)
            (out / "unlisted" / f"{item.name}.md").write_text(practice_page(name, item, None))
            section.append({title.split(":", 1)[0]: f"{course.name}/unlisted/{item.name}.md"})
        nav.append({"Not on the path yet": section})

    index = f"# {course.title}\n\nEach step is a guide, then an item to practice it on."
    if (course.root / "CURRICULUM.md").is_file():
        index += " [The curriculum](curriculum.md) says why the steps run in this order."
    index += '\n\n<div class="orbis-course" markdown>\n\n' + "\n".join(lines) + "\n\n</div>\n"
    if unlisted:
        index += (
            "\n## Not on the path yet\n\nThese items work, but no step lists them.\n\n"
            + "\n".join(
                f"- [{first_heading(i / 'TASK.md', i.name)}](unlisted/{i.name}.md){_status(n)}"
                for n, i in unlisted
            )
            + "\n"
        )
    (out / "index.md").write_text(index)
    return {course.title: nav}


def assemble(subjects_root, dest):
    """Write the docs tree and mkdocs.yml under dest. Return the config path."""
    subjects_root = pathlib.Path(subjects_root)
    dest = pathlib.Path(dest)
    docs = dest / "docs"
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)

    courses = {course.name: course for course in subject.find(subjects_root)}
    nav = [{"Home": "index.md"}]
    home = ["# Orbis", "", "One tab per subject. Each one is a course, in the order it's taken.", ""]
    for root in sorted(p for p in subjects_root.iterdir() if p.is_dir()):
        if root.name in courses:
            nav.append(_assemble_subject(courses[root.name], docs))
            title = courses[root.name].title
        elif (root / "CURRICULUM.md").is_file():
            # A curriculum with no subject.toml is a course being planned.
            # It gets its tab with that one page and no runner behind it.
            (docs / root.name).mkdir()
            shutil.copy(root / "CURRICULUM.md", docs / root.name / "index.md")
            title = curriculum_title(root)
            nav.append({title: [f"{root.name}/index.md"]})
        else:
            continue
        home.append(f"- [{title}]({root.name}/index.md)")
    (docs / "index.md").write_text("\n".join(home) + "\n")

    assets = docs / "assets" / "orbis"
    assets.mkdir(parents=True)
    for name in ("orbis.css", "orbis.js"):
        shutil.copy(WEB / name, assets / name)

    config = {
        "site_name": "Orbis",
        "docs_dir": "docs",
        "theme": THEME,
        "markdown_extensions": MARKDOWN_EXTENSIONS,
        "extra_css": ["assets/orbis/orbis.css"],
        # extra_javascript loads after the theme bundle, which is what puts
        # document$ in scope for orbis.js. tla-puzzles' mkdocs.yml has the
        # long version of why it has to subscribe rather than run on load.
        "extra_javascript": ["assets/orbis/orbis.js"],
        "plugins": ["search"],
        "nav": nav,
    }
    path = dest / "mkdocs.yml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    return path


def _digest(dest):
    sha = hashlib.sha256()
    for path in sorted([dest / "mkdocs.yml", *(dest / "docs").rglob("*")]):
        if path.is_file():
            sha.update(path.relative_to(dest).as_posix().encode() + b"\0")
            sha.update(path.read_bytes() + b"\0")
    return sha.hexdigest()


def build(subjects_root=subject.SUBJECTS, dest=BUILD, force=False):
    """Assemble the docs and run mkdocs if they changed. Return the site dir.

    The digest is written only after mkdocs succeeds, so a failed build is
    tried again next time instead of being taken for fresh.
    """
    dest = pathlib.Path(dest)
    config = assemble(subjects_root, dest)
    site = dest / "site"
    stamp = dest / "inputs.json"
    digest = _digest(dest)
    try:
        fresh = json.loads(stamp.read_text())["digest"] == digest
    except (OSError, ValueError, KeyError):
        fresh = False
    if fresh and not force and (site / "index.html").is_file():
        return site
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--quiet", "--clean",
         "-f", str(config), "-d", str(site)],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"mkdocs build failed:\n{result.stdout}{result.stderr}")
    stamp.write_text(json.dumps({"digest": digest}))
    return site


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(prog="orbis.site")
    parser.add_argument("--subjects", default=str(subject.SUBJECTS))
    parser.add_argument("--out", default=str(BUILD))
    parser.add_argument("--force", action="store_true", help="build even when fresh")
    args = parser.parse_args(argv)
    print(build(args.subjects, args.out, args.force))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
