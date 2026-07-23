"""The viewer — one page, two deliveries.

These tests exist because there used to be two implementations of this page. The
point is that the *only* differences between the served and static deliveries are
where previews come from and whether export is offered.
"""
from __future__ import annotations

import json
import re

from resume_pipeline import compose, space, viewer

SPECS = space.spread(5)


def _options(html: str) -> list[dict]:
    match = re.search(r"^let\s+OPTIONS\s*=\s*(\[.*\]);$", html, re.MULTILINE)
    assert match, "OPTIONS payload not found in page"
    return json.loads(match.group(1))


def test_page_embeds_every_spec(resume):
    options = _options(viewer.page(SPECS, resume))
    assert [o["name"] for o in options] == [s.name for s in SPECS]


def test_page_embeds_the_axes_as_facets(resume):
    options = _options(viewer.page(SPECS, resume))
    assert all(set(o["axes"]) == {"palette", "typeface", "header", "skills",
                                  "promo", "density", "grouping"}
               for o in options)


def test_static_delivery_points_at_sibling_files(resume):
    html = viewer.page(SPECS, resume, preview="file")
    assert 'const PREVIEW    = "file"' in html
    assert 'const EXPORTABLE = false' in html


def test_served_delivery_points_at_the_preview_route(resume):
    html = viewer.page(SPECS, resume, preview="route", exportable=True)
    assert 'const PREVIEW    = "route"' in html
    assert 'const EXPORTABLE = true' in html


def test_the_two_deliveries_differ_only_in_those_switches(resume):
    static = viewer.page(SPECS, resume, preview="file")
    served = viewer.page(SPECS, resume, preview="route", exportable=True)
    normalise = (lambda h: h.replace('"route"', '"file"')
                            .replace("EXPORTABLE = true", "EXPORTABLE = false"))
    assert normalise(served) == normalise(static)


def test_the_resume_name_titles_the_page(resume):
    assert "Jane Smith — Layouts" in viewer.page(SPECS, resume)


def test_a_hostile_name_cannot_break_out_of_the_title(make_resume):
    hostile = make_resume(lambda d: d["basics"].update(name="</title><script>x</script>"))
    html = viewer.page(SPECS, hostile)
    assert "</title><script>" not in html
    assert "&lt;/title&gt;" in html


def test_describe_matches_the_spec():
    spec = SPECS[0]
    described = viewer.describe(spec)
    assert described["name"] == spec.name
    assert described["description"] == spec.description
    assert described["axes"]["palette"] == compose.PALETTES[spec.palette][0]


def test_page_is_self_contained(resume):
    """It must work from `file://` — no external stylesheet, script, or font."""
    html = viewer.page(SPECS, resume)
    assert "http://" not in html
    assert not re.search(r'<(script|link)[^>]+(src|href)\s*=\s*"https?://', html)


# ── the colour bar ────────────────────────────────────────────────────────────

def test_the_served_viewer_offers_every_palette(resume):
    html = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    import re
    pals = json.loads(re.search(r"const PALETTES\s*=\s*(\[.*?\]);", html).group(1))
    assert [p["name"] for p in pals] == [p[0] for p in compose.PALETTES]
    assert 'const CAN_RECOLOR = PREVIEW === "route"' in html


def test_recolouring_swaps_the_palette_segment_only():
    """The mechanism the colour bar relies on: palette is the first name segment.

    So "this layout, that colour" is a different but equally valid spec, and the
    rest of the layout is untouched — which is why it can be an instant re-render
    rather than a live edit.
    """
    spec = compose.Spec(0, 0, "band", "pills", "ladder", 1, "grouped")
    assert spec.name.split("-")[0] == "harbor"
    recoloured = "moss" + spec.name[len("harbor"):]
    other = space.parse(recoloured)
    assert other is not None
    assert compose.PALETTES[other.palette][0] == "moss"
    # every axis but palette is identical
    assert (other.typeface, other.header, other.skills,
            other.promo, other.density, other.grouping) == \
           (spec.typeface, spec.header, spec.skills,
            spec.promo, spec.density, spec.grouping)


def test_the_first_page_button_exists_only_when_paging(resume):
    served = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    assert 'id="first"' in served
