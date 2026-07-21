"""Themes turn a `Resume` into HTML. The theme is the *only* place layout lives.

A theme declares how it lays the page out, and `lint.py` reads those declarations
to judge it. That is the point of the split: an agent rewriting your bullets can
never make the document unparseable, because it has no access to this layer.

Adding a layout means adding a module here and registering it below — no resume
content is duplicated, because content arrives as a `Resume`.

The declared attributes are a *contract*, not decoration. If you build a
two-column theme, say `columns = 2` and let the linter flag it honestly rather
than shipping a theme that quietly fails ATS parsing.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Theme:
    name: str
    description: str
    render: Callable[..., str]
    # -- declarations the linter reads --
    columns: int = 1
    min_font_pt: float = 10.0
    remote_assets: bool = False
    # Is this theme meant for machine parsing, or for a human reader?
    ats_safe: bool = True


def esc(value) -> str:
    """Escape for HTML text. Every theme must route content through this."""
    return html.escape(str(value or ""), quote=True)


def registry() -> dict[str, Theme]:
    # Imported lazily so a broken theme cannot stop the whole CLI from loading.
    from . import ats, designed, editorial, slate
    return {t.name: t for t in (slate.THEME, ats.THEME, editorial.THEME,
                                designed.THEME)}


def get(name: str) -> Theme:
    """Resolve a theme by name.

    Hand-built themes are looked up first, then generated layouts by their spec
    name. Without this, a layout you found in the catalogue could be previewed but
    never published — the interesting half of the space would be unreachable from
    every other command.
    """
    themes = registry()
    if name in themes:
        return themes[name]

    from .. import compose, space
    if spec := space.parse(name):
        return compose.as_theme(spec)

    available = ", ".join(sorted(themes))
    raise KeyError(
        f"Unknown layout {name!r}. Built-in themes: {available}. "
        f"Generated layouts look like 'moss-111-charter-airy' - "
        f"run `resume-pipeline catalogue` to browse them."
    )
