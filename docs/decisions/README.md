# Decisions

Architecture decision records. Each is one decision: **Context · Decision · Rationale ·
Consequences**.

**The ADRs carry the current decision state.** `product/` and `technical/` synthesise them —
when they disagree, the ADR is right and the synthesis is stale.

Numbers are four-digit, allocated in order, and **never renumbered or reused**, even when an
ADR is superseded.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-layouts-as-a-design-space.md) | Layouts are points in a design space, not hand-written themes | Accepted |
| [0002](0002-browse-not-search.md) | Browse the space with facets; no sampler, no session state | Accepted |
| [0003](0003-spec-names-are-written-out-in-full.md) | Spec names spell out every axis and are stable forever | Accepted |
| [0004](0004-one-viewer-two-deliveries.md) | One viewer, parameterised by delivery | Accepted |
| [0005](0005-generated-files-never-sit-beside-source.md) | Generated files live in a cache; only publishing writes to the workspace | Accepted |
| [0006](0006-the-linter-reports-it-never-edits.md) | The linter reports; it never edits | Accepted |
| [0007](0007-keep-the-in-house-renderer.md) | Keep the in-house renderer rather than adopting RenderCV | Accepted |
| [0008](0008-stints-as-a-local-schema-extension.md) | Per-title bullets as a local schema extension | Experimental |
