"""An environment is a copy of the target app, with or without a mutation.

Mutations are patches rather than forks, so the diff is the statement of what
broke. Materializing one is a copy plus a git apply, which keeps the real app
as the only full copy anybody edits.
"""

import functools
import http.server
import os
import pathlib
import shutil
import subprocess
import threading


class MutationError(RuntimeError):
    pass


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


class Site:
    """Serve a directory on a loopback port, the kernel's pick unless given one."""

    def __init__(self, root, port=0):
        self.root = pathlib.Path(root)
        handler = functools.partial(_QuietHandler, directory=str(root))
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.port = self._server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
        return False


def materialize(app_dir, patch_path, dest):
    """Copy app_dir to dest and apply patch_path, if there is one."""
    app_dir = pathlib.Path(app_dir)
    dest = pathlib.Path(dest)
    shutil.copytree(app_dir, dest)

    if patch_path is None:
        return dest

    # Inside a git checkout, git apply reads the patch's paths from the top of
    # the checkout and skips any that fall outside the cwd, and it exits 0
    # having changed nothing. `gate attempt` keeps its runs under run/ in the
    # repo, so every mutation there was the real app. The ceiling stops git
    # from finding the checkout above dest, so it patches dest like a plain
    # directory.
    applied = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", str(pathlib.Path(patch_path).resolve())],
        cwd=dest,
        env={**os.environ, "GIT_CEILING_DIRECTORIES": str(dest.resolve().parent)},
        capture_output=True,
        text=True,
        check=False,
    )
    if applied.returncode != 0:
        raise MutationError(
            f"{pathlib.Path(patch_path).name} did not apply: "
            f"{applied.stderr.strip() or applied.stdout.strip()}"
        )
    return dest
