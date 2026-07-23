# qa/ — the acceptance layer

Two layers of testing, on purpose:

| Layer | Where | Speed | Covers |
|---|---|---|---|
| **Unit** | [`tests/`](../tests/) (pytest) | fast, mocked, in-process | logic, every branch, ~200 cases run in CI |
| **Acceptance** | `qa/acceptance.py` | slow, real, on-demand | the un-mockable surface: a subprocess command, a **live server**, **real PDF through a browser**, a fresh `init` |

The unit suite mocks the browser and calls `cli.main` in-process, so it is blind to
"does it actually work end to end on a real machine." That is this harness's job — it was
written after an acceptance run caught an archive-collision bug the unit tests missed.

```bash
python qa/acceptance.py     # non-zero exit if any check fails
```

Browser-dependent checks skip cleanly when no Chromium-family browser is present, so it runs
anywhere; a full run needs one for the PDF leg.

This is a proof of concept for a reusable **agentic QA harness** — a standard target a dev (or
an agent) runs to offload acceptance testing. The pattern, and where it is headed
(browser-driven checks of the viewer's JavaScript, a CI leg), is written up in Private KB:
`Private KB/Notes/agentic-qa-harness.md`.
