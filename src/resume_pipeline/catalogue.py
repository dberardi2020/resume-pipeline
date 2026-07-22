"""A static, browsable catalogue of layouts.

`serve` is the same viewer with a process behind it. A catalogue needs no process:
it is a folder you open in a browser, commit, link, or hand to someone else — and a
`file://` path outlives a localhost URL.

The output is self-contained and works from `file://` — no server, no build step.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import compose, space, viewer


def build(resume, count: int, out_dir: Path) -> tuple[Path, list]:
    """Render `count` layouts plus an index. Returns (index path, specs)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = space.spread(count)

    for spec in specs:
        (out_dir / f"{spec.name}.html").write_text(
            compose.render(resume, spec), encoding="utf-8")

    index = out_dir / "index.html"
    index.write_text(viewer.page(specs, resume, preview="file"), encoding="utf-8")

    # The page is for a human; this is for the agent standing next to them. It
    # makes "use number 7" resolvable without parsing HTML or guessing.
    (out_dir / "options.json").write_text(json.dumps({
        "options": [
            dict(number=n, preview=f"{s.name}.html", **viewer.describe(s))
            for n, s in enumerate(specs, 1)
        ],
    }, indent=2) + "\n", encoding="utf-8")
    return index, specs
