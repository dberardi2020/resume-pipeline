"""Writing the deliverable — the one file set you actually send.

Kept out of the CLI because two surfaces publish: the `publish` command, and the
viewer's "make this my resume". They must write the same names to the same place,
or a workspace ends up with two competing answers to "which file do I send?".

A resume folder should answer that instantly, so publishing overwrites one fixed
set of names rather than accumulating layout-suffixed variants.
"""
from __future__ import annotations

from pathlib import Path

from . import compose, markdown, pdf


SUFFIXES = (".pdf", ".html", ".md")


def existing_stem(out_dir: Path) -> str | None:
    """The stem of a deliverable already in this folder, if there is exactly one.

    A workspace may already name its deliverable something other than this tool
    would choose — and publishing under a second convention does not replace the
    first, it *duplicates* it: two resumes side by side, one of them stale, which
    is precisely the "which file do I send?" confusion publishing exists to end.

    Ambiguous cases (no trio, or more than one) return None and let the caller
    fall back to the default.
    """
    out_dir = Path(out_dir)
    if not out_dir.is_dir():
        return None
    stems = {p.stem for p in out_dir.iterdir() if p.suffix in SUFFIXES}
    complete = [s for s in stems
                if all((out_dir / f"{s}{suffix}").is_file() for suffix in SUFFIXES)]
    return complete[0] if len(complete) == 1 else None


def default_stem(resume, out_dir: Path | None = None) -> str:
    """What to call the deliverable: match what is already there, else derive it."""
    if out_dir is not None and (found := existing_stem(out_dir)):
        return found
    parts = (resume.name or "").split()
    last = parts[-1] if parts else "Resume"
    return f"{last}_Resume".replace(" ", "_")


def write(resume, spec: compose.Spec, out_dir: Path, stem: str | None = None) -> str:
    """Render `spec` and write `<stem>.html`, `.md` and `.pdf`. Returns the stem.

    PDF is written last and is the step that can fail (it needs a browser), so a
    failure leaves the HTML and Markdown in place rather than half a PDF.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = stem or default_stem(resume, out_dir)

    html = compose.render(resume, spec)
    (out_dir / f"{stem}.html").write_text(html, encoding="utf-8")
    (out_dir / f"{stem}.md").write_text(markdown.render(resume), encoding="utf-8")
    pdf.write(html, out_dir / f"{stem}.pdf")
    return stem
