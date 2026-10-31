"""What the runtime remembers between sittings, as two append-only files.

Reveals say which lines of a worked answer were opened and when. Attempts say
what the gate made of the learner's own file. Both are facts about something
that happened, and nothing here turns them into a score. The predecessor's
mastery numbers came from a model's opinion of its own dialogue, which looked
quantitative and measured nothing.
"""

import datetime
import json
import pathlib
import threading


def _now():
    return datetime.datetime.now(datetime.UTC).isoformat()


class _Log:
    """One JSON record per line, appended and never rewritten."""

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self._lock = threading.Lock()

    def append(self, record):
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as out:
                out.write(json.dumps(record) + "\n")

    def records(self, item=None):
        if not self.path.exists():
            return []
        found = [json.loads(raw) for raw in self.path.read_text().splitlines()]
        return [r for r in found if item is None or r["item"] == item]


class RevealLog(_Log):
    def record(self, item, line):
        self.append({"item": item, "line": line, "at": _now()})

    def revealed(self, item):
        return {r["line"] for r in self.records(item)}


class AttemptLog(_Log):
    def record(self, item, candidate, accepted, cells):
        self.append({
            "item": item,
            "candidate": str(candidate),
            "accepted": accepted,
            "cells": cells,
            "at": _now(),
        })

    def last(self, item):
        found = self.records(item)
        return found[-1] if found else None
