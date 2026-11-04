"""The page: a task, and its worked answer opened one line at a time.

A line of the answer only reaches the browser as the reply to a reveal, and
the server writes the reveal down before it replies. So a line can't be read
without being recorded, and nothing ever asks the learner to log anything. The
predecessor specified three capture surfaces that asked, and all three stayed
empty.

The margin note beside each line is worked out from the code, not written by
hand. A hand-written note per line is the kind of enrichment that costs
minutes per item, and that kind gets skipped.
"""

import argparse
import html
import http.server
import json
import pathlib
import threading

from markdown_it import MarkdownIt

from . import progress, runners, subject
from .environment import Site

WEB = pathlib.Path(__file__).resolve().parent / "web"
DEFAULT_LOG = pathlib.Path("run") / "reveals.jsonl"

_MARKDOWN = MarkdownIt("commonmark").enable("table")


def find_items(subjects):
    """Every item of every subject, keyed subject/item."""
    found = {}
    for each in subjects:
        found.update(each.items())
    return found


def find_steps(subjects):
    """Every step that has a guide, keyed subject/step, in course order."""
    return {
        step.name: step.guide
        for each in subjects for step in each.steps if step.guide
    }


def runner_of(item):
    """The runner the item's subject names, which knows its file types."""
    return runners.get(subject.of_item(item).runner)


def reference_of(item):
    return min(runner_of(item).sources(item / "reference"))


def worked_lines(item):
    """Every line of the item's reference as (number, text, margin).

    Blank lines keep their place so the shape of the file survives, and they
    have nothing to reveal. The margin comes from the runner, since what kind
    of line a line is depends on the language it's in.
    """
    margin_for = runner_of(item).margin_for
    lines = []
    for number, text in enumerate(reference_of(item).read_text().splitlines(), 1):
        lines.append((number, text, margin_for(text) if text.strip() else ""))
    return lines


def _shell(title, body):
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        "<link rel=\"stylesheet\" href=\"/static/page.css\">\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "<script src=\"/static/page.js\"></script>\n"
        "</body>\n</html>\n"
    )


def task_title(item):
    for line in (item / "TASK.md").read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return item.name


def _verdict_word(attempt):
    return "accepted" if attempt["accepted"] else "rejected"


def _first_heading(path, fallback):
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _status(attempts, name):
    last = attempts.last(name)
    if not last:
        return ""
    word = _verdict_word(last)
    return f" <span class=\"status {word}\">{word}</span>"


def _step_label(step):
    """'03-locators' as 'Step 3, locators', for a step with no guide to name it."""
    number, _, slug = step.dir.partition("-")
    label = slug.replace("-", " ")
    return f"Step {int(number)}, {label}" if number.isdigit() else step.dir


def render_index(subjects, attempts):
    """The course: each subject's steps in order, with their practice items.

    A step with a guide and no item, like the one on just enough TypeScript,
    still gets a page of its own. A step with items and no guide yet stays on
    the path, since its items belong there, and says the guide is still owed.
    An item that no step lists is listed apart. It can still be worked, but it
    isn't on the path, and mixing it in would hide that.
    """
    body = "<main>\n<h1>Orbis</h1>\n"
    body += "<p class=\"hint\">Each step is a guide, then an item to practice it on.</p>\n"
    for course in subjects:
        items = course.items()
        listed = set()
        steps = []
        for step in course.steps:
            practice = []
            for item_dir in step.items:
                name = f"{course.name}/{item_dir}"
                listed.add(name)
                if name in items:
                    practice.append((name, items[name]))
            links = ", ".join(
                f"<a href=\"/item/{html.escape(name)}\">{html.escape(task_title(item))}</a>"
                f"{_status(attempts, name)}"
                for name, item in practice
            )
            if step.guide:
                title = html.escape(_first_heading(step.guide, step.dir))
                href = f"/item/{practice[0][0]}" if practice else f"/step/{step.name}"
                tail = (
                    f"then practice: {links}" if practice
                    else "a guide to read, with nothing to practice yet"
                )
                steps.append(
                    f"  <li><a href=\"{html.escape(href)}\">{title}</a>"
                    f" <span class=\"title\">{tail}</span></li>"
                )
            else:
                steps.append(
                    f"  <li><span class=\"step\">{html.escape(_step_label(step))}</span>"
                    f" <span class=\"title\">waiting for a guide, practice: {links}</span></li>"
                )
        body += f"<section class=\"subject\" id=\"subject-{html.escape(course.name)}\">\n"
        body += f"<h2>{html.escape(course.title)}</h2>\n"
        body += "<ol class=\"course\">\n" + "\n".join(steps) + "\n</ol>\n"
        waiting = [
            f"  <li><a href=\"/item/{html.escape(name)}\">{html.escape(task_title(item))}</a>"
            f" <span class=\"title\">{html.escape(name)}</span>{_status(attempts, name)}</li>"
            for name, item in items.items() if name not in listed
        ]
        if waiting:
            body += (
                "<div class=\"waiting\">\n<h3>Practice items no step lists yet</h3>\n"
                "<p class=\"hint\">These work, but they aren't on the path.</p>\n"
                "<ul>\n" + "\n".join(waiting) + "\n</ul>\n</div>\n"
            )
        body += "</section>\n"
    return _shell("Orbis", body + "</main>")


def render_lesson_page(name, path):
    """A step's guide with no practice item behind it, on a page of its own."""
    body = (
        "<main>\n<p class=\"crumbs\"><a href=\"/\">the course</a></p>\n"
        f"<section id=\"lesson\">\n{_MARKDOWN.render(path.read_text())}</section>\n</main>"
    )
    return _shell(_first_heading(path, name), body)


def _from_root(path):
    """A path as typed from the repo root, or as it is when it lies elsewhere."""
    path = pathlib.Path(path)
    try:
        return path.relative_to(subject.ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def render_app(name, item, url):
    """Where the learner drives the real app while writing tests.

    The tests are written against the live page, so it's one click away. Only
    the real app is served here. The broken copies never get a URL, since
    exploring them first would mean testing the breaks instead of the rules.
    """
    runner = runner_of(item)
    mine = runner.mine_name(name)
    rows = "\n".join(
        f"<tr><td>{html.escape(what)}</td><td><code>{html.escape(command)}</code></td></tr>"
        for what, command in runner.app_commands(url, mine)
    )
    url = html.escape(url)
    spec = html.escape(mine)
    workspace = html.escape(_from_root(subject.of_item(item).workspace))
    return (
        "<section id=\"app\">\n<h2>The app</h2>\n"
        f"<p>The real app is running at <a href=\"{url}\" target=\"_blank\">{url}</a>."
        " Poke at it, watch what changes and when, and write your tests against it.</p>\n"
        f"<p class=\"hint\">Write your tests in <code>{workspace}/{spec}</code>. In a shell,"
        f" after <code>source env.sh</code> and <code>cd {workspace}</code>:</p>\n"
        f"<table>\n{rows}\n</table>\n</section>"
    )


def render_attempt(name, item, last):
    """The gate's verdict on the learner's latest file, cell by cell."""
    runner = runner_of(item)
    workspace = _from_root(subject.of_item(item).workspace)
    command = (
        f"uv run python -m orbis.gate attempt {html.escape(_from_root(item))}"
        f" --candidate {html.escape(workspace)}/{html.escape(runner.mine_name(name))}"
    )
    if last is None:
        return (
            "<section id=\"attempt\">\n<h2>Your attempt</h2>\n"
            "<p>No attempt graded yet. Grade one with</p>\n"
            f"<pre><code>{command}</code></pre>\n</section>"
        )
    rows = "\n".join(
        f"<tr><td>{html.escape(c['environment'])}</td><td>{html.escape(c['cell'])}</td>"
        + "<td>" + "<br>".join(
            f"<code>{html.escape(runner.trace_command(t))}</code>"
            for t in c.get("traces", [])
        ) + "</td></tr>"
        for c in last["cells"]
    )
    word = _verdict_word(last)
    return (
        "<section id=\"attempt\">\n<h2>Your attempt</h2>\n"
        f"<p>The gate <span class=\"verdict {word}\">{word}</span>"
        f" <code>{html.escape(last['candidate'])}</code> at {html.escape(last['at'])}.</p>\n"
        "<table>\n<tr><th>environment</th><th>cell</th><th>what your tests saw</th></tr>\n"
        f"{rows}\n</table>\n"
        f"<p class=\"hint\">Grade another with</p>\n<pre><code>{command}</code></pre>\n"
        "</section>"
    )


def guide_of(item):
    """The guide of the step an item practices, or None if it has none yet."""
    step = subject.of_item(item).step_of(item.name)
    return step.guide if step else None


def render_lesson(item):
    path = guide_of(item)
    if path is None:
        return ""
    return f"<section id=\"lesson\">\n{_MARKDOWN.render(path.read_text())}</section>\n"


def _demote(rendered):
    """Push every heading down a level, so the lesson keeps the page's h1."""
    for level in (5, 4, 3, 2, 1):
        rendered = rendered.replace(f"<h{level}>", f"<h{level + 1}>")
        rendered = rendered.replace(f"</h{level}>", f"</h{level + 1}>")
    return rendered


def render_item(name, item, revealed, last=None, app_url=None):
    task = _MARKDOWN.render((item / "TASK.md").read_text())
    if guide_of(item):
        task = "<p class=\"step\">Practice</p>\n" + _demote(task)
    rows = []
    for number, text, margin in worked_lines(item):
        if not text.strip():
            rows.append("<li class=\"blank\"></li>")
            continue
        note = f"<span class=\"margin\">{html.escape(margin)}</span>"
        if number in revealed:
            body = f"<code>{html.escape(text)}</code>"
            rows.append(f"<li class=\"line\" id=\"line-{number}\">{note}{body}</li>")
        else:
            button = f"<button type=\"button\" data-line=\"{number}\">reveal</button>"
            rows.append(
                f"<li class=\"line hidden\" id=\"line-{number}\">{note}{button}</li>"
            )
    body = (
        f"<main data-item=\"{html.escape(name)}\">\n"
        "<p class=\"crumbs\"><a href=\"/\">the course</a></p>\n"
        f"{render_lesson(item)}"
        f"<section id=\"task\">\n{task}</section>\n"
        f"{render_app(name, item, app_url) if app_url else ''}\n"
        f"{render_attempt(name, item, last)}\n"
        "<section id=\"answer\">\n<h2>The worked answer</h2>\n"
        "<p class=\"hint\">Write your own attempt first. Each line opens on its own,"
        " and the margin says what kind of line it is.</p>\n"
        "<ol class=\"lines\">\n" + "\n".join(rows) + "\n</ol>\n</section>\n</main>"
    )
    return _shell(task_title(item), body)


def _handler(subjects, items, log, attempts, apps, steps):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, kind, payload):
            data = payload.encode() if isinstance(payload, str) else payload
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                page = render_index(subjects, attempts)
                return self._send(200, "text/html; charset=utf-8", page)
            if path.startswith("/step/"):
                name = path[len("/step/"):]
                if name in steps:
                    page = render_lesson_page(name, steps[name])
                    return self._send(200, "text/html; charset=utf-8", page)
            if path.startswith("/item/"):
                name = path[len("/item/"):]
                if name in items:
                    page = render_item(
                        name, items[name], log.revealed(name), attempts.last(name),
                        apps[name].base_url,
                    )
                    return self._send(200, "text/html; charset=utf-8", page)
            if path in ("/static/page.css", "/static/page.js"):
                kind = "text/css" if path.endswith(".css") else "text/javascript"
                return self._send(200, kind, (WEB / path.rsplit("/", 1)[1]).read_bytes())
            self._send(404, "text/plain", "not found")

        def do_POST(self):
            if self.path != "/reveal":
                return self._send(404, "text/plain", "not found")
            length = int(self.headers.get("Content-Length", "0"))
            try:
                asked = json.loads(self.rfile.read(length))
                name, number = asked["item"], int(asked["line"])
            except (ValueError, KeyError, TypeError):
                return self._send(400, "text/plain", "send an item and a line")
            if name not in items:
                return self._send(404, "text/plain", "no such item")
            lines = {n: text for n, text, _ in worked_lines(items[name])}
            if not lines.get(number, "").strip():
                return self._send(404, "text/plain", "no such line")
            # Written before the reply goes out, so the line is never on
            # screen without its record.
            log.record(name, number)
            reply = json.dumps({"line": number, "text": lines[number]})
            self._send(200, "application/json", reply)

    return Handler


class Server:
    """Serve the pages on a loopback port and record reveals to a log file.

    The attempts log sits beside the reveals log unless told otherwise, which
    is where `gate attempt` writes by default.

    Each item's real app gets a port of its own, because the tests call
    page.goto("/") and that resolves to the root of the base URL. Served under
    a path, every one of them would land on the wrong page. With a fixed page
    port the apps take the ports right after it, so the addresses stay the same
    from one sitting to the next.
    """

    def __init__(self, subjects_root, log_path, port=0, attempts_path=None):
        self.subjects = subject.find(subjects_root)
        self.items = find_items(self.subjects)
        self.log = pathlib.Path(log_path)
        attempts = pathlib.Path(attempts_path or self.log.parent / "attempts.jsonl")
        self.apps = {
            name: Site(item / "app", port + 1 + index if port else 0)
            for index, (name, item) in enumerate(self.items.items())
        }
        handler = _handler(
            self.subjects, self.items, progress.RevealLog(self.log),
            progress.AttemptLog(attempts), self.apps, find_steps(self.subjects),
        )
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.port = self._server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self):
        for app in self.apps.values():
            app.__enter__()
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
        for app in self.apps.values():
            app.__exit__(None, None, None)
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(prog="orbis.page")
    parser.add_argument(
        "--subjects", default=str(subject.SUBJECTS), help="the subjects directory"
    )
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="where reveals go")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    with Server(args.subjects, args.log, args.port) as running:
        print(f"Orbis at {running.base_url}  (reveals go to {args.log})")
        for name, app in running.apps.items():
            print(f"  {name:<32} {app.base_url}")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
