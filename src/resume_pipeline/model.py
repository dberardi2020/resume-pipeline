"""Load and validate a JSON Resume document.

The data layer. Everything downstream — themes, Markdown, PDF, lint — reads a
`Resume` and never touches raw JSON. Deliberately a *thin* wrapper: the schema is
JSON Resume (https://jsonresume.org/schema), not a bespoke shape, so the same
document stays portable to any other tool that speaks the standard.

Validation is structural, not stylistic. It answers "can this be rendered?" —
missing required fields, wrong types, malformed dates. Whether the *content* is
any good is `lint.py`'s job, and the two are kept apart on purpose: an agent
rewriting bullets should trip lint warnings, never a load error.

Stdlib only.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# JSON Resume date fields are ISO 8601, and may be truncated to year or
# year-month. `work[].endDate` is absent/empty for a current role.
_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


class ResumeError(ValueError):
    """A resume document that cannot be rendered."""


def _human_date(value: str | None, *, present: str = "Present") -> str:
    """`2024-12` -> `December 2024`. Empty/absent -> `present`."""
    if not value:
        return present
    parts = value.split("-")
    year = parts[0]
    if len(parts) == 1:
        return year
    return f"{_MONTHS[int(parts[1]) - 1]} {year}"


def date_range(start: str | None, end: str | None) -> str:
    """The `December 2024 - Present` string themes render for a role."""
    return f"{_human_date(start)} - {_human_date(end)}"


@dataclass
class Resume:
    """A validated JSON Resume document."""

    data: dict
    source: Path | None = None
    # Non-fatal structural notes surfaced by the CLI (e.g. unknown sections).
    notes: list[str] = field(default_factory=list)

    # -- section accessors ------------------------------------------------
    # Themes read through these so a missing optional section renders as empty
    # rather than raising. JSON Resume marks every section but `basics` optional.

    @property
    def basics(self) -> dict:
        return self.data.get("basics", {})

    @property
    def name(self) -> str:
        return self.basics.get("name", "")

    @property
    def label(self) -> str:
        """The positioning line, e.g. `Backend Software Engineer`."""
        return self.basics.get("label", "")

    @property
    def summary(self) -> str:
        return self.basics.get("summary", "")

    @property
    def location(self) -> str:
        loc = self.basics.get("location", {})
        parts = [loc.get("city"), loc.get("region")]
        return ", ".join(p for p in parts if p)

    @property
    def profiles(self) -> list[dict]:
        return self.basics.get("profiles", [])

    def section(self, name: str) -> list[dict]:
        value = self.data.get(name, [])
        return value if isinstance(value, list) else []

    @property
    def work(self) -> list[dict]:
        return self.section("work")

    @property
    def education(self) -> list[dict]:
        return self.section("education")

    @property
    def projects(self) -> list[dict]:
        return self.section("projects")

    @property
    def skills(self) -> list[dict]:
        return self.section("skills")


# JSON Resume's top-level sections. Anything else is passed through untouched
# but reported, so a typo like `experience` (correct name: `work`) surfaces
# instead of silently rendering an empty resume.
KNOWN_SECTIONS = {
    "basics", "work", "volunteer", "education", "awards", "certificates",
    "publications", "skills", "languages", "interests", "references",
    "projects", "meta",
    # Editors use this for schema autocompletion; it is not a content section.
    "$schema",
}

# Sections whose entries carry dates we validate and render.
_DATED_SECTIONS = ("work", "volunteer", "education", "projects", "awards",
                   "certificates", "publications")


def _validate(data: dict) -> list[str]:
    """Return non-fatal notes; raise ResumeError on anything unrenderable."""
    if not isinstance(data, dict):
        raise ResumeError("Top level must be a JSON object.")

    basics = data.get("basics")
    if not isinstance(basics, dict) or not basics.get("name"):
        raise ResumeError("`basics.name` is required.")

    notes: list[str] = []
    for unknown in sorted(set(data) - KNOWN_SECTIONS):
        notes.append(
            f"Unknown top-level section {unknown!r} — not part of JSON Resume, "
            f"so no theme will render it."
        )

    for name in _DATED_SECTIONS:
        entries = data.get(name, [])
        if not isinstance(entries, list):
            raise ResumeError(f"`{name}` must be an array.")
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ResumeError(f"`{name}[{i}]` must be an object.")
            for key in ("startDate", "endDate"):
                value = entry.get(key)
                if value and not _DATE_RE.match(str(value)):
                    raise ResumeError(
                        f"`{name}[{i}].{key}` is {value!r} — expected ISO 8601 "
                        f"(YYYY, YYYY-MM, or YYYY-MM-DD)."
                    )
            # A role that ends before it starts is almost always a bad agent edit.
            start, end = entry.get("startDate"), entry.get("endDate")
            if start and end and str(end) < str(start):
                raise ResumeError(
                    f"`{name}[{i}]` ends ({end}) before it starts ({start})."
                )
            highlights = entry.get("highlights")
            if highlights is not None and not isinstance(highlights, list):
                raise ResumeError(f"`{name}[{i}].highlights` must be an array.")

    return notes


def load(path: str | Path) -> Resume:
    """Read and validate a JSON Resume file."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ResumeError(f"No such resume: {path}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResumeError(f"{path} is not valid JSON: {exc}") from None
    return Resume(data=data, source=path, notes=_validate(data))
