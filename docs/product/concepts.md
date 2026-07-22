# Concepts

The vocabulary. **This is the single source for the concept model** — every other doc, the
CLI help, and the code use these words in this sense, and none of them redefine them.

## Profile

The structured resume data — one file, [JSON Resume](https://jsonresume.org/schema) schema.
**The only thing you edit.** Everything else is derived from it.

A profile is a **master superset**, not a finished document: it holds every skill, every role,
every bullet ever written, including things no single resume would show. Curating down to
what one employer sees is a *rendering* decision. **Nothing is deleted from the profile to
make a document shorter.**

Schema details, including the local extensions, are in
[`../technical/data-model-and-config.md`](../technical/data-model-and-config.md).

## Axis

One independent presentation choice. Seven of them:

| Axis | Values | What it varies |
|---|---|---|
| `palette` | 7 | Colour scheme — `harbor`, `ink`, `moss`, `clay`, `plum`, `slate`, `crimson` |
| `typeface` | 4 | Type pairing — `grotesk`, `humanist`, `charter`, `mixed` |
| `header` | 5 | Name/contact block — `band`, `masthead`, `rule`, `split`, `minimal` |
| `skills` | 3 | Skills section — `pills`, `inline`, `grid` |
| `promo` | 4 | How a title line reads within a role — `ladder`, `badge`, `stacked`, `inline` |
| `density` | 3 | Vertical rhythm — `airy`, `normal`, `compact` |
| `grouping` | 2 | Whether a promotion reads as one tenure or separate roles — `grouped`, `flat` *(experimental)* |

Axes are **independent and categorical**: changing one changes exactly one thing. That is
what makes the space browsable rather than chaotic, and it is worth protecting.

**Adding an axis is not free.** `grouping` doubled the space, added a segment to every spec
name, and does nothing at all for a profile with no promotion. Prefer new *values* on existing
axes — they multiply the space without lengthening a name or adding a lever that is inert for
some documents.

## Spec

One point in the space — a value on every axis — named by spelling out each value in a fixed
order, `palette-typeface-header-skills-promo-density-grouping`:

```
harbor-grotesk-band-pills-ladder-airy-grouped
ink-charter-masthead-inline-stacked-compact-flat
```

A spec is **pure data**: no rendering, no IO. It is what you save, share and publish against,
which is why the name is written out rather than encoded — it must be **decodable without a
legend** and **stable forever**. See
[`../decisions/0003-spec-names-are-written-out-in-full.md`](../decisions/0003-spec-names-are-written-out-in-full.md).

Four named **presets** (`default`, `plain`, `editorial`, `warm`) are ordinary specs with
convenient names, not a separate system.

## Space

The product of all axes: **10,080 specs**. Not a curated gallery — a combinatorial space,
enumerated exhaustively and browsed with the axes as facets, so "every layout in this palette"
and "this layout in any palette but this one" are the same operation.

**Combinatorial, not curated.** There are 28 hand-authored axis values over one HTML
skeleton. 10,080 is what those multiply to, not a count of designs — and widening the space
means adding values or a second skeleton, never raising the multiplier. Stated plainly
because the number is otherwise easy to oversell.

## Variant

A profile rendered through a spec. The thing you look at. Variants are cheap and
disposable — HTML, generated on demand, never stored as source.

## Deliverable

The one published output you send: PDF, HTML and Markdown of a single chosen variant. There
is exactly one current deliverable at a time, and it is regenerated, never hand-edited. If a
workspace already names its deliverable something, publishing keeps that name rather than
introducing a second convention.

## Workspace

The folder holding a profile, its deliverable, its archive, and eventually cover letters and
applications. `init` scaffolds one. **The tool never stores content itself** — a workspace is
someone's private data and lives wherever they keep it.

---

## Terms deliberately not used

| Not this | Because |
|---|---|
| *theme* | Implies a hand-written artefact. Layouts are points in a space; `--theme` survives on the CLI only as a familiar flag name. |
| *template* | Reserved for the workspace `init` scaffolds, not for layouts. |
| *number* / *option N* | An ordinal is positional and catalogue-scoped. The spec name is the handle. |
| *favourite*, *session* | There is no session state. See [`../decisions/0002-browse-not-search.md`](../decisions/0002-browse-not-search.md). |
