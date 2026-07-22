# 0002 — Browse the space; do not search it

**Status:** Accepted · 2026-07-21

## Context

The first explorer treated the space as something to *sample*: it showed a batch, let you mark
favourites and rejects, and drew the next batch from the neighbourhood of what you liked —
steering. That required a persisted session file, a sampler with a seed, and an interaction
model where the tool guessed at your taste.

## Decision

**Browse, do not search.** The space is enumerated and shown; the axes are the facets. There
is no sampler, no seed, no favourites, and no session state anywhere.

## Rationale

The space is **finite, deterministic and categorical**. That is not true of most search
problems and it changes the answer completely: a catalogue with facets can express every
question a recommender could, and answer it exactly rather than approximately. "Every layout
in this palette" and "this layout in any palette but this one" are the same operation on the
same data.

Steering also carried hidden state that the user could not see, could not edit, and could not
sync — and which made two runs of the same tool disagree.

## Consequences

- `space.diverse` and `space.steer` were deleted, along with the verdict file and the
  favourite/reject UI. `distance` and `neighbours` stay: they are what remix and merge are
  built from.
- `spread(count)` replaces sampling — deterministic greedy farthest-point selection, no seed.
  The same count always yields the same layouts, so a catalogue can be rebuilt and compared.
- **The server holds no per-user state**, which is most of what a hosted version would
  otherwise have to solve. A test asserts the context keys so state cannot creep back.
- Faceted filtering in the UI is not built yet; the viewer shows a spread. That is a gap in
  the *interface*, not in the model.
