"""The judge a judged DeepEval run reaches, and the only way out of its sandbox.

A judged run still starts under `unshare -rn`, so it has no network at all.
What it gets instead is a Unix socket. A socket file crosses a network
namespace because it lives in the filesystem, and this bridge sits on the
far end of it, outside the sandbox, and forwards one kind of request to one
host: a chat completion to api.poe.com.

That buys three things a plain "let judged runs have the network" can't.

- The run can reach Poe's chat endpoint and nothing else, not OpenAI, not
  Confident AI, not the learner's favorite pastebin.
- The Poe key never enters the run. The bridge adds it on the way out, so a
  test file that prints its environment prints no key.
- The bridge rewrites the model and the temperature on every request, so the
  judge is pinned even for a request that didn't come through DeepEval's own
  model plumbing. The plugin the run loads pins it there too, and this is
  the backstop.

It also counts the calls and the tokens, which is how a selfcheck says what
it cost.
"""

import atexit
import http.server
import json
import os
import pathlib
import shutil
import socketserver
import ssl
import tempfile
import threading
import urllib.error
import urllib.request

# Measured 2026-11-06 (orb-f79.4) on the refund-policy item and a library-hours
# fact check, 3 runs each. gpt-5.4-nano scored a correct answer 0.6 and a
# polite one 0.0 for courtesy, so the reference couldn't hold its own cell.
# gpt-5.4-mini scored every one of 132 measurements 0.0 or 1.0, the right
# side of 0.75 every time, at about $0.0006 a call against nano's $0.00023.
MODEL = "gpt-5.4-mini"
UPSTREAM = "https://api.poe.com/v1/chat/completions"
PATH = "/v1/chat/completions"
KEY_VARIABLE = "POE_API_KEY"

# A ceiling on calls per gate process, so a runaway candidate can't spend
# without limit. A selfcheck of 02-refund-policy makes about 400.
MAX_CALLS = int(os.environ.get("ORBIS_JUDGE_MAX_CALLS", "1500"))
UPSTREAM_TIMEOUT_S = 120


def _tls():
    """A TLS context that can verify Poe, which uv's own Python can't here.

    uv's standalone CPython carries no CA bundle, and on NixOS nothing sits
    where it looks, so the default context fails every handshake.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context(cafile="/etc/ssl/certs/ca-certificates.crt")


class _Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class Bridge:
    """A judge endpoint on a Unix socket, forwarding to Poe with the key added."""

    def __init__(self, key, model=MODEL, max_calls=MAX_CALLS):
        self.key = key
        self.model = model
        self.max_calls = max_calls
        self.calls = 0
        self.refused = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self._lock = threading.Lock()
        self._context = _tls()
        # A socket path has to fit in about 100 bytes, so it goes in a short
        # temp directory rather than beside the run.
        self.directory = tempfile.mkdtemp(prefix="orbis-judge-")
        self.socket = str(pathlib.Path(self.directory) / "judge.sock")
        self._server = _Server(self.socket, self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def _handler(self):
        bridge = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass

            def address_string(self):
                return "judge"

            def _send(self, status, body):
                data = json.dumps(body).encode() if not isinstance(body, bytes) else body
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._send(403, {"error": {"message": "the judge only takes chat completions"}})

            def do_POST(self):
                if self.path.split("?")[0] != PATH:
                    self._send(403, {"error": {"message": f"the judge only takes POST {PATH}"}})
                    return
                length = int(self.headers.get("Content-Length") or 0)
                try:
                    request = json.loads(self.rfile.read(length) or b"{}")
                except ValueError:
                    self._send(400, {"error": {"message": "the request body isn't JSON"}})
                    return
                if not bridge._take_call():
                    self._send(429, {"error": {"message": (
                        f"the judge's budget of {bridge.max_calls} calls for this "
                        "gate run is spent")}})
                    return
                status, body = bridge._forward(request)
                self._send(status, body)

        return Handler

    def _take_call(self):
        with self._lock:
            if self.calls >= self.max_calls:
                self.refused += 1
                return False
            self.calls += 1
            return True

    def _forward(self, request):
        request["model"] = self.model
        request["temperature"] = 0
        request.pop("stream", None)
        upstream = urllib.request.Request(
            UPSTREAM, data=json.dumps(request).encode(), method="POST",
            headers={"Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                upstream, context=self._context, timeout=UPSTREAM_TIMEOUT_S
            ) as response:
                body = response.read()
                status = response.status
        except urllib.error.HTTPError as error:
            return error.code, error.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            return 502, {"error": {"message": f"the judge couldn't reach Poe: {error}"}}
        try:
            usage = json.loads(body).get("usage") or {}
        except ValueError:
            usage = {}
        with self._lock:
            self.prompt_tokens += usage.get("prompt_tokens") or 0
            self.completion_tokens += usage.get("completion_tokens") or 0
        return status, body

    def summary(self):
        text = (
            f"{self.calls} call(s) to {self.model}, {self.prompt_tokens} prompt "
            f"and {self.completion_tokens} completion token(s)"
        )
        if self.refused:
            text += f", {self.refused} refused over the budget"
        return text

    def close(self):
        self._server.shutdown()
        self._server.server_close()
        shutil.rmtree(self.directory, ignore_errors=True)


_bridge = None
_bridge_lock = threading.Lock()


def bridge():
    """The process's one bridge, started on the first judged run."""
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            key = os.environ.get(KEY_VARIABLE)
            if not key:
                raise SystemExit(
                    f"this item is judged, and {KEY_VARIABLE} isn't set, so no "
                    "judge can be reached. Set it to a Poe API key and run again."
                )
            _bridge = Bridge(key)
            atexit.register(_bridge.close)
        return _bridge


def used():
    """What the judge was asked for so far, or None when nothing was judged."""
    return _bridge.summary() if _bridge else None
