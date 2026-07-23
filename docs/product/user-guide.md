# User guide

Install, first run, the workflow end to end, and what to do when something goes wrong. Assumes
the vocabulary in [`concepts.md`](concepts.md).

## Requirements

| | |
|---|---|
| **Python** | 3.11 or newer. Zero runtime dependencies — everything is stdlib. |
| **A Chromium-family browser** | Chrome, Chromium, Edge or Brave. Used **only** for PDF export, and located at runtime. Everything else works without one. |
| **A coding agent** *(recommended)* | The intended interface. `init` installs a skill that teaches it the workflow. |

Set `RESUME_PIPELINE_CHROME` to an executable path if the browser is somewhere unusual.

## Install

```sh
pipx install git+https://github.com/dberardi2020/resume-pipeline.git
```

Or from a checkout, with no install at all:

```sh
git clone https://github.com/dberardi2020/resume-pipeline.git
cd resume-pipeline
python3 -m venv .venv && .venv/bin/pip install -e .
python3 -m resume_pipeline --help
```

## First run

```sh
resume-pipeline init ~/Career
```

That writes a workspace and does not overwrite anything that already exists:

```
~/Career/
  CLAUDE.md                        the working rules, including anti-fabrication
  README.md                        orientation
  .claude/skills/career/SKILL.md   the agent skill
  Resume/resume.json               a starter profile to fill in
  Resume/Archive/                  pre-edit snapshots go here
  Cover Letters/  Applications/  Reference/
```

Then fill in `Resume/resume.json`. If you would rather see the tool working before writing
anything, point it at the demo profile that renders every screenshot in these docs:

```sh
resume-pipeline catalogue docs/assets/demo-profile.json
```

> **Importing an existing resume is not built yet** (RP-0001) — today you transcribe once.
> It is the biggest gap in the tool and it is the top of the backlog.

## The workflow

Five verbs. In practice you say what you want and the agent runs them.

### 1. Edit — through the agent

You describe the change; the agent edits `resume.json`. You do not hand-author structured
data, and you should not have to remember a command.

Two rules the skill installs into the workspace, which the agent reads before touching
anything:

- **Never invent a career fact.** No metric, date, scope claim, or technology. If a number
  would help, the agent asks for it and leaves the bullet unquantified until answered.
  Rewriting your own facts into stronger prose is the point; introducing new ones is not.
- **Never delete a skill from the profile.** Curation is a rendering choice.

Archive before a substantive rewrite — `Archive/YYYYMMDD-description.json`.

### 2. Lint — check it

```sh
resume-pipeline lint
```

Reports three levels: `ERROR` (likely to be mis-parsed or auto-rejected), `WARNING` (weakens
the resume; a deliberate choice may override), `INFO` (worth a look, often intentional). Only
errors fail the command, so it is usable in CI without forcing every nit.

**It never edits.** A finding is a question, not a task to silence. Full rule list in
[`../technical/module-reference.md`](../technical/module-reference.md#lintpy).

### 3. Browse — find a layout

Two deliveries of the same viewer.

```sh
resume-pipeline catalogue      # a folder of HTML you open from file://
resume-pipeline serve          # the same viewer, with a process behind it
```

`catalogue` writes a self-contained folder into the cache and prints a `file://` link — no
server, and you can commit it or send it to someone. `serve` renders previews on request and
adds two actions the static version cannot have: **Export PDF**, and **Make this my resume**,
which publishes directly.

Every preview is a **live render** — the same function that publishes — so nothing you see
can drift from what you get. Cards show each spec's axis values as chips; the full name is in
the detail view, and **Copy Name** puts it on the clipboard.

**Moving through the space** (served viewer): the arrows step one page at a time, **«** jumps
back to the first, and **Shuffle** lands somewhere else entirely. `[` and `]` page from the
keyboard. The static `catalogue` has no pages — it is a fixed spread across the whole space.

**Holding colour constant.** Palette is one of the seven axes, but the one the eye reacts to
first, so it has its own control. Pick a colour from the bar and every layout re-renders in
it — letting you judge *structure* without colour swinging the decision — or leave it on
**Varied** to see each layout's own palette. It works in the detail view too, so you can try a
layout you like in each colour. This is not a live edit: forcing a colour just asks for the
same layout's neighbouring spec, which is exactly what would publish.

> **Facet *filtering* is not built yet** (RP-0004) — you cannot yet say "only `charter`, only
> `moss`". Colour-pinning and paging are the pieces that exist; filtering the space down by any
> axis is the next step.

### 4. Publish — write the deliverable

```sh
resume-pipeline publish --theme harbor-grotesk-band-pills-ladder-airy-grouped
```

`--theme` takes a preset (`default`, `plain`, `editorial`, `warm`) or any spec name. Writes
`<Name>.pdf`, `.html` and `.md` beside the profile, overwriting in place — the folder always
answers "which file do I send?" If a deliverable is already there under another name, that
name is kept.

From the viewer, **Make this my resume** does the same thing with no name typed.

### 5. Cover letters — not built

Designed, unbuilt (RP-0009). `Cover Letters/` and `Applications/` are scaffolded and empty.

## Where files go

| | |
|---|---|
| **The profile and the deliverable** | In your workspace, beside each other. |
| **Everything else generated** | `~/.cache/resume-pipeline/<workspace>/` — catalogues, scratch exports. Safe to delete; rebuilding is instant and deterministic. |

Generated files never sit beside source. If your workspace is file-synced (Dropbox, iCloud, a
NAS), this is what keeps it from churning.

**Never create a virtualenv inside a synced workspace** — virtualenvs carry absolute paths and
per-machine binaries.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `no resume found` | No `resume.json` walking up from the working directory. Pass a path, set `RESUME_PIPELINE_RESUME`, or `cd` into the workspace. |
| `No Chrome/Chromium/Edge found` | PDF export needs one. Install it, or set `RESUME_PIPELINE_CHROME` to the executable. HTML and Markdown still work. |
| `unknown layout '…'` | Not a preset and not a valid spec name. Spec names have **seven** hyphen-separated segments; run `catalogue` to see real ones. |
| `error: <field> is … — expected ISO 8601` | Dates are `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. |
| `work[N] ends before it starts` | A date got transposed — usually a bad edit. Check the archive. |
| A published file does not match the preview | Should be impossible; previews call the same render function. Re-run `publish` and file a bug. |
| Two resumes in the folder | An older deliverable under a different name. Publishing now reuses an existing name, but a pre-existing pair may need deleting by hand. |

## Reference

Command surface, flags and exit codes:
[`../technical/module-reference.md`](../technical/module-reference.md#clipy).
