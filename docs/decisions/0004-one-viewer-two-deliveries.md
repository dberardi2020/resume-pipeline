# 0004 — One viewer, parameterised by delivery

**Status:** Accepted · 2026-07-21

## Context

There were two implementations of the same page. `catalogue.py` built a static grid of scaled
iframe previews with axis chips; `explore/ui.py` served a grid of scaled iframe previews with
axis chips. They shared no code — the same CSS variables, the same card structure and the same
scaling logic existed twice — and had already begun to drift.

## Decision

**One viewer.** `viewer.page(specs, resume, *, preview, exportable)` is the only UI, and the
two deliveries differ in exactly two switches:

- **where a preview comes from** — a sibling `<name>.html`, or a `/preview/<name>` route;
- **whether the page can act** — a served page can export and publish; a file on disk cannot,
  so those controls are absent rather than present and broken.

## Rationale

Duplicated UI drifts, always, and the drift is invisible until someone compares screenshots.
Both deliveries are genuinely wanted — a static folder can be committed, linked or sent, and a
`file://` path outlives a localhost URL — but that is a difference in *delivery*, not in
product.

## Consequences

- `explore/` was deleted; `catalogue.py` fell to 37 lines because the viewer does the work.
- **A test normalises the two outputs and asserts equality**, so a third difference cannot
  appear without someone deciding to add it.
- Preview HTML is always a **live render** — the same function that publishes — so nothing on
  screen can drift from what is produced. This is also why previews are HTML rather than
  pre-rendered images: an earlier version generated a PDF per variant at roughly a second
  each, which capped how much of the space was worth looking at.
- The viewer's JavaScript is asserted as a string and never executed. There is no browser in
  the test loop.
