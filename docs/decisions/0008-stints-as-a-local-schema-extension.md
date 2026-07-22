# 0008 — Per-title bullets as a local schema extension

**Status:** Experimental · 2026-07-22

## Context

A promotion was decoration. `work[].promotions` recorded prior *titles* with dates but no
bullets, so nothing in the data could say which work was done at which level. Every layout
therefore rendered promotion as a caption — and the complaint that "most of these designs
don't do promotion well" was correct but misdiagnosed: the information was not in the file.

JSON Resume has no field for in-company progression. The alternatives were separate `work`
entries per title (stock schema, but the employer repeats and grouping becomes guesswork at
render time) or tagging individual bullets (smallest diff, but two shapes in one array).

## Decision

`work[].stints` — a list of titles held at one employer, each with its own dates and
`highlights`. Employer-level `highlights` remain, for work spanning the whole tenure. Legacy
`promotions` normalises into stints on read; carrying both is an error.

A **`grouping`** axis renders the two structural readings: `grouped` (employer as heading,
titles nested — one continuous tenure) and `flat` (each title its own heading, employer
repeated — separate roles, what parsers expect).

## Rationale

If a promotion is worth showing, what is worth showing is *what changed* — and that is the
bullets, not the title. Only a data model that attaches bullets to titles can express it.

## Consequences

- The `promo` axis now chooses how a title line **reads**, not whether progression is visible.
- `grouping` doubled the space and added a segment to every spec name — the concrete price of
  a new axis, recorded in [0003](0003-spec-names-are-written-out-in-full.md).
- For a role with no promotion, both grouping values render **identically**. The axis is inert
  for most documents.
- **This is why the status is Experimental.** No real document has exercised it: the author's
  own resume was migrated onto stints and then migrated back, because a flat bullet list plus
  a `note` said the same thing with less machinery. That is evidence, and it is recorded
  rather than hidden.
- Do not build further features on it. Promoting it requires a document that genuinely needs
  per-title bullets, and a check for an upstream JSON Resume field first (RP-0014, RP-0024).
