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
    match = re.search(r"^const OPTIONS\s*=\s*(\[.*\]);$", html, re.MULTILINE)
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
    assert "Alex Rivera — layouts" in viewer.page(SPECS, resume)


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
