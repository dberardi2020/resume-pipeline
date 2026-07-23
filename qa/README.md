# qa/ — the acceptance layer

Testing here is layered on purpose:

| Layer | Where | Speed | Covers |
|---|---|---|---|
| **Unit** | [`tests/`](../tests/) (pytest) | fast, mocked, in-process | logic, every branch, run in CI |
| **Deterministic acceptance** | `qa/acceptance.py` | slow, real, on-demand | the un-mockable surface: a subprocess command, a **live server**, **real PDF through a browser**, a fresh `init` |
| **Agentic browser pass** | an agent with browser control | on-demand | the viewer's *interactions* (colour-pin, paging, publish) and whether it *looks right* |

The unit suite mocks the browser and calls `cli.main` in-process, so it is blind to "does it
actually work end to end on a real machine." That is the acceptance layer's job — it was written
after an acceptance run caught an archive-collision bug the unit tests missed.

```bash
python qa/acceptance.py     # non-zero exit if any check fails; --open to watch, --keep to inspect
```

Browser-dependent checks skip cleanly when no Chromium-family browser is present, so it runs
anywhere; a full run needs one for the PDF leg.

**`product-map.md`** is the companion: the accumulated knowledge of how to drive the app — its
surfaces, flows, gotchas, and a regression checklist — so an agent (or a person) runs QA like
someone who already knows the product rather than rediscovering it each time. It doubles as the
regression baseline: re-verify its checklist each pass, and add any new surface.
