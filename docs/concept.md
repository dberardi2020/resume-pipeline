# resume-pipeline — Concept

*An agent-first way to edit, store, browse and export a resume.*

This is a **target** concept, not an as-built one: it describes what v1 is, and what the
tool is growing toward. Where something does not exist yet it says so. The
[As-built](#as-built--what-actually-exists-today) section at the end is the honest ledger.

## The idea, in one paragraph

Your resume is data, not a document. Keep it that way: one structured **profile** that is
the only thing you ever edit, a **space** of layouts you browse rather than design, and a
single **deliverable** you publish when you find one you like. The editing happens through
a coding agent — you describe the change and it makes it — so the tool's job is not to be
a text editor. Its job is to make agent edits **visible and safe**, and to make the
resulting document **findable** among thousands of possible presentations of it.

**The architecture, in one line.** Rendering is a pure function — `render(profile, spec)`
— so every surface (the agent skill, the inspector, the explorer, the publisher) is a
different way of calling it, and none of them owns the data.

---

## Model, in six words

### Profile

The structured resume data — one file, [JSON Resume](https://jsonresume.org/schema)
schema. **The only thing you edit.** Everything else in this document is derived from it.

A profile is a **master superset**, not a finished document: it holds every skill, every
role, every bullet you have ever written, including things no single resume would show.
Curating down to what one employer sees is a *rendering* decision, made per variant.
**Nothing is ever deleted from the profile to make a document shorter.**

### Axis

One independent presentation choice. Six of them today:

| Axis | What it varies |
|---|---|
| `palette` | Colour scheme |
| `typeface` | Type pairing |
| `header` | Name/contact block treatment |
| `skills` | How the skills section is laid out |
| `promo` | How in-role progression is shown |
| `density` | Vertical rhythm — compact through airy |

Axes are **independent and categorical**: changing one changes exactly one thing. That
property is what makes the space browsable instead of chaotic, and it is worth protecting
when adding a seventh.

### Spec

One point in the space — a value on every axis — named by spelling out each axis value in
a fixed order, `palette-typeface-header-skills-promo-density`:

```
harbor-grotesk-band-pills-ladder-compact
ink-charter-masthead-inline-stacked-airy
```

A spec is **pure data**: no rendering, no IO. It is what you save, share, and publish
against — and that is exactly why the name is written out in full rather than encoded.
A spec name must be **decodable without a legend** and **stable forever**: adding a new
value to an axis must never change what an existing name refers to, or every saved and
published spec silently starts pointing somewhere else.

### Space

The product of all axes: **5,040 specs today**. Not a gallery someone curated — a
combinatorial space, enumerated exhaustively and browsed with facets. The axes *are* the
facets, so "show me every layout in this palette" and "this layout in any palette but
this one" are the same operation.

### Variant

A profile rendered through a spec. The thing you actually look at. Variants are cheap and
disposable — HTML, generated on demand, never stored as source.

### Deliverable

The one published output you send to someone: PDF, HTML and Markdown of a single chosen
variant. There is exactly one current deliverable at a time, and it is regenerated, never
hand-edited.

> **And one container:** a **Workspace** is the folder holding your profile, your
> deliverables and your applications. `init` scaffolds an empty one; the tool never
> stores your content itself.

---

## The four surfaces

Each surface serves one verb, and they all sit on the same pure render function.

### 1. The skill — *edit*

The primary interface. A packaged Claude Code slash command shipped with this repo (the
same pattern as `terminal-launcher`'s `/restore`) that installs into a workspace and
teaches an agent the rules: where the profile lives, what it may change, and what it must
never invent.

**Editing is conversational.** You say what you want; the agent edits the profile. You do
not type structured data by hand, and you should not have to remember a command to make
something happen — if a turn ends by telling you to run a command, the surface has failed.

### 2. The inspector — *see what changed*

A **read-only** live view of the profile, in a browser, that updates as the profile
changes and shows **what just changed** — a diff, not a dump.

This exists for one reason: watching an agent rewrite your career history is unnerving
when you cannot see it happening. The inspector is the antidote. It is deliberately
**not** a formatted render and **not** an editor — it sits *before* presentation, and
writes stay with the agent so there is never a question of who owns the file.

This is also where the **safety net** is visible: the pre-edit archive, the diff, and
(later) per-claim provenance.

### 3. The explorer — *browse*

A faceted catalogue over the whole space. You do not design a layout and you do not
generate a fixed batch of them — you **browse**, filtering and grouping by axis, until
something looks right.

Two consequences worth stating, because they are what makes this simple:

- **No search, no steering, no favourites.** The space is finite, enumerable and
  deterministic. A catalogue with facets answers every question a recommender would, and
  needs no session state.
- **"I like this layout but not that colour" is a filter,** not a feature. Hold five axes,
  clear the sixth.

One viewer serves both the live and exported cases; there is no second UI.

### 4. Publish — *export*

Take one spec, write the deliverable — PDF, HTML, Markdown — into the workspace. Every
spec in the space is publishable; nothing is browsable-but-unreachable.

### Running through all four: the lint gate

A layout linter (parse-safety) and a content linter (structure, vagueness, gaps) that any
surface can call. It **reports**; it never edits. See [Guardrails](#guardrails).

---

## Where things live

The tool holds **no content**. The workspace holds **no code**. This split is what lets
the tool be published while your resume stays private.

```
resume-pipeline/                 your workspace/
  the tool. generic.               your content. private.
  ─────────────────                ──────────────────────
  render / lint / browse           profile   (the data you edit)
  the axes and the space           renders   (the current deliverable)
  the packaged skill        ──▶    archive   (pre-edit snapshots)
  the workspace template           letters, applications
```

The tool is installed into the workspace and finds the profile by walking up from the
working directory. Nothing in the tool knows your name; nothing in the workspace is code.

**Three artifacts, deliberately distinct** — conflating them is the failure mode this
section exists to prevent:

1. **The tool** — generic, public, zero personal content.
2. **The workspace template** that `init` scaffolds — generic; a starting point, not
   anyone's actual resume.
3. **Someone's workspace** — personal, private, never in this repo.

---

## Guardrails

These are constraints on the product, not features of it.

### Never invent a fact about someone's career

No metric, no date, no scope claim, no technology they did not use. **The tooling itself
creates the pressure to break this rule** — the content linter flags unquantified bullets,
and the obvious way to satisfy it is to supply a number. Supplying that number is
misrepresentation, and the person who has to defend it in an interview is not the one who
wrote it.

Flagging a missing number is useful. Filling it in is not. **Ask instead**, and leave the
bullet unquantified until it is answered. Rewriting someone's own facts into stronger prose
is fine and is the point; introducing new facts is not.

### Never delete from the profile

The profile is a superset built over years. Rendering a shorter document is selection, not
deletion. Any curation feature operates on the *variant*.

### Justify layout rules by mechanism, never by magnitude

The evidence base for applicant-tracking-system advice is polluted. The ubiquitous "75% of
resumes never reach a human" traces to a vendor that folded in 2013 without ever publishing
a study, and the skeptical counter-statistics are no better sourced.

What survives is **mechanism**: parsers extract text top-to-bottom, left-to-right, so a
two-column layout demonstrably scrambles reading order. That is verifiable and sufficient.
Every generated layout is single-column and ≥10pt **by construction**, and the linter
explains *what* breaks, never *how often*.

### Archive before writing

Every edit that touches the profile snapshots it first. Cheap, and it is the difference
between an agent you supervise and an agent you fear.

---

## v1 — what "done" means

v1 is **the version that can be published**. Two tests, both from the outside:

> Someone who has never seen this repo can find out what it is, install it, and use it —
> and the answer to each is easy and agent-installable.

> Every piece fits together in a way that can be explained on one page. If it can't be,
> the scope is wrong, not the explanation.

In scope:

- The four surfaces above, working end to end, driven by an agent rather than by hand-run
  commands.
- The explorer browsing **the whole space** with facets — as many options as you care to
  look at, not a batch of twenty.
- The read-only inspector with pre-edit archiving and a visible diff.
- One viewer, not two. One theme system, not two.
- The skill **shipped in this repo**, with an installer, and free of any personal content.
- README to the standard of the sibling repos: value proposition, badges, a picture, this
  vocabulary, requirements, install, a **"hand it to your coding agent"** paste block, a
  command table, roadmap, docs index.
- Tests and CI. Golden-file renders per spec, invariants on the space, linter cases, and a
  PDF text-extraction smoke test.
- A plain-language explanation of what an applicant tracking system is and why the layout
  rules exist — the linter is meaningless without it.

Explicitly **not** in v1: everything in the next section.

---

## Beyond v1 — the shape it grows into

Not commitments. This is the vision the v1 architecture must not foreclose.

**Getting data in.** *Import an existing resume* (PDF/DOCX → profile) is the adoption
cliff for this entire category — every comparable tool requires hand-authoring structured
data before anything works. Extraction has a checkable oracle: every extracted string must
appear in the source, so a hallucinated field can be rejected mechanically. The verifier
ships with the extractor, not after it.

**Trusting what comes out.** A *provenance model* — per claim, is this a human-asserted
fact or model-generated prose? — with explicit confirmation before any new figure renders.
Nothing in this space ships it, and it is the necessary counterweight to a linter that asks
for numbers.

**More documents.** *Cover letters* are the same data model plus a job posting, and
*applications* are the object that ties a posting, a tailored variant and a letter
together. Modelling the application rather than the resume as the primary object is the
long-term shape.

**More control over presentation.** *Remix* (pin a layout, walk one axis), *merge* (take
two layouts you like and browse everything between them), and *loadouts* (named partial
specs — a middle ground between one-click themes and per-axis fiddling) are all the same
move: constrain some axes, browse the rest. Each generalises what v1 already does with
facets rather than adding a mechanism beside it — merge in particular is enumerable, not
random, since two specs differing on *k* axes span exactly 2^k specs. A *drag-and-drop
builder* sits on top of these, and only makes sense after the next item.

**A content space alongside the style space.** Today a spec describes presentation only.
Section ordering, short/long bullet variants, and which subset of the master skills render
are all *content* choices — and the correct home for per-variant curation, which is
selection over the master profile and never deletion from it. The explorer would then
browse the product of both spaces.

**Somewhere to put it.** *Copy-paste blocks* with per-field character limits for LinkedIn
and application forms, since no official API accepts a profile write.

**A hosted version.** Plausible later, and therefore a constraint now: **do not assume a
local filesystem or a single user.** Rendering is already pure and the explorer already
speaks a small HTTP API; the cache directory, the upward walk for the profile, and shelling
out to a local browser for PDF are the parts that assume otherwise. The job is to keep the
boundary clean and documented — not to build hosting.

---

## Principles

- **Agent-first, not agent-optional.** The command line is the substrate the agent drives.
  A human-facing workflow that requires memorising commands has failed.
- **Data in one place.** One profile, edited once, rendered many ways. No format is
  authoritative except the profile.
- **Generated files are disposable** and never live beside source.
- **Enumerate rather than recommend.** A finite space with good facets beats a
  recommender with hidden state.
- **The tool is public; the content never is.** Every feature must be describable without
  reference to any particular person's resume.
- **Explainable in one page,** or out of scope.

---

## As-built — what actually exists today

Honest ledger, so this document does not overstate the repo.

| Area | State |
|---|---|
| Pure `render(profile, spec)` | **Exists** |
| Six axes, 5,040-spec space | **Exists** |
| Spec naming | **Index-encoded and unstable** (`harbor-321-mixed-compact`) — adding an axis value renames existing specs; to be replaced with the fully-worded form above |
| Layout + content linter | **Exists** |
| Publish to PDF/HTML/Markdown | **Exists** |
| `init` workspace scaffold | **Exists** |
| Explorer / catalogue | **Two overlapping implementations** — to be collapsed to one |
| Hand-written themes | **Duplicate** the generated system — to be retired or absorbed |
| Steering / neighbourhood sampling | **Exists but unused** by this concept — defer or delete |
| Inspector | **Does not exist** |
| Faceted browse | **Does not exist** |
| Packaged skill in this repo | **Does not exist** — lives only in a private workspace |
| Tests, CI | **Do not exist** (empty `tests/`, empty `.github/`) |
| README, product/technical docs, ADRs | **Stubs and empty directories** |

---

## Open questions

1. **Rendering 5,040 variants for browse.** On-demand rendering with pagination is the
   obvious answer; whether the exported (static) catalogue can offer the same facets over
   a subset, and how that subset is chosen, is not settled.
2. **Where the inspector runs.** The explorer already serves HTTP; whether the inspector
   is a route on the same server or a separate surface is undecided.
3. **A seventh axis** would take the space past 5,040 and past what a static export can
   hold. The threshold at which browse needs a different answer is unknown.
4. **Retiring the hand-written themes.** One of them is two-column and deliberately not
   parse-safe, so it cannot be expressed as a spec. Keep it as the single exception, or
   drop it.
