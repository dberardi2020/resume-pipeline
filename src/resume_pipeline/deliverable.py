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


def default_stem(resume) -> str:
    """`<Lastname>_Resume`, falling back to something sane for one-word names."""
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
    stem = stem or default_stem(resume)

    html = compose.render(resume, spec)
    (out_dir / f"{stem}.html").write_text(html, encoding="utf-8")
    (out_dir / f"{stem}.md").write_text(markdown.render(resume), encoding="utf-8")
    pdf.write(html, out_dir / f"{stem}.pdf")
    return stem
