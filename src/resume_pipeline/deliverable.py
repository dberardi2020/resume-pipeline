"""Writing the deliverable — the one file set you actually send.

Kept out of the CLI because two surfaces publish: the `publish` command, and the
viewer's "make this my resume". They must write the same names to the same place,
or a workspace ends up with two competing answers to "which file do I send?".

A resume folder should answer that instantly, so publishing overwrites one fixed
set of names rather than accumulating layout-suffixed variants.

Two publish choices — *which layout* and *which formats* — are remembered in a
small hidden sidecar (`.resume-pipeline.json`) beside the deliverable, so a later
content edit can re-publish the same design without the caller restating it. The
sidecar rather than the deliverable itself, so the choice survives deleting every
generated file; folder-local rather than a global config, so it rides the same
sync and each folder (a tailored application, say) remembers its own.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import compose, markdown, pdf


FORMATS = ("pdf", "html", "md")
SUFFIXES = tuple(f".{fmt}" for fmt in FORMATS)
SIDECAR = ".resume-pipeline.json"


def read_prefs(out_dir: Path) -> dict:
    """The publish preferences recorded in this folder, or `{}` if none/unreadable."""
    try:
        data = json.loads((Path(out_dir) / SIDECAR).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_prefs(out_dir: Path, layout: str, formats) -> None:
    """Record the layout and formats this publish used, for the next bare re-publish."""
    payload = {"layout": layout, "formats": list(formats)}
    (Path(out_dir) / SIDECAR).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def recorded_layout(out_dir: Path) -> str | None:
    """The layout id a previous publish recorded here, if any.

    Lets a bare re-publish after a content edit keep the layout the user already
    chose, instead of silently reverting to the default. None → the caller falls
    back (nothing recorded, or a deliverable from before this was tracked).
    """
    layout = read_prefs(out_dir).get("layout")
    return layout if isinstance(layout, str) and layout else None


def recorded_formats(out_dir: Path) -> list[str] | None:
    """The output formats a previous publish recorded here, if any and still valid."""
    fmts = read_prefs(out_dir).get("formats")
    if isinstance(fmts, list):
        valid = [f for f in FORMATS if f in fmts]
        return valid or None
    return None


def existing_stem(out_dir: Path) -> str | None:
    """The stem of a deliverable already in this folder, if there is exactly one.

    A workspace may already name its deliverable something other than this tool
    would choose — and publishing under a second convention does not replace the
    first, it *duplicates* it: two resumes side by side, one of them stale, which
    is precisely the "which file do I send?" confusion publishing exists to end.

    "Complete" means the recorded formats are all present (all three if nothing is
    recorded), so a PDF-only deliverable still counts. Ambiguous cases — no match,
    or more than one — return None and let the caller fall back to the default.
    """
    out_dir = Path(out_dir)
    if not out_dir.is_dir():
        return None
    required = [f".{fmt}" for fmt in (recorded_formats(out_dir) or FORMATS)]
    stems = {p.stem for p in out_dir.iterdir() if p.suffix in SUFFIXES}
    complete = [s for s in stems
                if all((out_dir / f"{s}{suffix}").is_file() for suffix in required)]
    return complete[0] if len(complete) == 1 else None


def default_stem(resume, out_dir: Path | None = None) -> str:
    """What to call the deliverable: match what is already there, else derive it."""
    if out_dir is not None and (found := existing_stem(out_dir)):
        return found
    parts = (resume.name or "").split()
    last = parts[-1] if parts else "Resume"
    return f"{last}_Resume".replace(" ", "_")


def write(resume, spec: compose.Spec, out_dir: Path,
          stem: str | None = None, formats=None) -> str:
    """Render `spec` and write the chosen `formats` as `<stem>.<ext>`. Returns the stem.

    `formats` is a subset of `FORMATS`; None means all three. The layout and
    formats are recorded to the sidecar *first*, so the choice is remembered even
    if PDF export (which needs a browser and is done last) fails.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    formats = [f for f in FORMATS if f in formats] if formats is not None else list(FORMATS)
    stem = stem or default_stem(resume, out_dir)

    write_prefs(out_dir, spec.name, formats)

    html = compose.render(resume, spec)
    if "html" in formats:
        (out_dir / f"{stem}.html").write_text(html, encoding="utf-8")
    if "md" in formats:
        (out_dir / f"{stem}.md").write_text(markdown.render(resume), encoding="utf-8")
    if "pdf" in formats:
        pdf.write(html, out_dir / f"{stem}.pdf")
    return stem
