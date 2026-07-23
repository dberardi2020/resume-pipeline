# 0010 — Publish preserves the previous design

**Status:** Accepted · 2026-07-23

## Context

Publishing overwrites one fixed set of names in place (ADR-0004, ADR-0009) — that is what keeps a
folder answering "which file do I send?" with a single deliverable. But overwrite-in-place is
*destructive*: re-publishing after a layout or content change silently discards the version that
was there, with no way back. For a document people iterate on and send to employers, losing the
last-sent version is the wrong default.

The workspace already has an `Archive/` folder (the scaffold creates `Resume/Archive/`, and the
skill's content-change workflow snapshots the *source* `resume.json` there before an edit). Nothing
snapshotted the *deliverable*.

## Decision

**Before `publish` overwrites, it copies the existing deliverable into
`Archive/<YYYYMMDD-HHMMSS>/` — the files plus the sidecar, so the snapshot is self-describing.**
The archive only ever grows; nothing already in it is read or touched. A first publish, with
nothing to preserve, archives nothing. Both publish surfaces get this, because both go through
`deliverable.write`.

## Rationale

- **Non-destructive by default.** The version you last sent is always recoverable, without the
  user having to remember to back it up.
- **Reuses the existing convention.** `Archive/` is already the workspace's snapshot location and
  is already created by `init`; the deliverable snapshot sits beside the source snapshots under the
  same `YYYYMMDD-…` scheme (a timestamped *folder*, since a deliverable is several files).
- **The tool stays out of the archive's contents.** It writes new folders and never reads or
  prunes what is there — the user's own archived files (some predating this tool) are inviolate.

## Consequences

- The folder accumulates one snapshot per publish. That is the price of never losing a design;
  deduping identical consecutive publishes and pruning old snapshots are refinements, not part of
  this decision.
- `publish` now writes to `Archive/` — the one place beyond the canonical deliverable that it
  touches in the workspace (ADR-0005 confined generated *scratch* to the cache; a preserved
  deliverable is not scratch).
- Publishing remains *replace-in-place* for the live deliverable. Keeping several published designs
  side by side at once is a different, additive model — tracked as RP-0031, deliberately not built.
