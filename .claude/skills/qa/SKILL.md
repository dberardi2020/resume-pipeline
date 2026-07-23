---
name: qa
description: Run this repo's tests. Use when asked to test, verify, QA, or check the resume-pipeline codebase, or before shipping a change to it. Two layers — fast unit tests (pytest) and the slow end-to-end acceptance harness (real browser + live server). This is a dev skill for working ON resume-pipeline; it is not shipped to user workspaces.
---

# QA — running resume-pipeline's tests

Two layers, run with the repo's venv. **Unset the polluted env vars first** — an installed
`.app` on this machine leaks `PYTHONHOME`/`PYTHONPATH` into the shell and breaks the venv:

## Unit — fast, mocked, run always

```bash
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python -m pytest -q
```

~200 cases, in-process, browser mocked. Run after any code change. This is what CI runs.

## Acceptance — slow, real, run before shipping user-facing changes

```bash
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py
```

Runs the command as a subprocess, drives a live `serve` server over HTTP, and exports a real
PDF through an actual browser, against a fresh `init` workspace — the un-mockable surface the
unit suite is blind to. Non-zero exit on any failure. Run it before shipping changes to
**publish, serve, the deliverable, PDF, or the scaffold/skills**. Needs a Chromium-family
browser for the PDF leg (those checks skip cleanly if none is present).

**Ship only when both are green.** If you touched behaviour the acceptance harness does not yet
cover, add a check to `qa/acceptance.py` in the same change — see `qa/README.md`.
