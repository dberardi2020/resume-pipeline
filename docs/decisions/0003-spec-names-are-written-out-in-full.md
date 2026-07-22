# 0003 — Spec names spell out every axis, and are stable forever

**Status:** Accepted · 2026-07-21

## Context

Spec names were partly index-encoded: `harbor-321-mixed-compact`, where `321` was positional
indices into the header, skills and promo lists. Three axes read as words, three as digits,
with no principle for which.

Two problems. The digits were undecodable without the source — and they encoded the three axes
that most define a layout's character. Worse, they were **positional**: adding a value to any
of those three lists renumbered thousands of existing names, so a spec someone had bookmarked
or published against silently came to mean a different layout.

## Decision

A spec name spells out every axis value, in axis order:

```
palette-typeface-header-skills-promo-density-grouping
harbor-grotesk-band-pills-ladder-airy-grouped
```

A name must be **decodable without a legend** and **stable forever**.

## Rationale

A spec is what you save, share and publish against. That is a contract, and the previous
scheme broke it silently — the worst way. Spelling values out costs characters and buys
permanence.

It also makes `parse()` a lookup per segment rather than a scan of the whole space, and makes
names greppable and sortable as text.

## Consequences

- Names are long — around 45 characters. Accepted deliberately, on the reasoning that if the
  name stops being the *handle* it stops mattering: the viewer leads with axis chips, offers
  **Copy Name**, and can publish directly, so nobody types one.
- A regression test inserts a value into an axis and asserts existing names are unchanged.
- **Adding an axis still breaks names** — it appends a segment. Adding a seventh (`grouping`)
  did exactly that. New *values* are free; new *axes* are not.
- Ordinals were dropped from the viewer and `options.json` for the same reason: an ordinal is
  positional and catalogue-scoped, which is the property this ADR rejects.
