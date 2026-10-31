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
import re
import threading

from markdown_it import MarkdownIt

from . import progress
from .environment import Site

WEB = pathlib.Path(__file__).resolve().parent / "web"
DEFAULT_LOG = pathlib.Path("run") / "reveals.jsonl"

_MARKDOWN = MarkdownIt("commonmark").enable("table")


def find_items(items_root):
    """Every item under items_root, keyed by its path below it."""
    items_root = pathlib.Path(items_root)
    found = {}
    for app in sorted(items_root.glob("*/*/app")):
        item = app.parent
        found[item.relative_to(items_root).as_posix()] = item
    return found


def reference_of(item):
    return min((item / "reference").glob("*.spec.ts"))


def _words(name):
    """'reserveSucceeds' or 'reserve_succeeds' as 'reserve succeeds'."""
    name = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", name)
    return name.replace("_", " ").strip().lower()


def margin_for(text):
    """Say roughly what kind of line this is, without saying what it does."""
    line = text.strip()
    test = re.match(r"test(?:\.\w+)?\(\s*['\"`](.+?)['\"`]", line)
    if test:
        return "a test: " + test.group(1)
    helper = re.match(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
    if helper:
        return "a helper: " + _words(helper.group(1))
    if line.startswith("import "):
        return "imports"
    if line.startswith(("//", "/*", "*")):
        return "a note on why"
    line = line.removeprefix("await ")
    if line.startswith("expect("):
        return "check the result"
    for call, note in (
        ("page.goto", "open the page"),
        ("page.fill", "fill a field"),
        ("page.selectOption", "pick an option"),
        ("page.dblclick", "double click"),
        ("page.click", "click"),
        ("page.route", "stub the network"),
        ("page.once", "handle a dialog"),
        ("page.on", "handle an event"),
        ("page.goBack", "go back"),
        ("page.waitFor", "wait"),
    ):
        if line.startswith(call):
            return note
    if re.match(r"\w+\(page", line):
        return "use the helper"
    return ""


def worked_lines(reference):
    """Every line of the reference as (number, text, margin).

    Blank lines keep their place so the shape of the file survives, and they
    have nothing to reveal.
    """
    lines = []
    for number, text in enumerate(reference.read_text().splitlines(), 1):
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


def find_lessons(items_root):
    """Every lesson beside items/, keyed the way items are, in course order."""
    lessons_root = pathlib.Path(items_root).parent / "lessons"
    return {
        path.relative_to(lessons_root).with_suffix("").as_posix(): path
        for path in sorted(lessons_root.glob("*/[0-9]*.md"))
    }


def render_index(items, attempts, lessons=None):
    """The course: each lesson in order, with its practice item behind it.

    A lesson with no item, like the one on just enough TypeScript, is still a
    step and gets a page of its own. An item with no lesson yet is listed
    apart. It can still be worked, but it isn't a step on the path, and mixing
    it in would hide that.
    """
    if lessons is None:
        lessons = {
            name: lesson_of(name, item)
            for name, item in items.items() if lesson_of(name, item).is_file()
        }
    steps, waiting = [], []
    for name in sorted(lessons):
        title = html.escape(_first_heading(lessons[name], name))
        if name in items:
            last = attempts.last(name)
            status = (
                f" <span class=\"status {_verdict_word(last)}\">{_verdict_word(last)}</span>"
                if last else ""
            )
            steps.append(
                f"  <li><a href=\"/item/{html.escape(name)}\">{title}</a>"
                f" <span class=\"title\">then practice: {html.escape(task_title(items[name]))}"
                f"</span>{status}</li>"
            )
        else:
            steps.append(
                f"  <li><a href=\"/lesson/{html.escape(name)}\">{title}</a>"
                " <span class=\"title\">a lesson to read, with nothing to practice yet</span></li>"
            )
    for name, item in items.items():
        if name not in lessons:
            last = attempts.last(name)
            status = (
                f" <span class=\"status {_verdict_word(last)}\">{_verdict_word(last)}</span>"
                if last else ""
            )
            waiting.append(
                f"  <li><a href=\"/item/{html.escape(name)}\">{html.escape(task_title(item))}</a>"
                f" <span class=\"title\">{html.escape(name)}</span>{status}</li>"
            )
    body = "<main>\n<h1>Orbis: Playwright</h1>\n"
    body += "<p class=\"hint\">Each step is a lesson, then an item to practice it on.</p>\n"
    body += "<ol id=\"course\">\n" + "\n".join(steps) + "\n</ol>\n"
    if waiting:
        body += (
            "<section id=\"waiting\">\n<h2>Practice items waiting for a lesson</h2>\n"
            "<p class=\"hint\">These work, but they aren't on the path yet.</p>\n"
            "<ul>\n" + "\n".join(waiting) + "\n</ul>\n</section>\n"
        )
    return _shell("Orbis", body + "</main>")


def render_lesson_page(name, path):
    """A lesson with no practice item behind it, on a page of its own."""
    body = (
        "<main>\n<p class=\"crumbs\"><a href=\"/\">the course</a></p>\n"
        f"<section id=\"lesson\">\n{_MARKDOWN.render(path.read_text())}</section>\n</main>"
    )
    return _shell(_first_heading(path, name), body)


def _spec_name(name):
    return f"mine/{name.rsplit('/', 1)[-1]}.spec.ts"


def render_app(name, url):
    """Where the learner drives the real app while writing tests.

    The tests are written against the live page, so it's one click away. Only
    the real app is served here. The broken copies never get a URL, since
    exploring them first would mean testing the breaks instead of the rules.
    """
    url = html.escape(url)
    spec = html.escape(_spec_name(name))
    run = f"BASE_URL={url} npx playwright test {spec}"
    return (
        "<section id=\"app\">\n<h2>The app</h2>\n"
        f"<p>The real app is running at <a href=\"{url}\" target=\"_blank\">{url}</a>."
        " Poke at it, watch what changes and when, and write your tests against it.</p>\n"
        f"<p class=\"hint\">Write your tests in <code>learner/{spec}</code>. In a shell,"
        " after <code>source env.sh</code> and <code>cd learner</code>:</p>\n"
        "<table>\n"
        f"<tr><td>record clicks as test code, and pick up selectors</td><td><code>npx playwright codegen --target playwright-test {url}</code></td></tr>\n"
        f"<tr><td>run your tests step by step, with the page beside them</td><td><code>{run} --ui</code></td></tr>\n"
        f"<tr><td>watch your tests run in a browser</td><td><code>{run} --headed</code></td></tr>\n"
        f"<tr><td>pause on each action with the inspector</td><td><code>{run} --debug</code></td></tr>\n"
        "</table>\n</section>"
    )


def render_attempt(name, last):
    """The gate's verdict on the learner's latest file, cell by cell."""
    command = (
        f"uv run python -m orbis.gate attempt items/{html.escape(name)}"
        f" --candidate learner/{html.escape(_spec_name(name))}"
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
            f"<code>npx playwright show-trace {html.escape(t)}</code>"
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


def lesson_of(name, item):
    """The lesson that comes before an item, kept beside items/ in lessons/."""
    return item.parents[2] / "lessons" / f"{name}.md"


def render_lesson(name, item):
    path = lesson_of(name, item)
    if not path.is_file():
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
    if lesson_of(name, item).is_file():
        task = "<p class=\"step\">Practice</p>\n" + _demote(task)
    rows = []
    for number, text, margin in worked_lines(reference_of(item)):
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
        f"{render_lesson(name, item)}"
        f"<section id=\"task\">\n{task}</section>\n"
        f"{render_app(name, app_url) if app_url else ''}\n"
        f"{render_attempt(name, last)}\n"
        "<section id=\"answer\">\n<h2>The worked answer</h2>\n"
        "<p class=\"hint\">Write your own attempt first. Each line opens on its own,"
        " and the margin says what kind of line it is.</p>\n"
        "<ol class=\"lines\">\n" + "\n".join(rows) + "\n</ol>\n</section>\n</main>"
    )
    return _shell(task_title(item), body)


def _handler(items, log, attempts, apps, lessons):
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
                page = render_index(items, attempts, lessons)
                return self._send(200, "text/html; charset=utf-8", page)
            if path.startswith("/lesson/"):
                name = path[len("/lesson/"):]
                if name in lessons:
                    page = render_lesson_page(name, lessons[name])
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
            lines = {n: text for n, text, _ in worked_lines(reference_of(items[name]))}
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

    def __init__(self, items_root, log_path, port=0, attempts_path=None):
        self.items = find_items(items_root)
        self.log = pathlib.Path(log_path)
        attempts = pathlib.Path(attempts_path or self.log.parent / "attempts.jsonl")
        self.apps = {
            name: Site(item / "app", port + 1 + index if port else 0)
            for index, (name, item) in enumerate(self.items.items())
        }
        handler = _handler(
            self.items, progress.RevealLog(self.log), progress.AttemptLog(attempts),
            self.apps, find_lessons(items_root),
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
    parser.add_argument("--items", default="items", help="the items directory")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="where reveals go")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    with Server(args.items, args.log, args.port) as running:
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
