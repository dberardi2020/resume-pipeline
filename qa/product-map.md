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
  `harbor ink moss clay plum slate crimson`. Each swatch is `<button class="sw" data-p="moss" title="moss">`.
- **Type bar** (`#typeface`): its twin. A `.tf` "Varied" button (default) + 4 `.tf` sample chips —
  `grotesk humanist charter mixed` — each rendered *in its own face*. Each chip is
  `<button class="tf" data-t="charter" title="charter">`. Both bars appear in the detail dialog too
  (`#dlgPalette`, `#dlgTypeface`).
- **Holds FILTER the browse, server-side (RP-0033, changed 2026-07-23 — was an in-place overlay).**
  Clicking a swatch/chip sends the held axis as a query param to `/api/page`, which returns only
  matching layouts. So the browse **narrows**: hold `moss` → 1,440 layouts / 60 pages, `moss`+`charter`
  → 360 / 15; every card matches; **no 7×/4× redundancy** (the old overlay paged the full 10,080
  re-tinted). Holds **compose** and **persist across paging**; "Varied" (`data-p=""`/`data-t=""`)
  releases that axis. The header count **follows the filter** (see below).
- **Paging**: header shows `page N of <pages>` where `<pages>` tracks the *filtered* set (420
  unfiltered, 60 holding one palette, 15 holding palette+type); `«` first, `‹`/`›` prev/next, `[`/`]` keys.
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
| 2 | Colour hold = **filter** | click `moss` → header "1,440 layouts · holding moss · page 1 of 60", every card moss | 2026-07-23 ✅ (driven live) |
| 3 | Hold persists + no redundancy across paging | page 2 still all moss, different layouts (not the same design re-tinted) | 2026-07-23 ✅ (driven live) |
| 4 | Paging | `›` → "page 2 of 420" unfiltered, new layouts | 2026-07-23 ✅ |
| 5 | Detail modal | full-page render + publish controls | 2026-07-23 ✅ |
| 6 | Viewer publish | deliverable + real PDF + sidecar records the picked layout + archive-on-overwrite | 2026-07-23 ✅ |
| 7 | Typeface hold + compose (RP-0037) | click `charter` → all cards that face; `moss`+`charter` → "360 layouts · page 1 of 15", both held; release → back to 10,080/420 | 2026-07-23 ✅ (driven live) |
| 8 | Counts follow the filter (RP-0035) | header total & page count recompute per hold; `/api/page` returns live `total` | 2026-07-23 ✅ (driven live + acceptance) |

## Teardown (always — a QA cleans up)

Kill any `serve` you started (`kill <pid>`), remove temp workspaces (`rm -rf`), close the browser
tab you opened. Leave the machine as you found it.
