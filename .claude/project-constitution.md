---
# Project constitution — YAML front-matter
#
# Captured 2026-10-30, on the day the repo was published, by the session that
# built slice 1. Every field below was measured on this box rather than
# detected, because the repo is one day old and a detector would have had two
# files to go on.

shell:
  # No devbox.json and no flake.nix at the project root. The one environment
  # dependency is the nixpkgs Playwright browsers, and env.sh resolves that
  # through `nix build` rather than through a project shell.
  enter: ""
  run_prefix: ""

# uv, and NEVER pip. This is NixOS: `pip install` into the system is not how
# the box works. uv.lock is committed.
package_manager: uv

language:
  runtime: python
  # Capped BELOW 3.14 deliberately. uv picked CPython 3.14.6 on the first
  # sync and playwright has no wheel for it, and the error reads as a missing
  # playwright release rather than as a missing wheel for the interpreter.
  # pyproject.toml carries requires-python = ">=3.11,<3.14".
  version: "3.11"

# Not a lock-in posture, a measured absence: podman is NOT installed on this
# box, so nothing may reach for it. docker is present and is the route for a
# disposable learning target when one is needed.
forbidden:
  - podman

canonical_commands:
  # scripts/test is the REAL gate. It runs `selfcheck` on every item, which
  # grades the reference AND every candidate the item ships to be rejected.
  # Gating on anything less measures nothing, which is the whole argument the
  # project is built on.
  test: scripts/test
  lint: scripts/lint
  # EMPTY ON PURPOSE, and an empty verb here means no honest command exists
  # yet rather than that nobody got round to it. The predecessor project kept
  # every verb empty for a week for exactly this reason: naming a command that
  # fails by design asserts a canonical command that lies.
  build: ""
  dev: ""
  deploy: ""
  gen: ""

# The learner writes TypeScript Playwright (Frank, 2026-10-31), so learner/
# is a node workspace pinning @playwright/test 1.59.1, the exact version of
# the nixpkgs driver. Orbis itself is still Python under uv. npm is allowed
# for that one directory and nowhere else.
bypass_patterns:
  - "npm ci --prefix learner"
  - "npm install --prefix learner"
---

# Why these fields read the way they do

**`test` is the full run and there is no fast default.** `scripts/test --fast`
exists and skips every item that needs a browser, which is most of them. A fast
tier recorded as the canonical command would be the same class of lie the empty
verbs above are avoiding. Use `--fast` for tight iteration and gate on the
default.

**`lint` is ruff and it is green.** Keep it that way. Do not quiet a finding by
widening an ignore list. Fix it, or justify that one site with a comment above
the directive and say why.

**The absent verbs are the honest state of a one-day-old repo.** There is no
build step because the runtime is Python run in place. There is no `dev` server
because the page does not exist yet. There is no `deploy` because nothing is
deployed. Each becomes a real command the day something honest can fill it, and
not before.
