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

## Agentic browser pass — for the viewer's interactions

The acceptance harness renders the viewer in a headless browser and confirms the JS *builds the
grid*, but it does not exercise **interactions** — colour-pin re-rendering, paging, "Make this my
resume". Those need a real browser being driven and *watched*, which is a job for you, not for a
harness dependency.

**If you have browser control** (Claude for Chrome, computer-use, or a browser MCP), run this pass
before shipping viewer changes:

1. Bring up the live viewer on a demo profile:
   `env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py --open`
   (it opens the viewer in a real browser and holds the server up), or run `serve` directly.
2. Drive it: click a **palette swatch** and confirm every card recolours; **page** forward/back
   (`[` / `]`, the arrows) and confirm the grid changes; open a card and hit **Make this my
   resume**, then confirm the deliverable was written.
3. **Look** — alignment, overflow, contrast in light and dark, anything a screenshot would show a
   human. Report what is off; this catches what assertions can't.

If you have no browser control, say so and stop at the deterministic harness — do not claim the
interactions were verified.

**Ship only when the layers you touched are green.** If you touched behaviour the acceptance
harness does not yet cover, add a check to `qa/acceptance.py` in the same change — see
`qa/README.md`.
