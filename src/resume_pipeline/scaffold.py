"""Scaffold a career workspace.

The tool renders resumes; it does not, on its own, tell you how to *work*. Anyone
who clones this is left holding a CLI and the question "so where do I put my
resume, and what happens when I want to tailor it for a job?" That answer is a
folder layout and a couple of rules, which is exactly the kind of thing that
should ship rather than be re-derived.

So `init` writes a workspace: somewhere for the resume, somewhere for cover
letters, somewhere for per-application artefacts, a `CLAUDE.md` carrying the rules
that matter, and a Claude Code skill so an agent picks all of it up without being
briefed.

Nothing here is required to use the CLI. It is the opinionated default for people
who want one.
"""
from __future__ import annotations

from pathlib import Path

STARTER_RESUME = """{
  "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/master/schema.json",
  "basics": {
    "name": "Your Name",
    "label": "Software Engineer | Your specialisms here",
    "email": "you@example.com",
    "phone": "(555) 555-5555",
    "location": { "city": "Your City", "region": "ST", "countryCode": "US" },
    "profiles": [
      { "network": "LinkedIn", "username": "you", "url": "https://www.linkedin.com/in/you" },
      { "network": "GitHub", "username": "you", "url": "https://github.com/you" }
    ],
    "summary": "Two or three headline sentences. Name a role, a specialism, and a scope signal. A generic summary is worse than none."
  },
  "skills": [
    { "name": "Languages", "keywords": ["..."] },
    { "name": "Frameworks & Libraries", "keywords": ["..."] },
    { "name": "Tools", "keywords": ["..."] }
  ],
  "work": [
    {
      "name": "Employer",
      "position": "Your Title",
      "location": "City, ST (Remote)",
      "startDate": "2024-01",
      "highlights": [
        "What you built, what it was built with, and what it was for."
      ]
    }
  ],
  "education": [
    {
      "institution": "Your University",
      "location": "City, ST",
      "studyType": "Bachelor of Science",
      "area": "in Computer Science",
      "endDate": "2020-12"
    }
  ]
}
"""

WORKSPACE_CLAUDE_MD = """# Career workspace

The live workspace for career work: the resume, cover letters, and job applications.
Scaffolded by `resume-pipeline init`.

This is a workspace, not an archive of records. Keep signed offer letters, payslips and
similar somewhere else — this folder is for things actively being worked.

## Layout

```
Resume/          resume.json (source of truth) + the published deliverable + Archive/
Cover Letters/   drafts and sent letters
Applications/    per-posting: the job posting + the tailored resume + the letter
Reference/       notes worth consulting while writing
```

## The anti-fabrication rule — read this before editing any resume content

**Never invent a fact about this person's career. Not a metric, not a date, not a scope
claim, not a technology they did not use.**

This rule exists because the tooling actively creates pressure to break it. The linter
flags bullets that contain no figures. The obvious way to satisfy the linter is to supply
a figure. **Supplying it is not your job.** A resume is a factual representation made to
employers; an invented "reduced p99 latency by 40%" is a misrepresentation they would have
to defend in an interview and cannot.

In practice:

- **Flagging** that a bullet lacks a number is useful. **Filling it in is not.**
- If a metric would strengthen a bullet, **ask**, and leave it unquantified until answered.
- Rewriting *their* facts into stronger prose is fine and encouraged. Introducing *new*
  facts is not.
- If unsure whether something is their claim or your inference, treat it as yours and ask.
- Never fill a gap with a plausible placeholder that reads like a real figure.

The line is not "AI helped write this" — that is normal and fine. The line is
**misrepresentation**, and invented metrics are the specific failure mode.

## Editing

`Resume/resume.json` is the source of truth. Everything else is generated — never hand-edit
a `.html`, `.md`, or `.pdf`, because the next publish overwrites it and the two then
disagree silently.

**Never delete a skill from the data.** A skills list is built over years. Curating which
skills appear in a given variant is a rendering choice, not a deletion.

Archive before a substantive rewrite. `Archive/` uses one scheme, `YYYYMMDD-description.ext`,
so it sorts chronologically:

```
cp Resume/resume.json "Resume/Archive/$(date +%Y%m%d)-pre-<change>.json"
```

## Commands

```
resume-pipeline lint                     # ATS + content checks
resume-pipeline publish --theme slate    # write the deliverable beside resume.json
resume-pipeline serve                    # interactive layout explorer
resume-pipeline themes
```

Paths are optional — commands walk up from the working directory to find `resume.json`.
Scratch renders go to `~/.cache/resume-pipeline/`; only `publish` writes here.

**Never create a virtualenv inside this folder** if it is file-synced (Dropbox, iCloud,
Drive, a NAS). Virtualenvs carry absolute paths and per-machine binaries.
"""

SKILL_MD = """---
name: career
description: Work on the user's resume, cover letters, and job applications — render, lint, explore layouts, or edit content. Use whenever the request involves their resume, a cover letter, a job posting or application, or resume layouts/themes/PDFs. Handles "update my resume", "render my resume", "show me layouts", "lint my resume", "export a PDF", "write a cover letter". (Named `career`, not `resume` — `/resume` is a built-in Claude Code command.)
---

# Career

The resume lives at `Resume/resume.json` ([JSON Resume](https://jsonresume.org/schema)).
Everything beside it is **generated** — never hand-edit a `.md`, `.html`, or `.pdf`, because
the next publish silently overwrites it.

The tool is `resume-pipeline`. It finds `resume.json` by walking up from the working
directory, so the path argument is optional.

## Commands

```bash
resume-pipeline lint                     # ATS + content checks
resume-pipeline publish --theme slate    # write the deliverable beside resume.json
resume-pipeline serve                    # interactive layout explorer (opens a browser)
resume-pipeline build --theme all        # scratch renders for comparison
resume-pipeline themes
```

**`publish` vs `build`.** `publish` overwrites the canonical `.pdf/.html/.md` beside
`resume.json` — that trio *is* the deliverable attached to an application. Use it after any
content change. `build` writes scratch to `~/.cache/resume-pipeline/` and is for comparing
options; never point `build --out` at the resume folder.

`serve` blocks until ctrl-c — run it in the background.

## Before editing content — the rule that overrides everything

**Read `CLAUDE.md` in the workspace root and follow its anti-fabrication rule.** Never invent
a fact about their career: no metric, no date, no scope claim, no technology they did not use.

The linter will flag unquantified bullets. **Do not resolve that by supplying a number.**
Flagging the gap is useful; filling it is misrepresentation they would have to defend in an
interview.

You may rewrite their facts into stronger prose, restore text from `Resume/Archive/`, and
compute figures that follow arithmetically from dates already in the data. Nothing else.

Also: **never delete a skill from `resume.json`.** Per-variant curation is a rendering
choice, not a deletion.

## Workflow for a content change

1. Archive first — `Archive/` uses `YYYYMMDD-description.ext`, describing what the snapshot
   is *before*: `cp Resume/resume.json "Resume/Archive/$(date +%Y%m%d)-pre-<change>.json"`
2. Edit `resume.json` only.
3. `resume-pipeline lint` — compare against the pre-edit baseline; never silence a finding
   with invented data.
4. `resume-pipeline publish --theme slate`
5. Report what changed, and list anything you needed but did not have.
"""

WORKSPACE_README = """# Career workspace

Scaffolded by [`resume-pipeline`](https://github.com/dberardi2020/resume-pipeline) —
`resume-pipeline init`.

## Start here

1. Fill in `Resume/resume.json`. Already have a resume? See the import notes in the tool's
   README — until then, transcribe it once; everything downstream is generated from it.
2. `cd Resume && resume-pipeline lint` — see what a parser and a screener would object to.
3. `resume-pipeline serve` — browse layouts, keep the ones you like, and the next batch is
   sampled near them.
4. `resume-pipeline publish --theme slate` — writes the file you actually send.

## What goes where

| Folder | For |
|---|---|
| `Resume/` | `resume.json` (the only authored file), the published deliverable, and dated snapshots in `Archive/` |
| `Cover Letters/` | Drafts and sent letters |
| `Applications/` | One folder per posting: the job description, the tailored resume, the letter |
| `Reference/` | Notes worth consulting while writing |

`CLAUDE.md` holds the working rules, including the anti-fabrication rule — read it before
letting any agent edit your resume.
"""

LAUNCHER = """#!/bin/sh
# Double-click to open the layout explorer (macOS runs .command files in Terminal).
cd "$(dirname "$0")/Resume" || exit 1
exec resume-pipeline serve
"""


def _write(path: Path, content: str, *, executable: bool = False) -> str:
    if path.exists():
        return f"  skip  {path}  (exists)"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)
    return f"  write {path}"


def init(root: Path, *, skill_only: bool = False) -> list[str]:
    """Create the workspace. Never overwrites an existing file."""
    out: list[str] = []
    if skill_only:
        out.append(_write(root / ".claude" / "skills" / "career" / "SKILL.md", SKILL_MD))
        return out

    out.append(_write(root / "CLAUDE.md", WORKSPACE_CLAUDE_MD))
    out.append(_write(root / "README.md", WORKSPACE_README))
    out.append(_write(root / ".claude" / "skills" / "career" / "SKILL.md", SKILL_MD))
    out.append(_write(root / "Resume" / "resume.json", STARTER_RESUME))
    out.append(_write(root / "Explore Resume.command", LAUNCHER, executable=True))
    for folder in ("Resume/Archive", "Cover Letters", "Applications", "Reference"):
        target = root / folder
        target.mkdir(parents=True, exist_ok=True)
        # Empty directories do not survive git, and these are meaningful structure.
        keep = target / ".gitkeep"
        if not any(target.iterdir()):
            keep.write_text("", encoding="utf-8")
            out.append(f"  write {target}/")
    return out
