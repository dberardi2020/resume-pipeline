# QA product map — resume-pipeline

**The seasoned QA agent's memory.** Read this *first* so you act like someone who already knows the
product, not a first-timer fumbling through it — that is the difference between a cheap pass and one
that burns tokens rediscovering the obvious. Update it *last* with anything you learned. The
**fresh-eyes** agent must NOT read this file — its value is not knowing.

This doubles as the **regression baseline**: the checklist at the bottom is what must still work.
Each run, re-verify it and add any new surface. Point-in-time — update the "last verified" line.

**This is a QA lens, not a second product doc.** Canonical facts live in the repo's own docs — the
[`## Testing`](../README.md#testing) section and [`docs/technical/testing.md`](../docs/technical/testing.md)
for the layers and run story, [`docs/`](../docs/README.md) and the ADRs for the product and its
decisions. This file **links** there and holds only the QA *delta*: exact selectors, drive techniques,
gotchas, and the regression checklist. If something here is really a product fact, move it to the doc
that owns it and link — duplication drifts.

## Run the app

```bash
# unset the polluted env first (an installed .app leaks PYTHONHOME/PYTHONPATH and breaks the venv)
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py           # deterministic layer
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py --open     # + watch the viewer
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python -m resume_pipeline serve <profile> --port 8790 --no-open
```

Use `docs/assets/demo-profile.json` (Jane Smith) as the fixture — never a real resume.

## The viewer (`serve`) — surfaces & flows

- **Grid** is `<div id="grid">` — **empty in the served HTML; JavaScript builds the cards.** So HTTP
  checks see nothing; you must render in a real browser to test it (`--dump-dom` counts cards, or
  drive it live). A full page is 24 cards.
- **Colour bar** (`#palette`): a `.sw-varied` "Varied" button (default) + 7 `.sw` swatches —
  `harbor ink moss clay plum slate crimson`. Click a swatch → every card recolours in place (first
  axis chip flips, e.g. `clay`→`moss`) **and the pin persists across paging**. Each swatch is a
  `<button class="sw" data-p="moss" title="moss">`.
- **Type bar** (`#typeface`, RP-0037): the colour bar's twin. A `.tf` "Varied" button (default) + 4
  `.tf` sample chips — `grotesk humanist charter mixed` — each rendered *in its own face*. Click one →
  every card re-renders in that typeface (the **second** name segment swaps; the typeface axis chip
  flips) and the pin **persists across paging** and **composes with the colour pin**. Each chip is a
  `<button class="tf" data-t="charter" title="charter">`. The dialog carries the same bar (`#dlgTypeface`).
- **Paging**: header shows `page N of 420`; `«` first, `‹`/`›` prev/next (top-right), `[`/`]` keys.
- **Card** → `Open` → **detail modal**: buttons `Copy Name`, `Export PDF`, `★ Make this my resume`,
  `Close`, plus its own colour bar. `★ Make this my resume` → `POST /api/publish` → writes the
  deliverable (real PDF + HTML + MD) + `.resume-pipeline.json` sidecar, archiving the previous.

## Driving it — hard-won technique

- **Get element coordinates from the DOM, do not pixel-hunt.** Swatches are 20px wide; a pixel
  guess lands in the gap and silently no-ops. Use `javascript_tool`:
  `[...document.querySelectorAll('#palette .sw')].map(e=>{const r=e.getBoundingClientRect();return{p:e.title,cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)}})`
  then click those centres. (Screenshot coords are CSS px; `innerWidth` was 704, `dpr` 2.)
- **Verify publish by the filesystem, at the dir the server actually serves** — not the toast, not
  the folder you *think* you served. Publish is server-side + a real ~2s PDF render.
- **Turn on `read_network_requests` BEFORE the action** you want to capture — tracking starts on
  first call, so a click made earlier won't be in it.

## Gotchas (read before diagnosing a "bug")

- **Stale-server / wrong-dir trap.** A `serve` from a previous session can still hold the port; your
  new `serve` then **fails silently on the port conflict and you drive the OLD server**, which
  publishes to *its* cwd. Symptom: publish returns 200 but "nothing is written" — because you are
  checking the wrong folder. Before trusting a publish check: `lsof -iTCP:8790 -sTCP:LISTEN` and
  `lsof -a -p <pid> -d cwd` to confirm which server and dir. Kill stale servers or use a fresh port.
  *(This one cost a false bug report on 2026-07-23 — do not repeat it.)*
- The starter/demo resume lints with an ERROR (placeholder bullet has no figure) — that is correct
  behaviour, not a failure.

## Regression checklist (the PIT)

Re-verify each; expected result in parens. Add new rows as surface grows.

| # | Behaviour | Expected | Last verified |
|---|---|---|---|
| 1 | Grid renders in a real browser | 24 cards from an empty `#grid` | 2026-07-23 ✅ |
| 2 | Colour-pin | click `moss` → all cards green, chip `clay`→`moss` | 2026-07-23 ✅ |
| 3 | Pin persists across paging | page 2 cards still moss | 2026-07-23 ✅ |
| 4 | Paging | `›` → "page 2 of 420", new layouts | 2026-07-23 ✅ |
| 5 | Detail modal | full-page render + publish controls | 2026-07-23 ✅ |
| 6 | Viewer publish | deliverable + real PDF + sidecar records the picked layout + archive-on-overwrite | 2026-07-23 ✅ |
| 7 | Typeface-pin (RP-0037) | click `charter` → all cards in that face, chip `grotesk`→`charter`, persists across paging, composes with colour | 2026-07-23 ⚠️ render + unit + dump-DOM only; **live click not yet driven** |

## Teardown (always — a QA cleans up)

Kill any `serve` you started (`kill <pid>`), remove temp workspaces (`rm -rf`), close the browser
tab you opened. Leave the machine as you found it.
