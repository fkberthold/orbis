"""The page: the built reading site, plus the parts that are live.

orbis.site builds the guides, the course and each item's task into a static
mkdocs-material site. This server serves that site and answers the questions
the site can't answer for itself: where each item's real app is running, what
the gate said about the learner's last attempt, and the lines of the worked
answer the learner has opened.

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
import http.server
import json
import mimetypes
import pathlib
import threading
import urllib.parse

from . import progress, runners, site, subject
from .environment import Site

DEFAULT_LOG = pathlib.Path("run") / "reveals.jsonl"


def find_items(subjects):
    """Every item of every subject, keyed subject/item."""
    found = {}
    for each in subjects:
        found.update(each.items())
    return found


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


def _verdict_word(attempt):
    return "accepted" if attempt["accepted"] else "rejected"


def _from_root(path):
    """A path as typed from the repo root, or as it is when it lies elsewhere."""
    path = pathlib.Path(path)
    try:
        return path.relative_to(subject.ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def app_part(name, item, url):
    """Where the learner drives the real app while writing tests.

    The tests are written against the live page, so it's one click away. Only
    the real app is served here. The broken copies never get a URL, since
    exploring them first would mean testing the breaks instead of the rules.
    """
    runner = runner_of(item)
    mine = runner.mine_name(name)
    workspace = subject.of_item(item).workspace
    return {
        "url": url,
        "lead": list(runner.app_lead()),
        "mine": mine,
        "workspace": _from_root(workspace),
        "commands": [
            list(row) for row in runner.app_commands(url, mine, item / "app", workspace)
        ],
    }


def grade_command(name, item):
    workspace = _from_root(subject.of_item(item).workspace)
    return (
        f"uv run python -m orbis.gate attempt {_from_root(item)}"
        f" --candidate {workspace}/{runner_of(item).mine_name(name)}"
    )


def attempt_part(item, last):
    """The gate's verdict on the learner's latest file, cell by cell."""
    if last is None:
        return None
    runner = runner_of(item)
    stem = pathlib.Path(last["candidate"]).name.split(".", 1)[0] + "-"

    def trace(path):
        # Playwright names a trace's folder after the spec and the test, so
        # the folder is the test's name once the spec's part is cut off. The
        # full command is long, so the page tucks it under that name.
        test = pathlib.Path(path).parent.name.removeprefix(stem).replace("-", " ")
        return {"test": test, "command": runner.trace_command(path)}

    return {
        "word": _verdict_word(last),
        "candidate": _from_root(last["candidate"]),
        "at": last["at"],
        "cells": [
            {
                "environment": c["environment"],
                "cell": c["cell"],
                "traces": [trace(t) for t in c.get("traces", [])],
            }
            for c in last["cells"]
        ],
    }


def answer_part(item, revealed):
    """The worked answer, with text only on the lines already revealed.

    A hidden line goes out as its number and margin, so its text is never in
    the browser until a reveal brings it.
    """
    lines = []
    for number, text, margin in worked_lines(item):
        if not text.strip():
            lines.append({"number": number, "blank": True})
        elif number in revealed:
            lines.append({"number": number, "margin": margin, "text": text})
        else:
            lines.append({"number": number, "margin": margin})
    return lines


def practice(name, item, revealed, last, app_url):
    """Everything live on an item's practice page, as orbis.js draws it."""
    return {
        "item": name,
        "app": app_part(name, item, app_url),
        "attempt": attempt_part(item, last),
        "grade": grade_command(name, item),
        "lines": answer_part(item, revealed),
    }


def _handler(items, log, attempts, apps, site_dir):
    site_dir = pathlib.Path(site_dir).resolve()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, kind, payload, headers=()):
            data = payload.encode() if isinstance(payload, str) else payload
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, status, value):
            self._send(status, "application/json", json.dumps(value))

        def _static(self, path):
            """A file of the built site, or its 404 page."""
            target = (site_dir / path.lstrip("/")).resolve()
            if not target.is_relative_to(site_dir):
                return self._send(404, "text/plain", "not found")
            if target.is_dir():
                if not path.endswith("/"):
                    return self._send(301, "text/plain", "", [("Location", path + "/")])
                target = target / "index.html"
            if not target.is_file():
                missing = site_dir / "404.html"
                if missing.is_file():
                    return self._send(404, "text/html; charset=utf-8", missing.read_bytes())
                return self._send(404, "text/plain", "not found")
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if kind.startswith("text/") or kind in ("application/javascript", "application/json"):
                kind += "; charset=utf-8"
            self._send(200, kind, target.read_bytes())

        def do_GET(self):
            path = urllib.parse.unquote(self.path.split("?", 1)[0])
            if path.startswith("/api/practice/"):
                name = path[len("/api/practice/"):]
                if name not in items:
                    return self._json(404, {"error": "no such item"})
                return self._json(200, practice(
                    name, items[name], log.revealed(name), attempts.last(name),
                    apps[name].base_url,
                ))
            if path == "/api/status":
                return self._json(200, {
                    name: _verdict_word(last)
                    for name in items if (last := attempts.last(name))
                })
            return self._static(path)

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
    """Serve the site on a loopback port and record reveals to a log file.

    The site is built first, or rebuilt when what it's built from has changed,
    so the pages served are never older than the subjects tree.

    The attempts log sits beside the reveals log unless told otherwise, which
    is where `gate attempt` writes by default.

    Each item's real app gets a port of its own, because the tests call
    page.goto("/") and that resolves to the root of the base URL. Served under
    a path, every one of them would land on the wrong page. With a fixed page
    port the apps take the ports right after it, so the addresses stay the same
    from one sitting to the next.
    """

    def __init__(self, subjects_root, log_path, port=0, attempts_path=None,
                 build_dir=site.BUILD):
        self.subjects = subject.find(subjects_root)
        self.items = find_items(self.subjects)
        self.site_dir = site.build(subjects_root, build_dir)
        self.log = pathlib.Path(log_path)
        attempts = pathlib.Path(attempts_path or self.log.parent / "attempts.jsonl")
        self.apps = {
            name: Site(item / "app", port + 1 + index if port else 0)
            for index, (name, item) in enumerate(self.items.items())
        }
        handler = _handler(
            self.items, progress.RevealLog(self.log), progress.AttemptLog(attempts),
            self.apps, self.site_dir,
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
        print(f"  site built in {running.site_dir}")
        for name, app in running.apps.items():
            print(f"  {name:<32} {app.base_url}", flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
