# 0011 — Skills split by intent, generic and refreshable

**Status:** Accepted · 2026-07-23

## Context

`init` shipped one `career` skill: a prose blob teaching the whole workflow. Two problems surfaced
in use. First, the single skill mixed two distinct intents — *work on the resume's content* (edit,
lint, publish) and *choose its look* (browse the layout space) — so every invocation loaded all of
it. Second, the deployed copy in a real workspace had **drifted** from the shipped template: it
listed commands that no longer existed, because a hand-customised skill and the template had no way
to re-converge. The drift was possible because personal context (target roles, a specific notes
path) had been baked *into* the skill, so nobody dared overwrite it.

## Decision

**Two skills, split by intent, both generic; personal context lives in the workspace `CLAUDE.md`;
`init --skill-only` refreshes them in place.**

- `career-resume-update` — resume *content*: edit, lint, publish. Carries the content-change
  workflow and points at `CLAUDE.md` for the anti-fabrication rule.
- `career-layouts-browse` — the resume's *look*: browse the design space, pick a layout, publish it.

**Names are verb-forward and prefixed.** `career` alone said nothing about what the skill *did*; the
names now lead with the object-and-verb (`resume-update`, `layouts-browse`) so an agent — or a human
scanning the `/` menu — reads the job off the name, while the shared `career-` prefix groups them and
dodges the built-in `/resume` command. Cover letters and applications are *not* in scope: the tool is
resume-only, so a `resume-update`-named skill no longer claims capability it lacks.

Neither skill contains anything about a particular person. Because they are generic, overwriting
them is safe, so `init --skill-only` force-writes them — that command is how a workspace re-syncs to
the current version rather than silently drifting.

## Rationale

- **Intent-shaped.** "Update my resume" and "show me other layouts" are different requests; separate
  skills match them precisely and keep each small and individually invocable.
- **Generic skills, personal workspace.** The rule that must never be missed — the anti-fabrication
  rule — lives in one place (`CLAUDE.md`), not copied across skills where it could drift. A skill
  that names no person is a skill any workspace can share and any `init` can overwrite.
- **Drift becomes impossible to sustain.** The whole failure was a customised skill with no
  re-sync path. Generic + `--skill-only` refresh closes it: the workspace's skills can always be
  made identical to what ships.

## Consequences

- A consuming workspace keeps its specifics (target roles, voice, open questions) in `CLAUDE.md` and
  `resume.json`; its two skills stay byte-identical to the shipped templates.
- Splitting `import` (RP-0001) into its own skill later fits this shape — another intent, another
  generic skill — but is out of scope here.
- The skill and workspace-`CLAUDE.md` texts are covered by the docs-match-the-code tests, so a
  command that stops existing fails CI rather than reaching a newcomer's quickstart.
