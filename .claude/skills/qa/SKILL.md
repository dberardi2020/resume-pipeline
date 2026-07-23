---
name: qa
description: Run (or, on first use in a repo, scaffold) this repo's QA. Use when asked to test, verify, QA, or check the codebase, or before shipping a change to it. A self-improving, three-layer system — unit tests, a deterministic acceptance harness, and an agentic browser pass — driven by a product map the agent reads first and updates last. Generic and portable: the method is here, the repo's specifics live in qa/product-map.md. Dev skill; not shipped to end users.
---

# QA

This skill is **generic** — the same method in every repo. Everything specific to *this* repo (the
run commands, the app's surfaces and flows, gotchas, the regression checklist) lives in
**`qa/product-map.md`**. Keep it that way: learn once, write it to the map, not into this skill.

## 1. Assess state

- **Warm** — `qa/product-map.md` exists. **Read it first**, so you act like someone who already knows
  the product instead of burning tokens relearning it. Then run the layers (§2), regression-check the
  map's checklist, explore any new surface, and **update the map last**.
- **Cold** — no `qa/` yet. Don't fake a pass. **Investigate**: what does the repo build (CLI / server
  / browser UI / file outputs / install path)? What is the *un-mockable* surface? How do you run it?
  Then **scaffold a minimal first version** — `qa/acceptance.*` and `qa/product-map.md` with a
  regression checklist tailored to what you found. Minimal on purpose; later runs refine it. This
  first run is how QA gets built here.

## 2. The three layers

Run the layers a change touches; ship only when they're green. Exact commands live in the map.

1. **Unit** — fast, mocked, in-process; the CI gate.
2. **Deterministic acceptance** (`qa/acceptance.*`) — the un-mockable surface as real processes: the
   installed command as a subprocess, a live server over real requests, a real (headless) browser
   render with the JS asserted, real output artifacts, a fresh setup from nothing. Non-zero exit on
   failure; skips cleanly when a dependency (e.g. a browser) is absent; `--open`/`--keep` for
   visibility.
3. **Agentic browser pass** — the interactions and *looks-right* the harness can't assert. Needs
   browser control (Claude for Chrome). Open the live UI, drive it per the map, report. **No browser
   control → say so and stop; never claim interactions you didn't run.**
   - *Default:* the **seasoned** pass alone — map-driven, cheap.
   - *On request/confirmation only:* add a **fresh-eyes** persona — a separate agent with no repo
     context that must NOT read the map (a real first-timer). Valuable for onboarding/first-impression
     but expensive (it explores blind); reserve it for milestones. When both run, reconcile into
     **consensus / unique / conflicts**.

## 3. Always: teardown

A QA cleans up. Kill any server you started, remove temp workspaces, close browser tabs you opened.

## 4. Improve as you go

Touched behaviour the harness doesn't cover? Add a check to `qa/acceptance.*` in the same change.
Learned anything — a flow, a selector, a gotcha? Add it to `qa/product-map.md`. Reading the map first
and updating it last is what keeps the next pass cheap.
