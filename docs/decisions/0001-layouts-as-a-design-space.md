# 0001 — Layouts are a design space, not hand-written themes

**Status:** Accepted · 2026-07-21

## Context

The tool began with four hand-written themes, several hundred lines each. Every new look cost
another theme, and each duplicated the section logic of the last. Meanwhile the actual need
was the opposite of a curated set: *many* candidates to flip through, because judging a layout
takes under a second and generating one should be cheaper than that.

## Decision

A layout is not code. It is a **`Spec`** — a value on each of several independent categorical
axes — and one renderer reads the spec and emits the HTML.

## Rationale

Adding a value to any axis **multiplies** the catalogue rather than adding one to it. Seven
axes and 28 hand-authored values produce 10,080 layouts. The axes being independent and
categorical is what makes the result browsable rather than chaotic: changing one changes
exactly one thing, which is also what gives distance a meaning (see
[0002](0002-browse-not-search.md)).

Constraining every axis to stay single-column and ≥10pt means *everything* the space can
produce is submittable. Character comes from colour, type and the treatment of details —
never from a layout that breaks parsing.

## Consequences

- The hand-written themes were retired. The four surviving names are **presets**: ordinary
  specs with convenient labels, not a separate system.
- Variety is bounded by the axis values, not by the multiplier. 10,080 is combinatorial, not
  curated — 28 values over **one HTML skeleton** — and widening the space means adding values
  or a second skeleton. This is stated in the README and concepts doc so the number is not
  oversold.
- Every generated layout can be published; nothing is browsable-but-unreachable.
- A test renders every spec in the space, because "by construction" only stays true if
  something checks the construction.
